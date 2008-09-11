"""
Declare and execute state charts

A state chart is a generalization of a finite state machine designed for
the efficient declaration of complex behaviors with support for
hierachical states and history states. The original reference and a good
starting point for details is:

  "Statecharts: A Visual Formalism for Complex Systems", David Harel,
  Science of Computer Programming 8 (1987) 231-274.
"""

## @package tops.core.utility.state_chart
# Declare and execute state charts
#
# @author David Kirkby, dkirkby@uci.edu
# @date Created 4-Jul-2008
#
# This project is hosted at http://tops.googlecode.com/

import re
import time

from name_graph import *
from html import *

class StateChartException(Exception):
	"""Base class for state chart exceptions."""
	pass

class On(node):
	"""
	Describes an allowed state transition
	"""
	def __init__(self, action):
		self.action = action
	def goto(self,target):
		self.target = target
		return self

class History(node):
	"""
	Represents the history of a state.
	"""
	def __init__(self,state):
		self.name = 'recall(%s)' % state.name
		self.enter = state.recall

class State(node):
	"""
	Represents a well defined state of a system.
	"""
	scanner = re.compile('^\s*([A-Z_]+)\s*(?:->\s*([A-Z_]+)\s*)?$')
	def __init__(self,description,*items):
		"""
		Creates a new state of a system.
		
		A new state of a system is specified by a text description
		followed by an optional item list that includes any substates or
		trigger conditions.
		
		The description consists of a unique state name optionally
		followed by the name of this state's initial substate. State
		names must be all uppercase and use underscores (_) instead of
		spaces for word separators. White space around names is ignored.
		Examples of valid descriptions are '...'
		
		The description can be optionally followed by a list of
		substates (if this is a compound state) and/or trigger
		conditions. Substates can be declared in place, providing a
		hierarchical declaration of an entire state chart. Substates and
		triggers can be mixed freely.
		
		An optional string immediately following the description will be
		interpreted as documentation of this state.
		"""
		# parse the description
		matches = re.match(self.scanner,description)
		if matches is None:
			raise StateChartException('badly formatted state description "%s"' % description)
		(self.name,self.initial) = matches.groups()
		if not self.initial is None:
			self.initial = refByName(self.initial)
		# separate out the substates and triggers
		self.substates = []
		self.triggers = {}
		self.__doc__ = None
		for item in items:
			self.processItem(item)
		# check that we have an initial substate specified if we have any substates
		if len(self.substates) > 0:
			if self.initial is None:
				# should this be required? perhaps a better execution model to is defer this
				# as a runtime exception in enter()...
				raise StateChartException(
					'compound state "%s" requires an initial substate' % self.name)
			elif not self.initial in [s.name for s in self.substates]:
				raise StateChartException(
					'"%s" is not a valid initial state for "%s"' % (self.initial,self.name))
		# initialize our history (which will be updated by our immediate substates, if any)
		self.last = None
		# create a pseudo-state for our history
		self.history = History(self)
	def processItem(self,item):
		if isinstance(item,basestring):
			if not self.__doc__:
				self.__doc__ = ''
			self.__doc__ += item
		elif isinstance(item,State):
			self.substates.append(item)
		elif isinstance(item,On):
			self.triggers[item.action] = refByName(item.target)
		else:
			raise StateChartException('unrecognized state parameter: %s' % type(item))
	def recall(self):
		"""
		Returns the state reached by recalling our most recent state.
		
		In this state has substates, then recursively restore the most recent
		one entered. Otherwise, restore ourself. Raises an exception if
		no history has been recorded yet for this state.
		"""
		if len(self.substates) > 0:
			if self.last is None:
				raise StateChartException('no history saved for state "%s"' % self.name)
			return self.last.recall()
		else:
			return self
	def enter(self):
		"""
		Returns the state reached by entering this state.
		
		If this state has substates, then recusively enters its
		predefined initial substate. Returns the state that is
		ultimately reached. Updates the history of its parent state to
		support 'recall(STATE)' pseudo states.
		"""
		if len(self.substates) > 0:
			if self.initial is None:
				raise StateChartException('no initial substate specified for state "%s"' % self.name)
			return self.initial.enter()
		else:
			return self
	def exportHTML(self,container):
		decorator = Span(className='decorator')
		if not self._node__parent is None and self._node__parent.initial is self:
			decorator.append(Entity('raquo'))
		else:
			decorator.append(' ')
		content = Div(
			Div(decorator,self.name,className='title'),
			className='state',id=self.name
		)
		if not self.__doc__ is None:
			content.append(Div(self.__doc__,className='doc'))			
		triggers = Div(className='triggers')
		for (trigger,target) in self.triggers.iteritems():
			triggers.append(
				Span(
					trigger,Entity('nbsp'),Entity('rArr'),Entity('nbsp'),target.name,
					className='trigger',target=target.name
				)
			)
			triggers.append(Br())
		content.append(triggers)
		for substate in self.substates:
			substate.exportHTML(content)
		container.append(content)
	def exportGraphNodes(self,doc,indent='  '):
		if len(self.substates) > 0:
			doc += '%ssubgraph cluster%s {\n' % (indent,self.name)
			doc += '%s  label="%s";\n' % (indent,self.name)
			if not self.initial is None:
				doc += '%s  %s [label="I",shape=hexagon];\n' % (indent,self.name)
			doc += '%s  recall%s [label="H",shape=hexagon];\n' % (indent,self.name)
			doc += '%s  anchor%s [style=invis,height=0,width=0,fontsize=0]' % (indent,self.name)
			for substate in self.substates:
				doc = substate.exportGraphNodes(doc,indent+'  ')
			doc += '%s}\n' % indent
		else:
			doc += '%s%s\n' % (indent,self.name)
		return doc
	def exportGraphEdges(self,doc):
		def mangle(name):
			if name.startswith('recall('):
				return 'recall'+name[7:-1]
			else:
				return name
		if len(self.substates) > 0:
			if not self.initial is None:
				doc += '%s -> %s;\n' % (self.name,mangle(self.initial.name))
			for substate in self.substates:
				doc = substate.exportGraphEdges(doc)
			for (trigger,target) in self.triggers.iteritems():
				doc += ('anchor%s -> %s [ltail="cluster%s",label="%s"];\n'
					% (self.name,mangle(target.name),self.name,trigger))
		else:
			for (trigger,target) in self.triggers.iteritems():
				doc += '%s -> %s [label="%s"];\n' % (self.name,mangle(target.name),trigger)
		return doc

