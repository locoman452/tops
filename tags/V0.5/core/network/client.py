"""
Base class for simple telescope operations network clients

Defines a base class for a write-only network client that assumes a
simple protocol that is sufficient for simple services such as logging
and archiving. The implementation is intended for Header and Message
classes that correspond to Google protocol buffers, but any classes that
provide a SerializeToString() method can be used. There is a
corresponding server class in this package.
"""

## @package tops.core.network.client
# Base class for simple telescope operations network clients
#
# @author David Kirkby, dkirkby@uci.edu
# @date Created 26-Aug-2008
#
# This project is hosted at sdss3.org and tops.googlecode.com

import socket
import struct

class ClientException(Exception):
	pass

class Client(object):
	"""
	Manages the client side of a write-only socket protocol.
	
	Uses a UNIX socket when a path is provided and can be connected to.
	Otherwise, falls back to a TCP streams socket using the specified
	host and port. Data is sent in binary packets prefixed with an
	unsigned 16-bit length. The first packet is a Header object and all
	subsequent packets are Message objects. The Header and Message types
	must be defined by the superclass.
	"""

	lengthPrefix = struct.Struct('!H') # 16-bit unsigned int using network byte order

	def __init__(self,unix_path,tcp_host,tcp_port):
		self.unix_addr = unix_path
		self.tcp_addr = (tcp_host,tcp_port)
		self.hdr = None
		self.socket = self.connect()
	
	def connect(self):
		"""
		Attempts to return a connected socket.
		
		A UNIX address is tried first if one was provided in the
		constructor, otherwise a TCP address is tried.
		"""
		socket_type = socket.SOCK_STREAM
		if self.unix_addr is not None:
			try:
				s = socket.socket(socket.AF_UNIX, socket_type)
				s.connect(self.unix_addr)
				return s
			except socket.error:
				pass
		s = socket.socket(socket.AF_INET, socket_type)
		s.connect(self.tcp_addr)
		return s
		
	def send(self,data):
		"""
		Sends the specified data with an unsigned 16-bit length prefix.
		"""
		if self.socket is None:
			raise ClientException("must connect socket before sending")
		# add a length prefix
		packet = self.lengthPrefix.pack(len(data)) + data
		# try to send the packet
		try:
			if hasattr(self.socket,"sendall"):
				self.socket.sendall(packet)
			else:
				offset = 0
				remaining = len(packet)
				while remaining > 0:
					sent = self.socket.send(packet[offset:])
					offset += sent
					remaining -= sent
		except socket.error:
			self.close()
			raise
			
	def close(self):
		if self.socket:
			self.socket.close()
			self.socket = None			
		
	def sendHeader(self,hdr):
		"""
		Sends our header to the server.
		"""
		self.hdr = hdr
		self.send(hdr.SerializeToString())
	
	def sendMessage(self,msg):
		self.send(msg.SerializeToString())
