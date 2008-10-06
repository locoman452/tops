"""
Implements a generic web server

Defines a twisted web site that serves static files and handles dynamic
requests.
"""

## @package tops.core.network.webserver
# Implements a generic web server
#
# @author David Kirkby, dkirkby@uci.edu
# @date Created 10-Sep-2008
#
# This project is hosted at sdss3.org and tops.googlecode.com

from twisted.web import resource,server,static
from twisted.internet import reactor

import re

class SessionState(object):
	pass

class WebQuery(resource.Resource):
	"""
	Implements a web resource that handles GET and POST requests.
	
	Requests are matched to a per-service and per-client-window session
	state object. The client must include a 'uid' parameter in the
	request to support the per-client-window session state mapping.
	"""
	ServiceName = 'UNKNOWN'
	isLeaf = True

	def get_arg(self,name,default=None):
		try:
			return self.args[name][0]
		except (AttributeError,KeyError):
			return default

	def prepare(self,request):
		self.args = request.args
		request.sitepath = [self.ServiceName]
		session = request.getSession()
		if not 'uid' in request.args:
			uid = 0
		else:
			uid = request.args['uid'][0]
		#print 'Retrieving session state for uid',uid,'in',id(session)
		if not hasattr(session,'state'):
			session.state = { }
		if not uid in session.state:
			session.state[uid] = SessionState()
		return (session,session.state[uid])

	def render_GET(self, request):
		(session,state) = self.prepare(request)
		return self.GET(request,session,state)
			
	def render_POST(self, request):
		(session,state) = self.prepare(request)
		return self.POST(request,session,state)


class FilteredSite(server.Site):
	"""
	A web site that filters out request logs from certain sites.
	
	Use this class to filter out the log messages that would be
	generated by, for example, periodic AJAX requests. Set a
	filtered_paths attribute of your site instance to a list of URI
	regular-expression patterns that should be filtered use re.match.
	"""
	def log(self,request):
		if hasattr(self,'filtered_paths'):
			for path in self.filtered_paths:
				if path.match(request.uri):
					return None
		return server.Site.log(self,request)


def prepareWebServer(portNumber,handlers,properties,filterLogs=True):
	"""
	Prepares a web server to serve static and dynamic content.
	
	Static content is served from tops.core.network.web as /shared/ and
	also from the web/ sub-directory where the main program resides as
	/local/. Dynamic content is served via the specified handlers, if
	any. The server will not actually run until the twisted reactor is
	started. If filterLogs is True, then requests for dynamic content
	will not be logged.
	"""
	import sys,os.path
	# figure out the path of our shared static content
	from tops.core.network import __path__ as shared_parent
	shared_web = os.path.join(shared_parent[0],'web')
	# figure out the path of our local static content
	local_parent = os.path.abspath(os.path.dirname(sys.modules['__main__'].__file__))
	local_web = os.path.join(local_parent,'web')
	# create an empty root for our site
	root = resource.Resource()
	# serve our shared and local static content
	root.putChild('shared',static.File(shared_web))
	root.putChild('local',static.File(local_web))
	# serve any handlers
	for (path,handler) in handlers.iteritems():
		root.putChild(path,handler)
	# create the site for our content
	site = FilteredSite(root)
	if filterLogs:
		site.filtered_paths = [re.compile('/%s' % path) for path in handlers.keys()]
	# add any properties to the site object so they are accessible to
	# query handlers via session.site.<name>
	for (name,value) in properties.iteritems():
		setattr(site,name,value)
	reactor.listenTCP(portNumber,site)
