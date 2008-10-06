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
# This project is hosted at sdss3.org and tops.googlecode.com

import sys

from tops.core.utility.state_chart import *

import tops.core.utility.data as data
import tops.core.utility.config as config
import tops.core.network.logging.producer as logging
import tops.core.network.archiving.producer as archiving

import twisted.internet


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
			logging.debug('Action "%s" enters the state %s',action,self.state.name)
	
	def start(self):
		# Our service name should already have been set in the global initialize() function.
		assert(self.service_name is not None)
		# Let the world know we are starting
		logging.info('Starting proxy as %s' % self.service_name)
		# TODO: add a monitor for our state transitions
		#archiving.addMonitor('state',[('value',data.unsigned)])
		# Tell the archiver about the data we provide
		archiving.start()
		# Perform any optional startup configuration
		try:
			sys.modules['__main__'].configure()
		except AttributeError:
			logging.debug('Proxy does not perform any startup configuration')
		# Initialize our state machine
		self.state = self.setState(self)
		logging.info('Started in state %s',self.state.name)
		# Start the main loop (this call never returns)
		twisted.internet.reactor.run()
		
def initialize(name):
	"""
	Initializes the proxy environment before a new proxy is declared.
	
	The name provided must be a valid and unique network service name.
	See tops.core.network.naming for details.
	"""
	# check the name format (does not check uniqueness)
	from tops.core.network.naming import ResourceName
	name = ResourceName(name)
	# remember our service name
	Proxy.service_name = name
	# initialize our run-time configuration
	config.initialize()
	# initialize the logger
	logging.initialize(name)
	# initialize the archiver
	archiving.initialize(name)
