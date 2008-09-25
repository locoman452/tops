"""
Supports queueing and execution of asynchronous commands

Implements a FIFO command queue to support an execution model driven by
two types of asynchronous external event: command submission, and data
being received. Access to the command processor is assumed to be through
a read/write device, where writing some command payload will trigger the
command to start executing and the command completion (whether
successful or not) can be detected by inspection of the subsequent data
received. A completed command triggers any callbacks associated with a
twisted Deferred object.

The current implementation of this module is not thread safe.
"""

## @package tops.core.network.command
# Supports queueing and execution of asynchronous commands
#
# @author David Kirkby, dkirkby@uci.edu
# @date Created 16-Sep-2008
#
# This project is hosted at http://tops.googlecode.com/

from collections import deque
from twisted.internet.defer import Deferred

class CommandException(Exception):
	pass

class CommandQueue(object):
	"""
	Serializes access to an asynchronous command processor.
	
	Commands are started via an issue() call that subclasses should
	implement to transmit the command's payload to the command
	processor. By monitoring the data received from the processor after
	issuing a command, the queue owner should either call done() or
	error() to signal the command's completion. Upon successful
	completion, any callbacks associated with the Deferred object
	returned by add() will fire. Unsuccessful completion is signalled
	via the 'errback' error callback chain.
	"""
	class Command(object):
		def __init__(self,payload):
			self.payload = payload
			self.deferred = Deferred()

	def __init__(self,maxsize=None):
		"""
		Creates an empty command queue.
		
		Use the optional maximum queue size to flag queue overflow
		conditions that might signal a problem with the command
		processor.
		"""
		self.maxsize = None
		if maxsize:
			try:
				self.maxsize = int(maxsize)
			except ValueError:
				self.maxsize = None
		self.queued = deque()
		self.running = None

	def issue(self,payload):
		"""
		Issues a command by transmitting its associated payload.
		
		Subclasses should override this method to do something more useful.
		"""
		pass

	def add(self,payload):
		"""
		Queues a command for execution.
		
		The command will be issued immediately if the queue is idle.
		Otherwise, it will be added to the queue and issued in FIFO
		order. In case a maximum queue size was specified for this queue
		and has been reached, an exception will be raised.
		"""
		command = CommandQueue.Command(payload)
		if self.running:
			if self.maxsize and len(self.queued) >= self.maxsize:
				raise CommandException('CommandQueue is full with %d entries' % self.maxsize)
			self.queued.append(command)
		else:
			self.running = command
			self.issue(command.payload)
		return command.deferred
	
	def done(self,response=None):
		"""
		Signals the successful completion of the current command.
		
		Fires the defered callback chain associated with this command,
		passing any response data provided, and then notifies the host
		queue that a new command may be issued.
		"""
		if not self.running:
			raise CommandException('CommandQueue has no running command to complete')
		self.running.deferred.callback(response)
		self._next()
		
	def error(self,exception=None):
		"""
		Signals the unsuccessful completion of the command.
		
		Fires the defered error callback chain associated with this
		command and then notifies the host queue that a new command may
		be issued. This method is normally called after an exception has
		been raised, and propagates the exception into to the callback
		chain. In case no exception has been raised, one should be
		provided when calling this method.
		"""
		if not self.running:
			raise CommandException('CommandQueue has no running command to complete')
		self.running.deferred.errback(exception)
		self._next()

	def _next(self):
		"""
		Issues the next queued command, if any.
		"""
		try:
			self.running = self.queued.popleft()
			self.issue(self.running.payload)
		except IndexError:
			self.running = None


import unittest
import twisted.python.failure

class QueueTests(unittest.TestCase):
	
	args = None
	
	def done_callback(self,response,payload):
		self.args = (response,payload)
		
	def error_callback(self,failure,payload):
		try:
			failure.trap(CommandException)
			# the next line will only run if failure is a CommandException
			self.args = payload
		except twisted.python.failure.Failure:
			pass
	
	def test00(self):
		"""Queue construction"""
		q = CommandQueue()
		self.assertEqual(q.maxsize,None)
		q = CommandQueue(10)
		self.assertEqual(q.maxsize,10)
		q = CommandQueue(-10)
		self.assertEqual(q.maxsize,-10)
		q = CommandQueue(10.123)
		self.assertEqual(q.maxsize,10)
		q = CommandQueue('abc')
		self.assertEqual(q.maxsize,None)
	def test01(self):
		"""Add commands to a queue without overflow"""
		maxsize = 10
		q = CommandQueue(maxsize)
		for index in xrange(maxsize+1):
			q.add("command")
	def test02(self):
		"""Add commands to a queue with overflow"""
		maxsize = 10
		q = CommandQueue(maxsize)
		for index in xrange(maxsize+1):
			q.add("command")
		self.assertRaises(CommandException,lambda: q.add("command"))
	def test03(self):
		"""Cannot complete a command that is not running"""
		q = CommandQueue()
		self.assertRaises(CommandException,lambda: q.done())
		self.assertRaises(CommandException,lambda: q.error())
	def test04(self):
		"""Queued commands complete successfully"""
		q = CommandQueue()
		seq = range(10)
		for index in seq:
			payload = 'command %d' % index
			#d.addCallback(self.done_callback,payload)
			callback_args = (payload,)
			q.add(payload).addCallbacks(self.done_callback,self.error_callback,
				callbackArgs=callback_args,errbackArgs=callback_args)
		for index in seq:
			payload = 'command %d' % index
			response = 'ok %d' % index
			q.done(response)
			self.assertEqual(self.args,(response,payload))
	def test05(self):
		"""Queued commands complete with trapped error"""
		q = CommandQueue()
		seq = range(10)
		for index in seq:
			payload = 'command %d' % index
			self.args = None
			callback_args = (payload,)
			q.add(payload).addCallbacks(self.done_callback,self.error_callback,
				callbackArgs=callback_args,errbackArgs=callback_args)
		for index in seq:
			payload = 'command %d' % index
			q.error(CommandException())
			self.assertEqual(self.args,payload)
	def test06(self):
		"""Queued commands complete with untrapped error"""
		q = CommandQueue()
		seq = range(10)
		for index in seq:
			payload = 'command %d' % index
			self.args = None
			callback_args = (payload,)
			q.add(payload).addCallbacks(self.done_callback,self.error_callback,
				callbackArgs=callback_args,errbackArgs=callback_args)
		for index in seq:
			q.error(IndexError())
			self.assertEqual(self.args,None)
		
if __name__ == '__main__':
	unittest.main()