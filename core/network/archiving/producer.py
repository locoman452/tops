"""
Implements the producer client side of distributed archiving

By importing this module, a producer has access to global methods to
register itself with the archiving server (initialize,start) and define
the records it exports (addMonitor) and then trigger updates to be sent
across the network to the archiving server (update). Some global methods
will produce logging messages. If the logging producer has already been
started by someone else (this module does not start the logging
producer), these will be sent to the logging server. Otherwise, they
will be handled by python's built-in logging module.

The archiving module uses the tops.core.utility.config module to obtain
its network connection parameters so config.initialize() must be called
somewhere in the main program before this module's initialize() method.
"""

## @package tops.core.network.archiving.producer
# Implements the producer client side of distributed archiving
#
# @author David Kirkby, dkirkby@uci.edu
# @date Created 24-Aug-2008
#
# This project is hosted at http://tops.googlecode.com/

import tops.core.network.logging.producer as logging

from tops.core.network.client import Client,ClientException
from record import ArchiveRecord

from tops.core.network.naming import ResourceName

from time import time
from math import floor
from tops.core.utility.astro_time import AstroTime,UTC

import archiving_pb2

class ArchiveClient(Client):
	
	Header = archiving_pb2.Header
	Message = archiving_pb2.Update

	def __init__(self,unix_path,tcp_host,tcp_port):
		Client.__init__(self,unix_path,tcp_host,tcp_port)
		self.records = { }
		self.started = False
		
	def addMonitor(self,name,channels):
		self.records[name] = ArchiveRecord(name,channels)

	def start(self,name):
		hdr = self.Header()
		hdr.name = ResourceName(name)
		# set our timestamp origin
		hdr.timestamp_origin = int(floor(time()))
		self.timestamp_origin = AstroTime.fromtimestamp(hdr.timestamp_origin,UTC)
		# describe each record that we will provide updates for
		for record in self.records.itervalues():
			record.appendToHeader(hdr)
			self.sendHeader(hdr)
		self.started = True
			
	def sendUpdate(self,timestamp,record_name,channels):
		elapsed = timestamp - self.timestamp_origin
		msg = self.records[record_name].getUpdate(elapsed,channels)
		self.sendMessage(msg)
		

theArchive = None

import tops.core.utility.config as config

def initialize():
	"""
	Initializes the producer side of distributed archiving.
	
	Should usually be called right after importing this module. Must be
	called before archiving is started or any records are defined. This
	function attempts to connect to the archiving server and will
	raise an exception if this fails.
	"""
	global theArchive
	assert(theArchive is None)
	theArchive = ArchiveClient(
		config.get('archiver','unix_addr'),
		config.get('archiver','tcp_host'),
		config.get('archiver','tcp_port')
	)

def addMonitor(name,channels):
	"""
	Adds a monitor for a new record to this producer.
	
	The producer must be initialized before monitors can be added. No
	monitors can be added after the producer has been started. This
	function does not generate any network traffic itself but, instead,
	queues up the data that will be sent when the producer is started.
	"""
	global theArchive
	assert(theArchive is not None)
	assert(not theArchive.started)
	logging.info('Adding monitor for "%s"',name)
	theArchive.addMonitor(name,channels)

def start(name):
	"""
	Starts an archiving producer registered under the specified name.
	
	All records must be defined via addMonitor() calls before starting
	the producer. Updates cannot be send, via update(), until the
	producer has been started.
	"""
	global theArchive
	assert(theArchive is not None)
	assert(not theArchive.started)
	logging.info('Starting archive client')
	theArchive.start(name)

def update(utc_timestamp,record_name,channels):
	"""
	Sends a timestamped update for the named record.
	
	The record must have been defined via an addMonitor() call before
	this producer was started. The timestamp is a posix timestamp, i.e.,
	seconds since 00:00 1 Jan 1970 UTC.
	
	Note that channels are specified by keyword. This is probaby less
	efficient than a list of channels, but makes the producer code much
	easier to read.
	"""
	global theArchive
	assert(theArchive is not None)
	assert(theArchive.started)
	theArchive.sendUpdate(utc_timestamp,record_name,channels)