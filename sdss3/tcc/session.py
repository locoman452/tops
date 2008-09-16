"""
Implements a read-write proxy for the TCC command interpreter

Defines the custom data types associated with the TCC's command
interpreter, and implements a proxy that can issue commands via a pair
of telnet sessions: one connected to the VMS DCL command line and the
other connected to a TCC interpreter session command line.

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

from tops.core.network.telnet import TelnetSession,TelnetException

import re

class VMSSession(TelnetSession):
	"""
	Manages a telnet client session to an OpenVMS host.
	"""
	login_prompt = 'Username: '
	password_prompt = 'Password: '
	command_prompt = '$ '
	end_of_line = '\n\r'
	
	def session_login_failed(self):
		raise TelnetException('TelnetSession[%s]: VMS login failed' % self.name)


class TCCSession(VMSSession):
	"""
	Manages a telnet client session to a TCC interpreter.
	
	The TCC interpreter is running via a telnet session to an OpenVMS
	host.
	"""
	tcc_command = 'telrun'
	tcc_ready = 'UserNum=(\d+); UserAdded'
	
	def session_started(self):
		self.state = 'STARTING_INTERPRETER'
		self.send(self.tcc_command + '\n')

	def session_STARTING_INTERPRETER(self,data):
		started = re.search(self.tcc_ready,data)
		if started:
			self.user_num = int(started.group(1))
			print 'You are user number %d' % self.user_num
			self.state = 'COMMAND_LINE_READY'

	def _submit(self,command,deferred):
		self.command_prompt = '0 %d : Cmd="%s"' % (self.user_num,command.replace('"',r'\"'))
		VMSSession._submit(self,command,deferred)


def got_users(response):
	users = { 'TCC':0, 'TCCUSER':0 }
	parser = re.compile('\s*(TCC|TCCUSER)\s+([0-9]+)')
	for line in response:
		match = parser.match(line)
		if match:
			users[match.group(1)] = int(match.group(2))
	for (username,nproc) in users.iteritems():
		print '%s is running %d processes' % (username,nproc)

def show_users():
	print "Running show_users..."
	TelnetSession.do('VMS','show users').addCallback(got_users)
	
def tcc_response(response):
	print 'tcc response:\n>>%s' % '\n>>'.join(response)

def show_weather():
	print 'Running show_weather...'
	TelnetSession.do('TCC','show weather').addCallback(tcc_response)

if __name__ == "__main__":
	
	from getpass import getpass
	from twisted.internet import reactor,task
	from tops.core.network.telnet import prepareTelnetSession

	(hostname,port,username) = ('tcc25m.apo.nmsu.edu',23,'tcc')
	password = getpass('Enter password for %s@%s: ' % (username,hostname))
	
	prepareTelnetSession(VMSSession('VMS',username,password,debug=False),hostname,port)
	prepareTelnetSession(TCCSession('TCC',username,password,debug=True),hostname,port)
	
	reactor.callLater(2.0,show_weather)
	
#	looper = task.LoopingCall(show_users)
#	looper.start(1.0)
	
	reactor.run()
