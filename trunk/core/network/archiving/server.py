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

import archiving_pb2

class ArchiveManager(object):

	def __init__(self):
		self.sessions = { }
		self.fields = { }
		
	def createSession(self,hdr):
		if hdr.name not in self.sessions:
			# should generate a log message here...
			self.sessions[hdr.name] = [ ]
		self.sessions[hdr.name].append(hdr)
		for record in hdr.records:
			for field in record.fields:
				if field.field_name not in self.fields:
					self.fields[field.field_name] = hdr.name
				elif not self.fields[field.field_name] == hdr.name:
					# what if source name has changed since last session??
					pass

	def getFields(self):
		items = ',\n\t'.join(['{"name":"%s"}' % field for field in sorted(self.fields)])
		return '({"items":[' + items + ']})'
	

from tops.core.network.webserver import WebQuery

class ArchiveQuery(WebQuery):

	ServiceName = 'ARCHIVER'
	
	def GET(self,request,session,state):
		return session.site.manager.getFields()


from tops.core.network.server import Server

class ArchiveServer(Server):
	
	Header = archiving_pb2.Header
	Message = archiving_pb2.Update
	
	def handleHeader(self,hdr):
		print hdr
		self.factory.manager.createSession(hdr)

	def handleMessage(self,msg):
		print msg


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

	# create an archive manager to connect our consumers to our producers
	manager = ArchiveManager()

	# initialize a TCP server to listen for local or network clients producing log messages
	factory = Factory()
	factory.protocol = ArchiveServer
	factory.manager = manager
	reactor.listenTCP(1967,factory)
	reactor.listenUNIX('/tmp/archive-server',factory)

	# initialize an HTTP server to handle feed watcher requests via http
	webpath = os.path.join(os.path.dirname(__file__),'web')
	root = static.File(webpath)
	root.indexNames = ['archiver.html'] # sets default and prevents listing directory
	root.putChild("query",ArchiveQuery())
	site = server.Site(root)
	site.manager = manager
	reactor.listenTCP(8081,site)

	# fire up the reactor
	print 'Waiting for clients...'
	reactor.run()

if __name__ == '__main__':
	initialize()
