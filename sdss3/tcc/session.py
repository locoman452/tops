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

from twisted.internet import protocol,defer,reactor
from twisted.conch import telnet

from getpass import getpass


def answer(response,command):
	print 'the answer to "%s" is "%s"' % (command,response)

def delayed1():
	print "Running delayed1..."
	TelnetSession.do('FTPSession','help set').addCallback(answer,'help set')

def delayed2():
	print "Running delayed2..."
	TelnetSession.do('LocalhostSession','pwd').addCallback(answer,'pwd')

	
class TelnetSession(telnet.TelnetProtocol):

	debug = True
	registry = { }
	
	@staticmethod
	def do(session_name,command):
		try:
			session = TelnetSession.registry[session_name]
		except AttributeError:
			return defer.fail('')
		return session._do(command)

	def __init__(self):
		myname = self.__class__.__name__
		if self.debug:
			print 'TelnetSession: registering "%s"' % myname
		self.registry[myname] = self
		if not self.password:
			self.password = getpass('Enter password for "%s": ' % self.username)
		self.state = 'CONNECTING'
		# telnet.TelnetProtocol has no __init__ method to call

	def send(self,data,secret=False):
		"""Writes data through our connection transport"""
		if self.debug:
			if secret:
				print 'TelnetSession: sending something secret'
			else:
				print 'TelnetSession: sending %r' % data.encode('ascii','backslashreplace')
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
			self.send(self.password + '\n',secret=True)
		elif data.endswith(self.login_prompt):
			self.state = 'LOGIN_FAILED'
		elif data.endswith(self.command_prompt):
			self.session_started()

	def session_started(self):
		self.state = 'COMMAND_LINE_READY'

	def session_LOGIN_FAILED(self,data):
		pass
			
	def session_COMMAND_LINE_READY(self,data):
		pass
		
	def session_COMMAND_LINE_BUSY(self,data):
		self.command_response.append(data)
		if data.endswith(self.command_prompt):
			self.state = 'COMMAND_LINE_READY'
			if self.debug:
				print 'TelnetSession: response from last command:'
				for data in self.command_response:
					print repr(data.encode('ascii','backslashreplace'))
			self.command_defer.callback(self.command_response)
		
	def _do(self,command):
		self.command_response = [ ]
		if self.state == 'COMMAND_LINE_READY':
			self.state = 'COMMAND_LINE_BUSY'
			self.send(command + '\n')
			self.command_defer = defer.Deferred()
			return self.command_defer
		else:
			return defer.fail('')

class LocalhostSession(TelnetSession):

	login_prompt = 'login: '
	password_prompt = 'Password:'
	command_prompt = '~ % '
	username = 'david'	
	password = ''

class FTPSession(LocalhostSession):

	ftp_command = 'ftp'
	ftp_prompt = 'ftp> '

	def session_started(self):
		self.state = 'STARTING_FTP'
		self.send(self.ftp_command + '\n')
		
	def session_STARTING_FTP(self,data):
		if data.endswith(self.ftp_prompt):
			self.command_prompt = self.ftp_prompt
			self.state = 'COMMAND_LINE_READY'


class VMSSession(TelnetSession):

	login_prompt = 'Username: '
	password_prompt = 'Password: '
	command_prompt = '$ '
	username = 'tcc'
	password = ''


class TelnetConnection(telnet.TelnetTransport):

	def __init__(self,protocol=LocalhostSession):
		# create a session instance to handle the application-level protocol
		self.protocol = protocol()
		telnet.TelnetTransport.__init__(self)
		
	def connectionMade(self):
		# propagate our transport instance to the session protocol
		self.protocol.makeConnection(self)


if __name__ == "__main__":
	
	localhost = protocol.ClientCreator(reactor,TelnetConnection,FTPSession)
	localhost.connectTCP('localhost',23)
	
#	connectionFactory = protocol.ClientFactory()
#	connectionFactory.protocol = TelnetConnection
#	reactor.connectTCP('localhost',23,connectionFactory)
	#reactor.connectTCP('tcc25m.apo.nmsu.edu',23,connectionFactory)
	
	reactor.callLater(3.0,delayed1)
	
	reactor.run()
