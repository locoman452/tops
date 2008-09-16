"""
Supports remote operations via the telnet protocol

Defines the twisted protocol classes necessary to establish and control
a telnet client session. Based on the classes in twisted.conch.telnet.
"""

## @package tops.sdss3.tcc.session
# Supports remote operations via the telnet protocol
#
# @author David Kirkby, dkirkby@uci.edu
# @date Created 13-Sep-2008
#
# This project is hosted at http://tops.googlecode.com/

from twisted.conch import telnet
from twisted.internet import defer

from collections import deque

class TelnetException(Exception):
	pass

class TelnetSession(telnet.TelnetProtocol):
	"""
	Manages the application-level protocol for a telnet client session.
	
	Subclasses must be customized for a specific telnet host environment
	by setting the values of the following class attributes:
	login_prompt, password_prompt and command_prompt. The per-instance
	username and password are passed in to the class constructor.
	
	A TelnetSession implements an input-driven state machine to perform
	authentication and issue commands. Subclasses can extend this state
	machine following the pattern established here, which requires
	providing a method session_XXX(self,data) for each new state XXX.
	This method will be called when new input data is received in the
	"XXX" state, and can trigger a state change by setting the string
	value of self.state. Subclasses may also want to override the
	session_started() or session_login_failed() methods. Setting
	debug=True is useful for debugging a new subclass as it prints out
	all input and output (except for a user's password).
	
	Users normally interact with a TelnetSession via the asynchronous
	TelnetSession.do() method.
	
	TelnetSession relies on the services of TelnetConnection to handle
	the low-level telnet protocol.
	"""

	# If there are more than this number of commands queued, assume that something
	# is broken and signal an error condition to subsequent command issuers.
	MAX_QUEUED = 10

	registry = { }
	
	@staticmethod
	def do(session_name,command):
		try:
			session = TelnetSession.registry[session_name]
		except KeyError:
			return defer.fail(TelnetException('No such session registered: "%s"' % session_name))
		return session._do(command)

	def __init__(self,myname,username,password,debug=False):
		if myname in self.registry:
			raise TelnetException('cannot create second session with name "%s"' % myname)
		self.name = myname
		self.debug = debug
		if self.debug:
			print 'TelnetSession: initializing "%s" (%s)' % (myname,self.__class__.__name__)
		self.registry[myname] = self
		# remember our authentication info
		self.username = username
		self.password = password
		# initialize our state machine
		self.state = 'CONNECTING'
		# initialize our command queue
		self.queue = deque()
		# telnet.TelnetProtocol has no __init__ method to call

	def send(self,data,secret=False):
		"""Writes data through our connection transport"""
		if self.debug:
			if secret:
				print 'TelnetSession[%s]: sending something secret' % self.name
			else:
				print ('TelnetSession[%s]: sending %r'
					% (self.name,data.encode('ascii','backslashreplace')))
		self.transport.write(data)

	def dataReceived(self,data):
		"""Drives a state machine based on the input received"""
		if self.debug:
			print ("TelnetSession[%s]: got %r in state '%s'" %
				(self.name,data.encode('ascii','backslashreplace'),self.state))
		oldState = self.state
		getattr(self, "session_" + self.state)(data)
		if self.debug and self.state != oldState:
			print 'TelnetSession[%s]: entering new state "%s"' % (self.name,self.state)

	def session_CONNECTING(self,data):
		if data.endswith(self.login_prompt):
			self.state = 'AUTHENTICATING'
			self.send(self.username+'\n')

	def session_AUTHENTICATING(self,data):
		if data.endswith(self.password_prompt):
			self.send(self.password + '\n',secret=True)
		elif data.endswith(self.login_prompt):
			self.session_login_failed()
		elif data.endswith(self.command_prompt):
			self.session_started()

	def session_started(self):
		"""
		Called when we first get a command line prompt.
		
		This default implementation gets us ready to handle commands.
		Subclasses can override this method to launch a program with its
		own command line interface.
		"""
		self.state = 'COMMAND_LINE_READY'

	def session_login_failed(self):
		"""
		Called if our initial login attempt yields another login prompt.
		
		The default implementation parks our state machine in the
		LOGIN_FAILED state which, by default, is a terminal state.
		Alternatively, you could bump the state machine into the
		'CONNECTING' state which will re-attempt the login handshake
		(but don't do this indefinitely.)
		
		If you do not detect this condition by overriding this method or
		inspecting self.state, your command handlers will never be
		called back and your command queue may fill up.
		"""
		self.state = 'LOGIN_FAILED'

	def session_LOGIN_FAILED(self,data):
		pass
			
	def session_COMMAND_LINE_READY(self,data):
		pass
		
	def session_COMMAND_LINE_BUSY(self,data):
		# Break the data into lines
		lines = data.split('\n')
		if lines[-1] == '':
			del lines[-1]
		# Ignore a command echo
		if len(self.command_response) == 0 and lines[0] == self.command_string:
			del lines[0]
		# Have we seen all of the command's response now?
		completed = len(lines) > 0 and lines[-1].endswith(self.command_prompt)
		if completed:
			del lines[-1]
		# Append the new lines to the command response.			
		self.command_response.extend(lines)
		# Update our state if necessary
		if completed:
			if self.debug:
				print 'TelnetSession[%s]: response from last command:' % self.name
				for data in self.command_response:
					print repr(data.encode('ascii','backslashreplace'))
			# Notify any callbacks that the command has completed
			self.command_defer.callback(self.command_response)
			# Update our state machine
			self.state = 'COMMAND_LINE_READY'
			# Submit the next queued command, if any
			try:
				self._submit(*self.queue.popleft())
			except IndexError:
				# idle until we receive a new command
				pass
		
	def _submit(self,command,deferred):
		if self.debug:
			print 'TelnetSession[%s]: submitting command "%s"' % (self.name,command)
		assert(self.state == 'COMMAND_LINE_READY')
		# remember the command we are currently running
		self.command_string = command
		self.command_defer = deferred
		# prepare to collect the command response
		self.command_response = [ ]
		self.state = 'COMMAND_LINE_BUSY'
		# send the command
		self.send(command + '\n')

	def _do(self,command):
		deferred = defer.Deferred()
		# can we actually submit this command now?
		if self.state == 'COMMAND_LINE_READY':		
			self._submit(command,deferred)
		else:
			# queue this one for later
			if len(self.queue) > self.MAX_QUEUED:
				return defer.fail(TelnetException('%s: command queue overflow' % self.name))
			self.queue.append((command,deferred))
			if self.debug:
				print ('TelnetSession[%s]: queued command "%s" (now %d in the queue)'
					% (self.name,command,len(self.queue)))
		return deferred


class TelnetConnection(telnet.TelnetTransport):
	"""
	Manages the connection-level protocol for a telnet client session.
	
	Application-level data is delegated to a TelnetSession instance.
	"""

	def __init__(self,session_protocol):
		# create a session instance to handle the application-level protocol
		assert(isinstance(session_protocol,TelnetSession))
		self.protocol = session_protocol
		telnet.TelnetTransport.__init__(self)

	def connectionMade(self):
		# propagate our transport instance to the session protocol
		self.protocol.makeConnection(self)


from twisted.internet import protocol,reactor

def prepareTelnetSession(SessionClass,hostname,port=23):
	"""
	Prepares a telnet client session.
	
	SessionClass defines the authentication sequence required and
	handles the application-level protocol. The session does not start
	until the twisted reactor is started.
	"""
	session = protocol.ClientCreator(reactor,TelnetConnection,SessionClass)
	session.connectTCP(hostname,port)
