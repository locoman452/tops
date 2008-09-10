"""
Manages the message formats used for distributed logging

A record combines a session header and a message resulting from a
client-server interaction.
"""

## @package tops.core.network.logging.record
# Manages the message formats used for distributed logging
#
# @author David Kirkby, dkirkby@uci.edu
# @date Created 10-Aug-2008
#
# This project is hosted at http://tops.googlecode.com/

from time import time
from datetime import datetime
import logging

from tops.core.network.naming import ResourceNamePattern,NamingException

class LogRecord(object):
	"""
	The record generated from a single log message.
	"""
	def __init__(self,msg,hdr):
		self.timestamp = time()
		self.when = datetime.fromtimestamp(self.timestamp)
		# we assume that these are valid names
		self.source = hdr.name + '.' + msg.source if msg.source else hdr.name
		self.msg = msg
		self.hdr = hdr
		self.cached_json = None

	def json(self):
		if self.cached_json:
			return self.cached_json
		msg = self.msg
		if msg.HasField('context'):
			context = msg.context
			json_context = ('{"file":"%s","line":%d,"func":"%s"}' %
				(context.filename,context.lineno,context.funcname))
		else:
			json_context = 'null'
		json_exception = '"%s"' % msg.exception if msg.exception else 'null'
		# See http://www.json.org/ for string escaping rules
		escaped_body = (msg.body
			.replace('\\', r'\\')
			.replace('"', r'\"')
			.replace('\b', r'\b')
			.replace('\f', r'\f')
			.replace('\n', r'\n')
			.replace('\r', r'\r')
			.replace('\t', r'\t'))
		print ">>%s<<" % escaped_body
		self.cached_json = (
			'{"tstamp":%d,"level":"%s","source":"%s","body":"%s"}' %
			(int(1000*self.timestamp),logging.getLevelName(msg.levelno).replace(' ','_'),
			self.source,escaped_body)
		)
		return self.cached_json

	def __str__(self):
		return '[%02d] %s (%s) %s' % (self.msg.levelno,self.when,self.source,self.msg.body)

class LogFilter(object):
	"""
	Filters a log record.
	"""
	def __init__(self,sourceFilter='*',minLevel='WARNING'):
		self.last = 0
		try:
			self.sourcePattern = ResourceNamePattern(sourceFilter)
		except NamingException:
			# quietly accept everything if we are passed an invalid pattern
			self.sourcePattern = ResourceNamePattern()
		try:
			self.minLevel = logging.__dict__[minLevel]
		except KeyError:
			# quietly accept everything if we are passed an invalid level name
			self.minLevel = logging.NOTSET

	def selects(self,record):
		selected = (
			(record.timestamp > self.last) and
			(record.msg.levelno >= self.minLevel) and
			(self.sourcePattern.matches(record.source))
		)
		if record.timestamp > self.last:
			self.last = record.timestamp
		return selected