class StateChart(State):
	"""
	Represents a complete set of states describing a system's behavior.
	"""
	def __init__(self,description,*states):
		State.__init__(self,description,*states)
		self.namespace = createGraph(self)
	def getActions(self,state):
		"""
		Returns a dictionary of the actions allowed from the specified state.
		"""
		actions = state.triggers.copy()
		iter = state
		while not iter._node__parent is None:
			iter = iter._node__parent
			actions.update(iter.triggers)
		return actions
	def setState(self,state):
		"""
		Enters a specified state and returns the new state finally reached.
		"""
		# check for a valid name
		if not state.name in self.namespace:
			raise StateChartException('no such state named "%s"' % name)
		# check that this is the correct object registered to this name
		if not state is self.namespace[state.name]:
			raise StateChartException('state does not match registered state "%s"' % state.name)
		# enter this state
		newstate = state.enter()
		# update our history
		iter = newstate
		while not iter._node__parent is None:
			iter._node__parent.last = iter
			iter = iter._node__parent
		return newstate
	def exportHTML(self,filename,title=None,diagram=None):
		"""
		Export chart as an interactive HTML document
		"""
		doc = HTMLDocument(
			Head(title=title,css='statechart.css',js='statechart.js'),
			Body(onload="State.initialize(states[0].name)")
		)
		# prepare a flat javascript declaration of all states
		js = 'states = ['
		nstates = 0
		for (name,state) in self.namespace.iteritems():
			if not isinstance(state,State):
				continue
			args = 'name:"%s"' % name
			if len(state.substates) > 0:
				args += ',compound:true'
			else:
				args += ',compound:false'
			if not state.initial is None:
				args += ',initial:"%s"' % state.initial.name
			if not state._node__parent is None:
				args += ',parent:"%s"' % state._node__parent.name
			js += '%s  new State({%s})' % (nstates > 0 and ',\n' or '\n',args)
			nstates += 1
		js += '\n]\n'
		doc.head.js.append(js)
		# Add the state diagram if one was provided
		if not diagram is None:
			doc.body.append(Div(Img(src=diagram),id='diagram'))
		# Recursively export each state node
		states = Div(id='states')
		State.exportHTML(self,states)
		doc.body.append(states)
		# Write the file
		file = open(filename,'w')
		print >> file,doc
		file.close()
	def exportGraph(self,filename):
		"""
		Export chart as a Graphviz graph
		"""
		doc = '// Statechart automatically generated on %s\n' % time.ctime()
		doc += 'digraph statechart {\n'
		doc += '  compound=true;\n'
		doc += '  remincross=true;\n'
		doc += '  size="5,50";\n'
		doc += '  bgcolor="#FFFFFF00";'
		doc = State.exportGraphNodes(self,doc)
		doc = State.exportGraphEdges(self,doc)
		doc += '}'
		# Write the file
		file = open(filename,'w')
		print >> file,doc
		file.close()


