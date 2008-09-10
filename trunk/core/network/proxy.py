"""
Base class for a device proxy in the Telesope Operations Software

A proxy is a python program that adapts a particular device in the
operations platform to the uniform applications environment and
interfaces it to the logging and archiving services. Proxies are project
specific and should be described by classes that inherit from this one.
"""

## @package tops.core.network.proxy
# Base class for a device proxy in the Telesope Operations Software
#
# @author David Kirkby, dkirkby@uci.edu
# @date Created 18-Aug-2008
#
# This project is hosted at http://tops.googlecode.com/

import sys

from tops.core.utility.state_chart import *

import tops.core.utility.data as data

import twisted.internet

try:
	import tops.core.network.logging.producer as logging
except Exception,e:
	print 'Unable to load logging service:',e
	sys.exit(-1)

try:
	import tops.core.network.archiving.producer as archiving
except Exception,e:
	print 'Unable to load archiving service:',e
	sys.exit(-2)


class Monitor(object):
	def __init__(self,name,*fields):
		self.name = name
		self.fields = fields


class ProxyState(State):
	def processItem(self,item):
		if isinstance(item,Monitor):
			archiving.addMonitor(item.name,item.fields)
		else:
			State.processItem(self,item)


class Proxy(StateChart):
	
	def __init__(self,description,*states):
		StateChart.__init__(self,description,*states)
		self.state = None
		
	def getState(self):
		return self.state.name if self.state else None
	
	def do(self,action):
		allowed = self.getActions(self.state)
		if action not in allowed:
			logging.warning('Ignoring illegal action %s from %s',action,self.state.name)
		else:
			self.state = self.setState(allowed[action])
			logging.debug('Entering state %s following %s',self.state.name,action)
	
	def start(self):
		source_name = self.name.lower().replace('_','.')
		logging.start(source_name)
		logging.info('Starting proxy')
		# add a monitor for our state transitions
		#archiving.addMonitor('state',[('value',data.unsigned)])
		archiving.start(source_name)
		try:
			sys.modules['__main__'].configure()
		except AttributeError:
			logging.debug('Proxy does not perform any startup configuration')
		self.state = self.setState(self)
		logging.debug('Started in state "%s"',self.state.name)
		twisted.internet.reactor.run()
		
def initialize():
	archiving.intialize()
