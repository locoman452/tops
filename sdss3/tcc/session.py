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

from tops.core.network.proxy import *

from tops.core.network.telnet import TelnetSession,TelnetException
from tops.core.utility.astro_time import AstroTime,UTC

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
		session.do('login_failed')

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
	
	# TCC status codes from src/subr/msg/format.for
	status_codes = {
		':': 'Done',    # also 'Superceded'
		'>': 'Started',
		'I': 'Information',
		'W': 'Warning',
		'F': 'Error',
		'!': 'Fatal'
	}
	
	# regular expressions for parsing message lines and token strings
	line_pattern = re.compile('\r?0 (\d+) ([\:IWF>])\s+')
	token_pattern = re.compile('\s*([A-Za-z0-9_]+)\s*(=\s*)?')
	
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
			session.do('interpreter_started')
			
	def session_COMMAND_LINE_READY(self,data):
		"""
		Processes new incoming data while a command is not running.
		"""
		for line in data.split('\n'):
			if not line.strip():
				# ignore blank lines
				continue
			print self.parse_line(line)
	
	def session_COMMAND_LINE_BUSY(self,data):
		"""
		Processes new incoming data while a command is running.
		"""
		for line in data.split('\n'):
			if not line.strip():
				# ignore blank lines
				continue
			if line == self.running.payload:
				# ignore the TCC's echo of a command we just submitted
				continue
			(user_num,status,keywords) = self.parse_line(line)
			print (user_num,status,keywords)
			if user_num == self.user_num and 'Cmd' in keywords:
				print 'got Cmd',keywords['Cmd']
				#assert(keywords['Cmd'] == [self.running.payload])
				# this line marks the completion of our running command
				self.state = 'COMMAND_LINE_READY'
				if status == 'Done':
					self.done()
				else:
					self.error(TCCException('Command failed: %s' % self.running.payload()))

	def parse_line(self,line):
		# try to parse the standard initial fields of the line
		parsed = self.line_pattern.match(line)
		if not parsed:
			raise TCCException("%s: cannot parse line '%s'"
				% (self.name,line.encode('ascii','backslashreplace')))
		(user_num,status) = parsed.groups()
		user_num = int(user_num)
		if status in self.status_codes:
			status = self.status_codes[status]
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

def got_users(response):
	users = { 'TCC':0, 'TCCUSER':0 }
	parser = re.compile('\s*(TCC|TCCUSER)\s+([0-9]+)')
	for line in response:
		match = parser.match(line)
		if match:
			users[match.group(1)] = int(match.group(2))
	for (username,nproc) in users.iteritems():
		print '%s is running %d processes' % (username,nproc)
	utc = AstroTime.now(UTC)
	archiving.update(utc,'vms',{
		'nproc.tcc':		users['TCC'],
		'nproc.tccuser':	users['TCCUSER']
	})

def show_users():
	print "Requesting show_users..."
	TelnetSession.do('VMS','show users').addCallback(got_users)
	
def show_status():
	print 'Requesting a TCC status update...'
	TelnetSession.do('TCC','axis status all')
	TelnetSession.do('TCC','mirror status')

def configure():
	"""
	Perform startup configuration of the session proxy.
	"""
	from twisted.internet import reactor,task
	from tops.core.network.telnet import prepareTelnetSession

	(hostname,port,username) = ('tcc25m.apo.nmsu.edu',23,'tcc')
	password = config.getsecret('tcc.session','password')
	
	prepareTelnetSession(VMSSession('VMS',username,password,debug=False),hostname,port)
	prepareTelnetSession(TCCSession('TCC',username,password,debug=False),hostname,port)
	
	#task.LoopingCall(show_status).start(3.0,now=False)
	#task.LoopingCall(show_users).start(5.0,now=False)

	
if __name__ == '__main__':

	initialize('tcc.session')
	
	#########################################################################
	# Define the proxy's states and data
	#########################################################################

	session = Proxy('TCC_SESSION -> CONNECTING',
		ProxyState('CONNECTING',
			"""
			Establishing telnet session with the TCC.
			""",
			On('interpreter_started').goto('READY'),
			On('login_failed').goto('FAULT')
		),
		ProxyState('READY',
			"""
			TCC interpreter session has been established. TCC status keywords
			are being periodically read and fed to the archiver.
			""",
			#On('timeout').goto('FAULT'),
			Monitor('vms',
				('nproc.tcc',		data.unsigned),
				('nproc.tccuser',	data.unsigned)
			)
		),
		ProxyState('FAULT',
			"""
			A fault condition has been signalled.
			"""
		)
	)
	
	session.start()
