"""
Implements the server side of distributed logging

The logging server simultaneously handles messages arriving from
producer clients and serves consumer clients via a web server.
"""

## @package tops.core.network.logging.server
# Implements the server side of distributed logging
#
# @author David Kirkby, dkirkby@uci.edu
# @date Created 8-Aug-2008
#
# This project is hosted at http://tops.googlecode.com/

from twisted.internet.protocol import Factory
from twisted.internet.task import LoopingCall
from twisted.web import resource,server,static
from twisted.python import log

from collections import deque
from record import *
from datetime import datetime,timedelta

from logging import DEBUG

import logging_pb2

class FeedBuffer(object):
	"""
	Maintains an in-memory buffer of recent log messages.
	"""
	def __init__(self,maxdepth=100):
		self.maxdepth = maxdepth
		self.buffer = deque()
		self.hdr = logging_pb2.Header()
		self.hdr.name = 'logging.server'
		self.msgCount = 0
		self.starttime = datetime.now()
		LoopingCall(self.statusMessage).start(60.0)

	def add(self,record):
		self.buffer.append(record)
		if len(self.buffer) > self.maxdepth:
			self.buffer.popleft()
		self.msgCount += 1

	def dump(self,filt):
		items = ',\n\t'.join([r.json() for r in self.buffer if filt.selects(r)])
		return '({"items":[' + items + ']})'

	def statusMessage(self):
		msg = logging_pb2.Message()
		msg.levelno = DEBUG
		elapsed = datetime.now() - self.starttime
		elapsed = timedelta(elapsed.days,elapsed.seconds)
		msg.body = 'Server has been running %s and handled %u messages.' % (elapsed,self.msgCount) 
		self.add(LogRecord(msg,self.hdr))


class FeedUpdate(resource.Resource):
	"""
	Serves filtered updates from the site's FeedBuffer via JSON
	responses to HTTP GET queries. Listens to POST queries to configure
	the per-session filter.
	"""
	isLeaf = True

	def render_GET(self, request):
		request.sitepath = ['LOGGER']
		session = request.getSession()
		try:
			uid = request.args['uid'][0]
			#print 'Retrieving session filter for',uid,'in',id(session)
			filt = session.filter[uid]
			return session.site.feed.dump(filt)
		except AttributeError:
			print 'Cannot determine filter from GET args'
			log.err()
			return '{"status":"ERROR"}'
	
	def render_POST(self, request):
		request.sitepath = ['LOGGER']
		session = request.getSession()
		try:
			(uid,sourceFilter,minLevel) = (
				request.args[name][0] for name in ['uid','sourceFilter','minLevel'])
			filter = LogFilter(sourceFilter,minLevel)
			if not hasattr(session,'filter'):
				session.filter = { }
			#print 'Storing session filter for',uid,'in',id(session)
			session.filter[uid] = filter
			return 'OK'
		except:
			print 'Cannot find expected POST args'
			log.err()
			return 'ERROR'


from tops.core.network.server import Server

class LogServer(Server):
	"""
	Receives log messages from local and remote clients and feeds them into a central buffer.
	"""
	Header = logging_pb2.Header
	Message = logging_pb2.Message
	
	def handleMessage(self,msg):
		record = LogRecord(msg,self.hdr)
		self.factory.feed.add(record)
		print record

		
def initialize():
	"""
	Starts the server main loop.
	"""
	from twisted.internet import reactor
	from twisted.python.logfile import LogFile
	import sys
	import os,os.path

	# use file-based logging for ourself (print statements are automatically redirected)
	log.startLogging(sys.stdout)
	#log.startLogging(LogFile('logserver','logs'))
	print 'Executing',__file__,'as PID',os.getpid()

	# create a record buffer to connect our feed watchers to our clients
	feed = FeedBuffer()
	
	# initialize a TCP server to listen for local or network clients producing log messages
	factory = Factory()
	factory.protocol = LogServer
	factory.feed = feed
	reactor.listenTCP(1966,factory)
	reactor.listenUNIX('/tmp/log-server',factory)

	# initialize an HTTP server to handle feed watcher requests via http
	webpath = os.path.join(os.path.dirname(__file__),'web')
	root = static.File(webpath)
	root.indexNames = ['logwatch.html'] # sets default and prevents listing directory
	root.putChild("feed",FeedUpdate())
	site = server.Site(root)
	site.feed = feed
	reactor.listenTCP(8080,site)

	# fire up the reactor
	print 'Waiting for clients...'
	reactor.run()

if __name__ == '__main__':
	initialize()
