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
# This project is hosted at sdss3.org and tops.googlecode.com

from twisted.internet.protocol import Factory
from twisted.web import resource,server,static
from twisted.python import log

from tops.core.network.naming import ResourceNamePattern,NamingException

import tops.core.utility.data as data

import archiving_pb2

class ArchiveManager(object):

	def __init__(self):
		self.sessions = { }
		self.channels = { }
		
	def createSession(self,hdr):
		"""
		Creates a new server session for a producer client.
		"""
		print 'creating new session for',hdr.name,'with',len(hdr.records),'records'
		records = [ ]
		for (rindex,record) in enumerate(hdr.records):
			assert(record.record_id == rindex)
			types = [ ]
			channels = [ ]
			for (cindex,channel) in enumerate(record.channels):
				full_name = "%s.%s" % (hdr.name,channel.channel_name)
				if full_name not in self.channels:
					self.channels[full_name] = (hdr.name,rindex,cindex)
				channels.append('???')
				types.append(data.factory(channel.value_type))
			records.append((types,channels))
		self.sessions[hdr.name] = records

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
		(types,channels) = self.sessions[hdr.name][msg.record_id]
		for (cindex,value) in enumerate(msg.values):
			channels[cindex] = types[cindex].unpack(value)
		
	def getValues(self,channels):
		"""
		Returns a list of channel values formatted as double-quoted strings.
		"""
		values = [ ]
		for channel in channels:
			(name,rindex,cindex) = self.channels[channel]
			(types,channels) = self.sessions[name][rindex]
			value = channels[cindex]
			values.append('"%s"' % value)
		return values


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
		self.factory.manager.setValues(self.hdr,msg)


def initialize():
	"""
	Starts the server main loop.
	"""
	from twisted.internet import reactor
	from twisted.python.logfile import LogFile
	import os,os.path,sys

	# load our run-time configuration
	import tops.core.utility.config as config
	verbose = config.initialize()

	# use file-based logging for ourself (print statements are automatically redirected)
	logpath = config.getfilename('archiver','logfile')
	if not logpath or logpath == 'stdout':
		log.startLogging(sys.stdout)
	else:
		(logpath,logfile) = os.path.split(logpath)
		log.startLogging(LogFile(logfile,logpath))

	print 'Executing',__file__,'as PID',os.getpid()
	try:
		# create an archive manager to connect our consumers to our producers
		manager = ArchiveManager()

		# initialize a TCP server to listen for local or network clients producing log messages
		factory = Factory()
		factory.protocol = ArchiveServer
		factory.manager = manager
		reactor.listenTCP(config.getint('archiver','tcp_port'),factory)
		reactor.listenUNIX(config.getfilename('archiver','unix_addr'),factory)

		# initialize an HTTP server to handle archive monitoring queries via http
		prepareWebServer(
			portNumber = config.getint('archiver','http_port'),
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
