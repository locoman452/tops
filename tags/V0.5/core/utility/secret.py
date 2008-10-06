"""
Provides an interface to secret data


"""

## @package tops.core.utility.secret
# Provides an interface to secret data
#
# @author David Kirkby, dkirkby@uci.edu
# @date Created 23-Sep-2008
#
# This project is hosted at sdss3.org and tops.googlecode.com

import getpass
from Crypto.Hash import MD5 as hasher
from Crypto.Cipher import AES as cipher

class SecretException(Exception):
	pass

class SecretEngine(object):
	
	def __init__(self,key=None,passphrase=None,prompt='Enter the pass phrase: '):
		"""
		Initializes an encryption engine.
		
		Uses the 32-byte binary key provided or else prompts the user
		for a pass phrase and derives the key from that.
		"""
		if not key:
			if not passphrase:
				passphrase = getpass.getpass(prompt)
			key = hasher.new(passphrase).digest()
		if len(key) not in [16,24,32]:
			raise SecretException('wrong key length: %d' % len(key))
		self.key = key
		self.engine = cipher.new(key,cipher.MODE_ECB)

	def encrypt(self,plaintext):
		"""
		Returns the encrypted equivalent of plaintext.
		"""
		npad = cipher.block_size - (len(plaintext) % cipher.block_size)
		assert(npad > 0)
		data = plaintext + '\x00'*(npad-1) + chr(npad)
		assert(len(data) % cipher.block_size == 0)
		return self.engine.encrypt(data)
		
	def decrypt(self,encrypted):
		"""
		Returns the plaintext equivalent of encrypted.
		"""
		data = self.engine.decrypt(encrypted)
		npad = ord(data[-1])
		if npad <= 0 or npad > cipher.block_size or data[-npad:-1] != '\x00'*(npad-1):
			raise SecretException('badly formed encrypted data')
		return data[0:-npad]
		

def bin2hex(data):
	"""
	Returns an ASCII hexadecimal representation of binary data.
	"""
	bytes = ['%02x' % ord(c) for c in data]
	return ''.join(bytes)

def hex2bin(data):
	"""
	Returns the inverse of bin2hex().
	"""
	if not len(data) % 2 == 0:
		raise SecretException('hex digest must have even length')
	bytes = [ ]
	for index in xrange(len(data)/2):
		bytes.append(chr(int(data[2*index:2*(index+1)],16)))
	return ''.join(bytes)

import unittest

class SecretTests(unittest.TestCase):
	
	passphrase = 'The quick brown fox jumps over the lazy dog'
	key = hasher.new(passphrase).digest()
	short_message = 'hello, world'
	long_message = ''.join([chr(i%256) for i in range(1000)])
	
	def test00(self):
		"""Engine creation with key"""
		engine = SecretEngine(key=self.key)
	
	def test01(self):
		"""Engine creation with passphrase"""
		engine = SecretEngine(passphrase=self.passphrase)
		self.assertEqual(engine.key,self.key)
		
	def test02(self):
		"""Engine creation with bad key length"""
		self.assertRaises(SecretException,lambda: SecretEngine(key='123'))

	def test03(self):
		"""Encryption and decryption round trip with short message"""
		engine = SecretEngine(key=self.key)
		encrypted = engine.encrypt(self.short_message)
		self.assertEqual(engine.decrypt(encrypted),self.short_message)

	def test04(self):
		"""Encryption and decryption round trip with long message"""
		engine = SecretEngine(key=self.key)
		encrypted = engine.encrypt(self.long_message)
		self.assertEqual(engine.decrypt(encrypted),self.long_message)

	def test05(self):
		"""Decryption of corrupted zero pad in short message"""
		engine = SecretEngine(key=self.key)
		encrypted = engine.encrypt(self.short_message)
		bytes = list(encrypted)
		bytes[-2] = '\x01'
		self.assertRaises(SecretException,lambda: engine.decrypt(''.join(bytes)))

	def test06(self):
		"""Decryption of corrupted pad length in short message"""
		engine = SecretEngine(key=self.key)
		encrypted = engine.encrypt(self.short_message)
		bytes = list(encrypted)
		bytes[-1] = chr(ord(bytes[-1])+1)
		self.assertRaises(SecretException,lambda: engine.decrypt(''.join(bytes)))
		
	def test07(self):
		"""Decryption of corrupted zero pad in long message"""
		engine = SecretEngine(key=self.key)
		encrypted = engine.encrypt(self.long_message)
		bytes = list(encrypted)
		bytes[-2] = '\x01'
		self.assertRaises(SecretException,lambda: engine.decrypt(''.join(bytes)))

	def test08(self):
		"""Decryption of corrupted pad length in long message"""
		engine = SecretEngine(key=self.key)
		encrypted = engine.encrypt(self.long_message)
		bytes = list(encrypted)
		bytes[-1] = chr(ord(bytes[-1])+1)
		self.assertRaises(SecretException,lambda: engine.decrypt(''.join(bytes)))
		
	def test09(self):
		"""bin2hex - hex2bin roundtrip for short message"""
		hex = bin2hex(self.short_message)
		self.assertEqual(hex2bin(hex),self.short_message)
	
	def test10(self):
		"""bin2hex - hex2bin roundtrip for long message"""
		hex = bin2hex(self.long_message)
		self.assertEqual(hex2bin(hex),self.long_message)


if __name__ == '__main__':
	
	engine = SecretEngine()
	while True:
		plaintext = raw_input('Enter data to encrypt or hit RETURN to quit: ')
		if len(plaintext) == 0:
			break
		print bin2hex(engine.encrypt(plaintext))