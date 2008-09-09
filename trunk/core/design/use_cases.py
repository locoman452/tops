"""
Classes to model a design through uses cases

Supports the description of the uses cases for an object-oriented
design via python declarations.

TODO:
 - implement HTML output using utility.html
 - implement some unit tests
"""

## @package tops.core.design.use_cases
# Classes to model a design through uses cases
#
# @author David Kirkby, dkirkby@uci.edu
# @date Created 26-Jun-2008
#
# This project is hosted at http://tops.googlecode.com/

import time

class UseCasesError(Exception):
	pass

class Task:
	pass
	
class Narrative(Task):
	def __init__(self,text):
		self.text = ''
		for line in text.splitlines():
			line = line.strip()
			if len(line) > 0:
				if len(self.text) > 0:
					self.text += '\n'
				self.text += line
	def __repr__(self):
		return '"%s"' % self.text

class Reference(Task):
	UNKNOWN_COUNT = -1
	(NORMAL_FLOW,ALTERNATE_FLOW) = range(2)
	def __init__(self,scenarioName,count,flow):
		self.scenarioName = scenarioName
		self.count = count
		self.flow = flow
		self.scenario = None
	def __repr__(self):
		s = '--> "%s"' % self.scenarioName
		if not self.count == 1:
			s += ' repeated'
			if self.count > 1:
				s += ' %d times' % self.count
		if self.flow == Reference.ALTERNATE_FLOW:
			s += ' [ALTERNATE FLOW]'
		return s

def Do(scenarioName):
	return Reference(scenarioName,count=1,flow=Reference.NORMAL_FLOW)

def Alternate(scenarioName):
	return Reference(scenarioName,count=1,flow=Reference.ALTERNATE_FLOW)

def Repeat(scenarioName,count=Reference.UNKNOWN_COUNT):
	return Reference(scenarioName,count=count,flow=Reference.NORMAL_FLOW)

class Scenario:
	def __init__(self,name,*tasks):
		self.name = name
		self.tag = name.replace(' ','_')
		self.tasks = []
		for task in tasks:
			if isinstance(task,str):
				# wrap a string as a Narrative task
				self.tasks.append(Narrative(task))
			elif not isinstance(task,Task):
				raise UseCasesError('Found a %s where a Task was expected' %
					task.__class__.__name__)
			else:
				self.tasks.append(task)
	def validate(self,dictionary):
		for task in self.tasks:
			if not isinstance(task,Reference):
				continue
			if not task.scenarioName in dictionary:
				raise UseCasesError('Task references unknown scenario "%s"' % task.scenarioName)
			task.scenario = dictionary[task.scenarioName]
	def __repr__(self):
		s = '<Scenario "%s">\n' % self.name
		for task in self.tasks:
			s += '    %s\n' % task
		return s

class UseCases:
	def __init__(self,name,*scenarios):
		self.name = name
		self.scenarios = scenarios
		self.validate()
	def validate(self):
		# first pass to build a dictionary of scenarios
		self.dictionary = { }
		for scenario in self.scenarios:
			if not scenario.__class__ is Scenario:
				raise UseCasesError('Found a %s where a Scenario was expected' %
					scenario.__class__.__name__)
			self.dictionary[scenario.name] = scenario
		# second pass to resolve scenario references by name
		for scenario in self.scenarios:
			scenario.validate(self.dictionary)
	def __repr__(self):
		s = "<Use Cases for %s>\n" % self.name
		for scenario in self.scenarios:
			s += '  %s' % scenario
		return s
	def exportHTML(self,filename,title,model=None,glossaryURL='glossary.html',stylesheet=None):
		# write an html file containing our glossary
		file = open(filename,'w')
		print >> file, '''
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
  "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
  <title>%s</title>
  <meta name="description" content="Automatically generated on %s" />''' % (title,time.ctime())
		if not stylesheet is None:
			print >> file, '  <link rel="stylesheet" type="text/css" href="%s" />' % stylesheet
		print >> file, '</head>\n<body>'
		print >> file, '<div class="title">%s</div>' % title
		for scenario in self.scenarios:
			print >> file, '<div class="scenario">'
			print >> file, '<a name="%s">' % scenario.tag
			print >> file, '<div class="scenarioname">%s</div></a>' % scenario.name
			print >> file, '<ul>'
			for task in scenario.tasks:
				if isinstance(task,Narrative):
					if model is None:
						text = task.text
					else:
						text = model.embedLinks(task.text,baseURL=glossaryURL)
					print >> file, '<li class="narrative">%s</li>' % text
				elif isinstance(task,Reference):
					if task.flow == Reference.ALTERNATE_FLOW:
						className = 'alternate'
					else:
						className = 'reference'
					print >> file, ('<li class="%s"><a href="#%s">%s</a>' % 
						(className,task.scenario.tag,task.scenarioName))
					if not task.count == 1:
						print >> file, '<span class="count">REPEAT'
						if task.count > 1:
							print >> file, ' %dX' % task.count
						print >> file, '</span>'
					print >> file, '</li>'
				else:
					print >> file, '<li>Unknown Task Type</li>'
			print >> file, '</div>'
		print >> file, '</body>'
		file.close()


import unittest

class UseCasesTests(unittest.TestCase):
	def setUp(self):
		pass

if __name__ == '__main__':
	unittest.main()