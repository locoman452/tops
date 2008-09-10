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
import re

class LogException(Exception):
	pass

class LogSourceName(object):
	"""
	Represents a valid logging source name.
	
	A valid name consists of one or more elements separated by '.' where
	each element uses only the characters A-Z and a-z. For example,
	'aaa.bbb.ccc' or 'aaa'. A valid name cannot begin or end with '.'
	"""
	element = '[A-Za-z]+'
	separator = '.'
	validPath = re.compile(r"%s(\%s%s)*" % (element,separator,element))

	def __init__(self,name):
		self.name = name
		valid = self.validPath.match(self.name)
		if not valid or valid.end() < len(self.name):
			raise LogException('Illegal source name: "%s"' % self.name)

	def __str__(self):
		return str(self.name)
		

class LogSourcePattern(object):
	"""
	Represents a valid logging source name pattern list.
	
	A valid pattern list consists of one or more patterns separated by
	',' where each pattern looks like a valid source name but with zero
	or more elements entirely replaced with the wildcard '*'. For
	example, 'aaa.*.ccc,aaa' or '*.bbb.*'. A wildcard represents any
	valid source name so that 'aaa.*' matches 'aaa.bbb' and
	'aaa.bbb.ccc' but not 'aaa'.
	"""
	wildcard = '*'
	separator = ','
	element = r"(\%s|%s)" % (wildcard,LogSourceName.element)
	validPattern = re.compile(r"%s(\%s%s)*" % (element,LogSourceName.separator,element))

	def __init__(self,name=wildcard):
		"""
		The default pattern matches all valid source names.
		"""
		self.name = name
		self.patterns = []
		for pattern in name.split(self.separator):
			valid = self.validPattern.match(pattern)
			if not valid or valid.end() < len(pattern):
				raise LogException('Illegal source pattern: "%s"' % pattern)
			self.patterns.append(pattern
				.replace(LogSourceName.separator,r"\%s" % LogSourceName.separator)
				.replace(self.wildcard,LogSourceName.validPath.pattern))
		self.pattern = re.compile('(%s)' % ')|('.join(self.patterns))

	def __str__(self):
		return str(self.name)

	def matches(self,name):
		match = self.pattern.match(name)
		return match is not None and match.end() == len(name)


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
			self.sourcePattern = LogSourcePattern(sourceFilter)
		except LogException:
			# quietly accept everything if we are passed an invalid pattern
			self.sourcePattern = LogSourcePattern()
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