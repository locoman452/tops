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
	
	parse_parameter_name = re.compile('\s*([A-Za-z_]+)\s*=')
	
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
			self.update_pattern = re.compile('\r0 %d I (.+)' % self.user_num)
			self.state = 'COMMAND_LINE_READY'

	def handle_command_response(self,response,command):
		print 'got response to "%s":' % command
		for line in response:
			update_found = self.update_pattern.match(line)
			if update_found:
				for parameter_update in update_found.group(1).split(';'):
					name_parsed = self.parse_parameter_name.match(parameter_update)
					if not name_parsed:
						pass # what to do here?
					name = name_parsed.group(1)
					values = [
						val.strip() for val in parameter_update[name_parsed.end():].split(',')
					]
					print '"%s" has values %s' % (name,','.join(values))
						

	def _submit(self,command,deferred):
		self.command_prompt = '\r0 %d : Cmd="%s"' % (self.user_num,command.replace('"',r'\"'))
		deferred.addCallback(self.handle_command_response,command)
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
	
def handle_tcc_command_response(response):
	print 'tcc response:\n>>%s' % '\n>>'.join(response)
	for line in response:
		update_found = self.update_pattern.match(line)
		if update_found:
			parameters = update_found.group(1)
			print 'got update for parameters:',parameters

def show_status():
	print 'Running show_status...'
	TelnetSession.do('TCC','show status')

if __name__ == "__main__":
	
	from getpass import getpass
	from twisted.internet import reactor,task
	from tops.core.network.telnet import prepareTelnetSession

	(hostname,port,username) = ('tcc25m.apo.nmsu.edu',23,'tcc')
	password = getpass('Enter password for %s@%s: ' % (username,hostname))
	
	prepareTelnetSession(VMSSession('VMS',username,password,debug=False),hostname,port)
	prepareTelnetSession(TCCSession('TCC',username,password,debug=False),hostname,port)
	
	reactor.callLater(2.0,show_status)
	
#	looper = task.LoopingCall(show_users)
#	looper.start(1.0)
	
	reactor.run()
