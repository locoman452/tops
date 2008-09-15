"""
Tests core telnet services

Creates two telnet client sessions, both to localhost, that run in
parallel handling asynchronous commands. One session allows command to
be sent directly to the login shell and the other runs ftp and
interfaces to the ftp command line.

The connection parameters provided below below should be customized for
the testing host and the telnet service must be enabled on localhost.
Because of this, no automatic unit tests are implemented here.

For a more complex example of telnet client programming within the
framework of a proxy, refer to tops.sdss3.tcc.session.
"""

## @package tops.core.network.test
# Tests core telnet services
#
# @author David Kirkby, dkirkby@uci.edu
# @date Created 15-Sep-2008
#
# This project is hosted at http://tops.googlecode.com/

from tops.core.network.telnet import TelnetSession

class LocalhostSession(TelnetSession):
	"""
	Manages a telnet client session to localhost.
	
	The username and password to use are provided to our constructor.
	You will probably need to modify login_prompt, password_prompt and
	command_prompt for your testing environment.
	"""
	login_prompt = 'login: '
	password_prompt = 'Password:'
	command_prompt = '~ % '

class FTPSession(LocalhostSession):
	"""
	Manages an ftp command line via telnet to localhost.
	
	The localhost username and password are provided to our constructor.
	You many need to modify ftp_command and ftp_prompt for your testing
	environment.
	"""
	ftp_command = 'ftp'
	ftp_prompt = 'ftp> '

	def session_started(self):
		self.state = 'STARTING_FTP'
		self.send(self.ftp_command + '\n')

	def session_STARTING_FTP(self,data):
		if data.endswith(self.ftp_prompt):
			self.command_prompt = self.ftp_prompt
			self.state = 'COMMAND_LINE_READY'

# The following three global methods are called asynchronously within the
# twisted reactor framework below.

def answer(response,command):
	print 'the answer to "%s" is:\n%s' % (command,'\n'.join(response))

def ftp_commands():
	print "Running ftp_commands..."
	TelnetSession.do('FTP','debug').addCallback(answer,'debug toggle 1')
	TelnetSession.do('FTP','help set').addCallback(answer,'help set')
	TelnetSession.do('FTP','debug').addCallback(answer,'debug toggle 2')

def localhost_commands():
	print "Running localhost_commands..."
	TelnetSession.do('localhost','pwd').addCallback(answer,'pwd')
	TelnetSession.do('localhost','whoami').addCallback(answer,'whoami')

	from getpass import getpass
	from twisted.internet import reactor
	from tops.core.network.telnet import prepareTelnetSession

if __name__ == "__main__":

	from getpass import getpass
	from twisted.internet import reactor
	from tops.core.network.telnet import prepareTelnetSession

	# Update these connection parameters for your testing environment
	debug = False
	(hostname,port,username) = ('localhost',23,'david')
	password = getpass('Enter password for %s@%s: ' % (username,hostname))

	# prepare two parallel telnet client sessions
	prepareTelnetSession(FTPSession('FTP',username,password,debug),hostname,port)
	prepareTelnetSession(LocalhostSession('localhost',username,password,debug),hostname,port)

	# schedule commands to be sent asynchronously to both sessions
	reactor.callLater(1.0,ftp_commands)
	reactor.callLater(1.1,localhost_commands)
	
	# schedule our program's exit
	reactor.callLater(3.0,reactor.stop)

	# fire up the reactor
	reactor.run()