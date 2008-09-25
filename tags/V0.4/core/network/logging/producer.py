"""
Implements the producer client side of distributed logging

This module serves as a wrapper for the builtin python logging library
and should normally be invoked with:

  import tops.core.network.logging.producer as logging
  ...
  logging.initialize("my.source.name.prefix")

Without the call to initialize(), logging defaults to the built-in
implementation. By calling initialize(), all messages will be logged
via a TCP handler to the distributed logging server. Messages will be
identified by a source name that consists of the prefix name provided
to initialize() followed by the name associated with any custom logger
created by the user.

The logging module uses the tops.core.utility.config module to obtain
its network connection parameters so config.initialize() must be called
somewhere in the main program before logging.initialize().

The source name prefix (and any user-defined logger name) must be a
valid ResourceName. See record.py in this package for details.

initialize() also sets the message level filter to DEBUG so that all
messages are sent to the server by default. Use, for example,
logging.setLevel(logging.ERROR) to change this.
"""

## @package tops.core.network.logging.producer
# Implements the producer client side of distributed logging
#
# @author David Kirkby, dkirkby@uci.edu
# @date Created 7-Aug-2008
#
# This project is hosted at http://tops.googlecode.com/

from logging import *
from logging.handlers import SocketHandler

from struct import Struct
from traceback import format_exception

import socket

from logging_pb2 import Message,Header
from tops.core.network.naming import ResourceName

class ClientHandler(SocketHandler):

	_LengthPacker = Struct('!H') # 16-bit unsigned int using network byte order

	def __init__(self,source,path,host,port):
		self.path = path
		SocketHandler.__init__(self,host,port)
		header = Header()
		header.name = str(source)
		self.hdr = self._pack16(header.SerializeToString())

	def _pack16(self,data):
		"""
		Returns data with a 16-bit unsigned integer length prepended, in network byte order.
		"""
		return self._LengthPacker.pack(len(data)) + data

	def makePickle(self,record):
		"""
		Serializes the record in binary format with a 16-bit length
		prefix, and returns it ready for transmission across the socket.
		Uses a Google protocol buffer instead of the default pickle
		implementation.
		"""
		msg = Message()
		msg.levelno = record.levelno
		interpolated = record.msg % record.args
		msg.body = interpolated.encode('utf-8','replace')
		if not record.name == 'root':
			msg.source = record.name
		if 'SaveContext' in record.__dict__ and record.SaveContext:
			msg.context.filename = record.filename
			msg.context.lineno = record.lineno
			msg.context.funcname = record.funcName
		if record.exc_info is not None:
			msg.exception = ''.join(format_exception(*record.exc_info))
		return self._pack16(msg.SerializeToString())

	def makeSocket(self):
		"""
		Returns a connected socket.
		
		Tries a unix socket first if a path is provided, otherwise (or
		if the unix socket fails) uses a TCP socket.
		"""
		if self.path is not None:
			try:
				s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
				s.connect(self.path)
				return s
			except socket.error:
				pass
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((self.host, self.port))
		return s

	def createSocket(self):
		SocketHandler.createSocket(self)
		if self.sock:
			self.send(self.hdr)


import tops.core.utility.config as config

def initialize(name):
	"""
	Initializes a logging producer registered under the specified name.
	
	Overrides the built-in logging.getLogger(name) to check that name is
	a valid source name. Attempts to connect this producer to the server
	and raises an exception if this fails. Sets the default logging
	level to DEBUG so that the server has a chance to see all messages.
	"""
	_getLogger = getLogger

	def clientGetLogger(name=None):
		"""
		Overrides the built-in implementation to check for a valid source name.
		"""
		if name:
			source = ResourceName(name)
		return _getLogger(name)
	
	globals()["getLogger"] = clientGetLogger

	source = ResourceName(name)	
	clientHandler = ClientHandler(source,
		config.get('logger','unix_addr'),
		config.get('logger','tcp_host'),
		config.get('logger','tcp_port')
	)
	root.handlers.append(clientHandler)
	root.setLevel(DEBUG)
