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
	
	def session_login_failed(self):
		raise TelnetException('TelnetSession[%s]: VMS login failed' % self.name)

class TCCException(TelnetException):
	pass

class TCCSession(VMSSession):
	"""
	Manages a telnet client session to a TCC interpreter.
	
	The TCC interpreter is running via a telnet session to an OpenVMS
	host.
	"""
	tcc_command = 'telrun'
	tcc_ready = 'UserNum=(\d+); UserAdded'
	
#	parse_parameter_name = re.compile('\s*([A-Za-z_]+)\s*=?')

	line_pattern = re.compile('\r?0 (\d+) ([\:IWF>])\s+')
	token_pattern = re.compile('\s*([A-Za-z_]+)\s*(=\s*)?')
	
	def session_started(self):
		self.state = 'STARTING_INTERPRETER'
		self.send(self.tcc_command + '\n')

	def session_STARTING_INTERPRETER(self,data):
		started = re.search(self.tcc_ready,data)
		if started:
			self.user_num = int(started.group(1))
			print 'You are user number %d' % self.user_num
			self.update_pattern = re.compile('\r0 %d ([IWF]) (.+)' % self.user_num)
			self.state = 'COMMAND_LINE_READY'

	def parse_line(self,line):
		# try to parse the standard initial fields of the line
		parsed = self.line_pattern.match(line)
		if not parsed:
			raise TCCException("%s: cannot parse line '%s'"
				% (self.name,line.encode('ascii','backslashreplace')))
		(user_num,status) = parsed.groups()
		# split the rest of the line into tokens delimited by a semicolon
		keywords = { }
		for token in line[parsed.end():].split(';'):
			# split each token into (keyword,value) where value is None unless
			# the token	contains an equals sign
			parsed = self.token_pattern.match(token)
			if not parsed:
				raise TCCException("%s: cannot parse token '%s'"
					% (self.name,token.encode('ascii','backslashreplace')))
			if not parsed.group(2) and parsed.end() < len(token):
				raise TCCException("%s: bad keyword '%s'"
					% (self.name,token.encode('ascii','backslashreplace')))
			keyword = parsed.group(1)
			values = [ ]
			# split anything following an equals sign into values delimited by a comma
			for value in token[parsed.end():].split(','):
				values.append(value.strip())
			# store the results of parsing this token in a keywords dictionary
			keywords[keyword] = values
		# return the results of parsing this line
		return (user_num,status,keywords)

	def handle_command_response(self,response,command):
		print 'got response to "%s":' % command
		for line in response:
			if not line.strip():
				continue
			(user_num,status,keywords) = self.parse_line(line)
			print 'user=%s status=%s read %d keywords:' % (user_num,status,len(keywords))
			for (keyword,values) in keywords.iteritems():
				print '  %20s = (%s)' % (keyword,','.join(values))
			"""
			update_found = self.update_pattern.match(line)
			if update_found:
				status = update_found.group(1)
				for parameter_update in update_found.group(2).split(';'):
					name_parsed = self.parse_parameter_name.match(parameter_update)
					if not name_parsed:
						pass # what to do here?
					name = name_parsed.group(1)
					values = [
						val.strip() for val in parameter_update[name_parsed.end():].split(',')
					]
					print '"%s" has values (%s) [status %s]' % (name,','.join(values),status)
			"""

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
	print "Requesting show_users..."
	TelnetSession.do('VMS','show users').addCallback(got_users)
	
def show_status():
	print 'Requesting a TCC status update...'
	TelnetSession.do('TCC','axis status all')
	TelnetSession.do('TCC','mirror status')

if __name__ == "__main__":
	
	from getpass import getpass
	from twisted.internet import reactor,task
	from tops.core.network.telnet import prepareTelnetSession

	(hostname,port,username) = ('tcc25m.apo.nmsu.edu',23,'tcc')
	password = getpass('Enter password for %s@%s: ' % (username,hostname))
	
	prepareTelnetSession(VMSSession('VMS',username,password,debug=False),hostname,port)
	prepareTelnetSession(TCCSession('TCC',username,password,debug=False),hostname,port)
	
#	reactor.callLater(2.0,show_status)	
	task.LoopingCall(show_status).start(3.0,now=False)
	task.LoopingCall(show_users).start(5.0,now=False)
	
	reactor.run()
