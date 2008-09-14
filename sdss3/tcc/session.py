"""
Implements a read-write proxy for the TCC command interpreter

Defines the custom data types associated with the TCC's command
interpreter, and implements a proxy that can issue commands via a telnet
session.

Refer to the proxy declaration below for details of its operating states
and archive records. Running this module will start the proxy and so
requires that the logging and archiving servers are already up.
"""

## @package tops.sdss3.tcc.session
# Implements a read-write proxy for the TCC command interpreter
#
# @author David Kirkby, dkirkby@uci.edu
# @date Created 13-Sep-2008
#
# This project is hosted at http://tops.googlecode.com/

#from tops.core.network.proxy import *

from twisted.internet import protocol, reactor
from twisted.conch import telnet

from getpass import getpass

class TelnetSession(telnet.TelnetProtocol):
	
	login_prompt = 'Username: '
	password_prompt = 'Password: '
	command_prompt = '$ '

	username = 'tcc'
	password = ''

	# warning: enabling debug mode will display the password on the console
	debug = True
	
	state = 'CONNECTING'
	
	def send(self,data):
		"""Writes data through our connection transport"""
		if self.debug:
			print 'TelnetSession: sending >>%s<<' % data
		self.transport.write(data)

	def dataReceived(self,data):
		"""Drives a state machine based on the input received"""
		if self.debug:
			print ("TelnetSession: got %r in state '%s'" %
				(data.encode('ascii','backslashreplace'),self.state))
		oldState = self.state
		getattr(self, "session_" + self.state)(data)
		if self.debug and self.state != oldState:
			print 'TelnetSession: entering new state "%s"' % self.state
	
	def session_CONNECTING(self,data):
		if data.endswith(self.login_prompt):
			self.state = 'AUTHENTICATING'
			self.send(self.username+'\n')
			
	def session_AUTHENTICATING(self,data):
		if data.endswith(self.password_prompt):
			self.send(self.password + '\n')
		elif data.endswith(self.login_prompt):
			self.state = 'LOGIN_FAILED'
		elif data.endswith(self.command_prompt):
			self.state = 'COMMAND_LINE_READY'

	def session_LOGIN_FAILED(self,data):
		pass
			
	def session_COMMAND_LINE_READY(self,data):
		if self.debug and len(self.command_response):
			print 'TelnetSession: response from last command'
			for data in self.command_response:
				print repr(data.encode('ascii','backslashreplace'))
		self.command_response = [ ]
		pass
		
	def session_COMMAND_LINE_BUSY(self,data):
		if data.endswith(self.command_prompt):
			self.state = 'COMMAND_LINE_READY'
		else:
			self.command_response.append(data)
		
	def do(self,command):
		if self.state == 'COMMAND_LINE_READY':
			self.state = 'COMMAND_LINE_BUSY'
			self.send(command)

class TelnetConnection(telnet.TelnetTransport):

	def __init__(self):
		# create a session instance to handle the application-level protocol
		self.protocol = TelnetSession()
		telnet.TelnetTransport.__init__(self)
		
	def connectionMade(self):
		# propagate our transport instance to the session protocol
		self.protocol.makeConnection(self)


if __name__ == "__main__":
	
	TelnetSession.password = getpass('Enter TCC password: ')

	connectionFactory = protocol.ClientFactory()
	connectionFactory.protocol = TelnetConnection
	reactor.connectTCP('tcc25m.apo.nmsu.edu',23,connectionFactory)
	
	reactor.run()
