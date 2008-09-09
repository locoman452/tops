"""
Supports data dictionary declarations and provides numeric data
services.

Defines a metaclass for numeric data types that can be efficiently
serialized for network transport and database storage.
"""

## @package tops.core.utility.data
# Lightweight object graphs for simple configuration declarations
#
# @author David Kirkby, dkirkby@uci.edu
# @date Created 21-Aug-2008
#
# This project is hosted at http://tops.googlecode.com/

class ValueType(type):
	"""
	A metaclass for types that represent an enumerated or numeric value.
	
	ValueTypes can serialize themselves for efficient network transport
	(via pack and unpack methods) or database storage (via ?).
	"""
	registry = {}
	def __init__(cls,name,bases,dct):
		"""
		Initializes a new class that is an instance of a ValueType.
		"""
		# create the type
		super(ValueType,cls).__init__(name,bases,dct)
		ValueType.registry[name] = cls

class double(float):
	"""
	Represents a double-precision real value.
	"""
	__metaclass__ = ValueType

	def pack(self,buffer):
		buffer.double = self

	@classmethod
	def unpack(cls,buffer):
		return cls(buffer.double)

class signed(int):
	"""
	Represents a signed integer.
	"""
	__metaclass__ = ValueType

	def pack(self,buffer):
		buffer.signed = self

	@classmethod
	def unpack(cls,buffer):
		return cls(buffer.signed)

class unsigned(int):
	"""
	Represents an unsigned integer.
	"""
	__metaclass__ = ValueType
	
	def __new__(cls,value):
		if int(value) < 0:
			raise ValueError('invalid literal for unsigned()')
		return int.__new__(cls,value)
	
	def pack(self,buffer):
		buffer.unsigned = self

	@classmethod
	def unpack(cls,buffer):
		return cls(buffer.unsigned)

class enumerated(str):
	"""
	Represents an enumerated value.
	
	A subclass will normally only define a single class attribute: a
	tuple of the allowed string labels for this enumeration.
	"""
	__metaclass__ = ValueType

	labels = ( )
	_values = None
	
	def __new__(cls,value):
		if not value in cls.labels:
			raise ValueError('invalid literal for %s: "%s" (should be one of %s)' % 
				(cls.__name__,value,';'.join(cls.labels)))
		return str.__new__(cls,value)
	
	def pack(self,buffer):
		# self._values looks for, in order, an instance attribute, a
		# class attribute, or a superclass attribute. A superclass attribute is
		# already defined as None so this this test will be true unless
		# we have already defined a class or instance attribute that hides it.
		if self._values is None:
			# Build a label -> value dictionary and store it as a class attribute
			# that will be shared by all other instances of this enumerated subclass.
			self.__class__._values = dict(zip(self.labels,range(len(self.labels))))
		# store the index of our current label value
		buffer.unsigned = self._values[self]
	
	@classmethod	
	def unpack(cls,buffer):
		# load our label by indexing into our labels sequence
		return cls(cls.labels[buffer.unsigned])


import unittest

class DataTests(unittest.TestCase):

	class buffer(object):
		double = float(0)
		signed = int(0)
		unsigned = int(0)

	def test00(self):
		"""Numeric type constructors"""
		self.assertEqual(double(1.23),1.23)
		self.assertEqual(unsigned(123),123)
		self.assertEqual(signed(-123),-123)

	def test01(self):
		"""Enumeration constructor"""
		class truefalse(enumerated):
			labels = ('true','false')
		self.assertEqual(truefalse('true'),'true')
		self.assertEqual(truefalse('false'),'false')

	def test02(self):
		"""Double packing and unpacking"""
		buf = self.buffer()
		x1 = double(1.23)
		x1.pack(buf)
		x2 = double.unpack(buf)
		self.assertEqual(x1,x2)

	def test03(self):
		"""Unsigned packing and unpacking"""
		buf = self.buffer()
		u1 = unsigned(123)
		u1.pack(buf)
		u2 = unsigned.unpack(buf)
		self.assertEqual(u1,u2)

	def test04(self):
		"""Signed packing and unpacking"""
		buf = self.buffer()
		s1 = signed(-123)
		s1.pack(buf)
		s2 = signed.unpack(buf)
		self.assertEqual(s1,s2)
		
	def test05(self):
		"""Enumerated packing and unpacking"""
		class truefalse(enumerated):
			labels = ('true','false')
		buf = self.buffer()
		t1 = truefalse('true')
		t1.pack(buf)
		t2 = truefalse.unpack(buf)
		self.assertEqual(t1,t2)
		f1 = truefalse('false')
		f1.pack(buf)
		f2 = truefalse.unpack(buf)
		self.assertEqual(f1,f2)
		
	def test06(self):
		"""Range errors triggered by constructors"""
		self.assertRaises(ValueError,lambda: double('not a double'))
		self.assertRaises(ValueError,lambda: unsigned('not an unsigned'))
		self.assertRaises(ValueError,lambda: signed('not a signed'))
		self.assertRaises(ValueError,lambda: unsigned(-123))
		class truefalse(enumerated):
			labels = ('true','false')
		self.assertRaises(ValueError,lambda: truefalse(123))
		self.assertRaises(ValueError,lambda: truefalse('neither'))

		
if __name__ == '__main__':
	unittest.main()
