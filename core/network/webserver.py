"""
Implements a generic web server

Defines a twisted web site that serves static files and handles dynamic
requests.
"""

## @package tops.core.network.archiving.server
# Implements a generic web server
#
# @author David Kirkby, dkirkby@uci.edu
# @date Created 10-Sep-2008
#
# This project is hosted at http://tops.googlecode.com/

from twisted.web import resource,server,static
from twisted.internet import reactor

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

	def prepare(self,request):
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


def prepareWebServer(portNumber,handlers,properties):
	"""
	Prepares a web server to serve static and dynamic content.
	
	Static content is served from tops.core.network.web as /shared/ and
	also from the web/ sub-directory where the main program resides as
	/local/. The server will not actually run until the twisted reactor
	is started.
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
	site = server.Site(root)
	# add any properties to the site object so they are accessible to
	# query handlers via session.site.<name>
	for (name,value) in properties.iteritems():
		setattr(site,name,value)
	reactor.listenTCP(portNumber,site)