class StateTrooper(object):
	"""
	Implement the behavior specified by a state chart.
	"""
	def __init__(self,chart):
		self.chart = chart
		self.reset()
	def reset(self):
		self.state = self.chart.setState(self.chart)
	def run(self):
		try:
			while True:
				print 'Current State: %s' % self.state.name
				actions = self.chart.getActions(self.state)
				choices = actions.keys()
				nchoices = len(choices)
				for index in xrange(len(choices)):
					choice = choices[index]
					target = actions[choice]
					print '  [%d] %s -> %s' % (index+1,choice,target.name)
				index = 0
				while index < 1 or index > nchoices:
					try:
						index = int(raw_input('select an action 1-%d or ^C to quit: ' % nchoices))
					except ValueError:
						print 'invalid selection'
				self.state = self.chart.setState(actions[choices[index-1]])
		except KeyboardInterrupt:
			print '\nbye'


import unittest

class StateChartTests(unittest.TestCase):
	def test00(self):
		"""Declare an empty state chart"""
		states = StateChart("TEST_CHART")
	def test01(self):
		"""Declare an empty state chart with a missing initial state"""
		self.assertRaises(UnresolvedReference,
			lambda: StateChart("TEST_CHART -> INITIAL_STATE")
		)
	def test02(self):
		"""Hiearchical state chart declaration and execution"""
		states = StateChart("TEST_CHART -> ON",
			State('ON -> IDLE',
				"""
				Device is turned ON
				""",
				On('turn off').goto('OFF'),
				On('fault').goto('ERROR'),
				State('IDLE',
					"""
					Device is waiting for input
					""",
					On('run').goto('BUSY')
				),
				State('BUSY',
					"""
					Device is busy
					""",
					On('done').goto('IDLE')
				)
			),
			State('ERROR',
				"""
				Device encountered an error condition
				""",
				On('resume').goto('recall(ON)')
			),
			State('OFF',
				"""
				Device is turned OFF
				""",
				On('turn on').goto('ON')
			)
		)
		idle = states.setState(states)
		self.assertEqual(idle.name,'IDLE')
		self.assertEqual(states.getActions(idle).keys(),{'turn off':0,'run':0,'fault':0}.keys())
		busy = states.setState(states.getActions(idle)['run'])
		self.assertEqual(busy.name,'BUSY')
		self.assertEqual(states.getActions(busy).keys(),{'turn off':0,'done':0,'fault':0}.keys())
		error = states.setState(states.getActions(busy)['fault'])
		self.assertEqual(error.name,'ERROR')
		self.assertEqual(states.getActions(error).keys(),{'resume':0}.keys())
		resumed = states.setState(states.getActions(error)['resume'])
		self.assertEqual(resumed.name,'BUSY')
	
if __name__ == '__main__':
	unittest.main()