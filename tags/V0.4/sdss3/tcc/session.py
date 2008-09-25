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
from tops.core.utility.astro_time import AstroTime,UTC,TAI

import message
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
	
	def session_started(self):
		self.state = 'STARTING_INTERPRETER'
		self.send(self.tcc_command + '\n')

	def session_STARTING_INTERPRETER(self,data):
		"""
		Processes incoming data while the interpreter is adding us
		"""
		for line in data.split('\n'):
			if line == self.tcc_command: # ignore our command echo
				continue
			(user_num,status,keywords) = self.process_line(line)
			# we assume that the next user added is us...is there a better way?
			if status and 'UserAdded' in keywords:
				self.user_num = user_num
				logging.info('connected as user number %d',self.user_num)
				self.state = 'COMMAND_LINE_READY'
				session.do('interpreter_started')

	def session_COMMAND_LINE_READY(self,data):
		"""
		Processes incoming data while a command is not running.
		"""
		for line in data.split('\n'):
			(user_num,status,keywords) = self.process_line(line)
	
	def session_COMMAND_LINE_BUSY(self,data):
		"""
		Processes incoming data while a command is running.
		"""
		for line in data.split('\n'):
			# ignore our command echo (a previous line may have already completed this command)
			if self.running and line == self.running.payload:
				continue
			(user_num,status,keywords) = self.process_line(line)
			if status and user_num == self.user_num and 'Cmd' in keywords:
				self.state = 'COMMAND_LINE_READY'
				if status == 'Done':
					self.done()
				else:
					self.error(TCCException('Command failed: %s' % self.running.payload))

	def process_line(self,line):
		"""
		Processes a new line of data received from the TCC
		"""
		if not line.strip(): # ignore blank lines
			return (None,None,None)
		try:
			(mystery_num,user_num,status,keywords) = message.parse(line)
			print '%2d %10s %s' % (user_num,status,keywords)
			if status == 'Done' and 'Cmd' in keywords:
				logging.info('user %d issued %s',user_num,keywords['Cmd'][0])
			elif 'UserAdded' in keywords:
				logging.warn('connected new user number %d' % user_num)

			# update records based on this message
			'''
			if 'AzStat' in keywords:
				try:
					(pos,vel,tai,stat) = keywords['AzStat']
					print (pos,vel,tai,stat)
					archiving.update(self.timestamp(tai),'AzStat',{
						'pos': float(pos),
						'vel': float(vel),
						'stat': int(stat,16)
					})
				except ValueError:
					logging.warn('unable to parse AzStat values: %r',keywords['AzStat'])
			'''

			return (user_num,status,keywords)
		except message.MessageError,e:
			logging.warn('unable to parse line >>%r<<',line)
			return (None,None,None)

	def timestamp(self,tai):
		"""
		Converts an TAI timestamp expressed as MJD seconds(!) into a UTC timestamp
		"""
		# convert from MJD seconds to MJD days
		try:
			mjdtai = float(tai)/86400.
		except ValueError:
			logging.warn('unable to convert MJD TAI timestamp: %r',tai)
			# as a fallback, return the current time
			return AstroTime.now(UTC)
		when = AstroTime.fromMJD(mjdtai,TAI)
		return when.astimezone(UTC)

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
				'nproc.tcc':			users['TCC'],
				'nproc.tccuser':		users['TCCUSER']
		})

def show_users():
	TelnetSession.do('VMS','show users').addCallback(got_users)
	
def show_status():
	TelnetSession.do('TCC','axis status all')
	#TelnetSession.do('TCC','mirror status')


def configure():
	"""
	Perform startup configuration of the session proxy.
	"""
	from twisted.internet import task
	from tops.core.network.telnet import prepareTelnetSession

	# lookup our connection parameters
	hostname = config.get('tcc.session','telnet_host')
	port= config.getint('tcc.session','telnet_port')
	username = config.get('tcc.session','telnet_user')
	password = config.getsecret('tcc.session','telnet_pw')
	
	# initialize our telnet sessions
	prepareTelnetSession(VMSSession('VMS',username,password,debug=False),hostname,port)
	prepareTelnetSession(TCCSession('TCC',username,password,debug=False),hostname,port)
	
	# initialize periodic commands
	#task.LoopingCall(show_status).start(5.0,now=False)
	task.LoopingCall(show_users).start(5.0,now=False)

	
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
			On('login_failed').goto('FAULT'),
			On('command_overflow').goto('FAULT')
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
			#,Monitor('AzStat',
			#	('pos',				data.double),
			#	('vel',				data.double),
			#	('status',			data.unsigned)
			#)
		),
		ProxyState('FAULT',
			"""
			A fault condition has been signalled.
			"""
		)
	)
	
	session.start()
