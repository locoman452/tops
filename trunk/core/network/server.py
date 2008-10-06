"""
Base class for simple telescope operations network servers

Defines a base class for a read-only network server that assumes a
simple protocol that is sufficient for simple services such as logging
and archiving. The implementation is intended for Header and Message
classes that correspond to Google protocol buffers, but any classes that
provide a ParseFromString() method can be used. There is a
corresponding client class in this package.
"""

## @package tops.core.network.server
# Base class for simple telescope operations network servers
#
# @author David Kirkby, dkirkby@uci.edu
# @date Created 21-Aug-2008
#
# This project is hosted at sdss3.org and tops.googlecode.com

import twisted.protocols.basic
import twisted.internet.error

class Server(twisted.protocols.basic.Int16StringReceiver):

	def __init__(self):
		self.hdr = self.Header()
		self.msgcount = 0
		self.bytecount = 0

	def connectionMade(self):
		print 'Got a new connection from',self.transport.getPeer()

	def connectionLost(self,reason):
		if reason.check(twisted.internet.error.ConnectionDone):
			print 'Connection closed'
		else:
			print 'Connection lost:',reason

	def stringReceived(self, raw):
		if self.msgcount == 0:
			self.hdr.ParseFromString(raw)
			self.handleHeader(self.hdr)
		else:
			msg = self.Message()
			msg.ParseFromString(raw)
			self.handleMessage(msg)
		self.msgcount += 1
		self.bytecount += len(raw)
		
	def handleHeader(self,hdr):
		pass

	def handleMessage(self,msg):
		raise NotImplementedError