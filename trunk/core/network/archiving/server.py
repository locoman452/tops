"""
Implements the server side of distributed archiving

The archiving server simultaneously handles messages arriving from
producer clients and serves consumer clients via a web server.
"""

## @package tops.core.network.archiving.server
# Implements the server side of distributed archiving
#
# @author David Kirkby, dkirkby@uci.edu
# @date Created 21-Aug-2008
#
# This project is hosted at http://tops.googlecode.com/

from twisted.internet.protocol import Factory
from twisted.web import resource,server,static
from twisted.python import log

from tops.core.network.naming import ResourceNamePattern,NamingException

import archiving_pb2

class ArchiveManager(object):

	def __init__(self):
		self.sessions = { }
		self.channels = { }
		
	def createSession(self,hdr):
		"""
		Creates a new server session for a producer client.
		"""
		if hdr.name not in self.sessions:
			# should generate a log message here...
			self.sessions[hdr.name] = [ ]
		self.sessions[hdr.name].append(hdr)
		for record in hdr.records:
			for channel in record.channels:
				full_name = "%s.%s" % (hdr.name,channel.channel_name)
				if full_name not in self.channels:
					self.channels[full_name] = "???"

	def subscribe(self,pattern):
		"""
		Subscribes a consumer client to channels matching the specified pattern.
		"""
		try:
			filter = ResourceNamePattern(pattern)
		except NamingException:
			return [ ]
		return [ channel for channel in sorted(self.channels) if filter.matches(channel) ]
		
	def setValues(self,hdr,msg):
		"""
		Updates the current values of the channels associated with one record.
		"""
		print 'setting values for record id',msg.id,'of',hdr.name
		
	def getValues(self,channels):
		"""
		Returns a list of channel values formatted as double-quoted strings.
		"""
		return [('"%s"' % self.channels[channel]) for channel in channels]


from tops.core.network.webserver import WebQuery,prepareWebServer

class ArchiveQuery(WebQuery):

	ServiceName = 'ARCHIVER'
	
	def GET(self,request,session,state):
		try:
			values = session.site.manager.getValues(state.channels)
		except AttributeError:
			values = [ ]
		return '({"values":[%s]})' % ','.join(values)

	def POST(self,request,session,state):
		pattern = self.get_arg('pattern')
		if pattern:
			print 'subscribing %d with pattern "%s"' % (id(state),pattern)
			# subscribe this client with this pattern
			state.channels = session.site.manager.subscribe(pattern)
			json_items = [ ]
			for channel in state.channels:
				json_items.append('{"name":"%s"}' % (channel))
			return '({"channels":[%s]})' % ','.join(json_items)
		return '({})'

from tops.core.network.server import Server

class ArchiveServer(Server):
	
	Header = archiving_pb2.Header
	Message = archiving_pb2.Update
	
	def handleHeader(self,hdr):
		self.hdr = hdr
		self.factory.manager.createSession(hdr)

	def handleMessage(self,msg):
		print msg
		self.factory.manager.setValues(self.hdr,msg)


def initialize():
	"""
	Starts the server main loop.
	"""
	from twisted.internet import reactor
	from twisted.python.logfile import LogFile
	import os,os.path,sys

	# use file-based logging for ourself (print statements are automatically redirected)
	log.startLogging(sys.stdout)
	#log.startLogging(LogFile('logserver','logs'))
	print 'Executing',__file__,'as PID',os.getpid()

	try:
		# create an archive manager to connect our consumers to our producers
		manager = ArchiveManager()

		# initialize a TCP server to listen for local or network clients producing log messages
		factory = Factory()
		factory.protocol = ArchiveServer
		factory.manager = manager
		reactor.listenTCP(1967,factory)
		reactor.listenUNIX('/tmp/archive-server',factory)

		# initialize an HTTP server to handle archive monitoring queries via http
		prepareWebServer(
			portNumber = 8081,
			handlers = {"feed":ArchiveQuery()},
			properties = {"manager":manager},
			filterLogs = True
		)

		# fire up the reactor
		print 'Waiting for clients...'
		reactor.run()

	except Exception:
		print 'Reactor startup failed'
		# How do I release my unix socket cleanly here?
		#reactor.stop()
		raise

if __name__ == '__main__':
	initialize()
