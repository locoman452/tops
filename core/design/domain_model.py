"""
Classes to declare the domain model of a design

Suports the description of a domain model for an object-oriented design
via python declarations.

This module should really be implemented on top of utility.name_graph,
which grew out of the ideas first developed here.
"""

## @package tops.core.design.domain_model
# Classes to declare the domain model of a design
#
# @author David Kirkby, dkirkby@uci.edu
# @date Created 24-Jun-2008
#
# This project is hosted at http://tops.googlecode.com/

import re
import time

from tops.core.utility.html import *

class DomainModelError(Exception):
	pass

class Target:
	(AUTO,ONE,MULTIPLE) = range(3)
	def __init__(self,name,number=AUTO):
		self.name = name
		self.number = number
		self.node = None
	def __repr__(self):
		if self.number == self.MULTIPLE:
			return 'multiple "%s"' % self.name
		else:
			return '"%s"' % self.name
	def validate(self):
		if not self.number in [self.AUTO,self.ONE,self.MULTIPLE]:
			raise DomainModelError('Invalid Target number for "%s"' % self.name)
		# check that we have been linked to a model object
		if self.node is None:
			raise DomainModelError('Target not associated with Domain Model')
		node = self.node
		# check that our name and number are self-consistent
		if self.number == Target.ONE:
			if not self.name == node.name:
				raise DomainModelError('"%s" is not singular (expected "%s")' %
					self.name,node.name)
		elif self.number == Target.MULTIPLE:
			if not self.name == node.plural:
				raise DomainModelError('"%s" is not plural (expected "%s")' %
					(self.name,node.plural))
		elif self.number == Target.AUTO:
			if self.name == node.name:
				self.number = Target.ONE
			else:
				self.number = Target.MULTIPLE

# Explicitly specify the number of a target for target names that have the same
# singular and plural forms (e.g., "Data")

def one(name):
	return Target(name,Target.ONE)

def multiple(name):
	return Target(name,Target.MULTIPLE)

class Relationship:
	def __init__(self,type,target):
		self.type = type
		if isinstance(target,Target):
			self.target = target
		else:
			self.target = Target(target)
	def __repr__(self):
		return '%s %s' % (self.type,self.target)

# The following functions define the valid relationship clauses.
# Each clause lists one or more targets for a particular type of relationship.

def isA(*targets):
	return [Relationship("isA",target) for target in targets]
	
def has(*targets):
	return [Relationship("has",target) for target in targets]

# Implement the most common rules for pluralizing English nouns
# (following ASPN recipe http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/82102)
def pluralize(noun):
	postfix = 's'
	if len(noun) > 2:
		vowels = 'aeiou'
		if noun[-2:] in ('ch','sh','ss'):
			postfix = 'es'
		elif noun[-1:] == 'y':
			if not noun[-2:-1] in vowels:
				noun,postfix = noun[:-1],'ies'
		elif noun[-2:] == 'is':
			noun,postfix = noun[:-2],'es'
		elif noun[-1:] in ('s', 'z', 'x'):
			postfix = 'es'
		elif noun[-1:] == 'f':
			noun,postfix = noun[:-1],'ves'
		elif noun[-2:] == 'fe':
			noun,postfix = noun[:-2],'ves'
	return noun + postfix
	
class Node:
	# Valid Node names are "A" and "A(B:C)" where A,B,C are composed of A-Z,a-z and space.
	# The second form, where any of A,B,C can be empty, specifies an explicit pluralization
	# rule for the name, i.e., singular is "AB" and plural is "AC". With the first form,
	# "A" should be singular and standard pluralization rules will be applied automaticallly.
	scanner = re.compile('^([A-Za-z ]*)(?:\(([A-Za-z ]*):([A-Za-z ]*)\))?$')
	def __init__(self,name,description,clauses):
		self.type = self.__class__.__name__
		scan = re.match(Node.scanner,name)
		if scan is None or not len(scan.groups()) == 3:
			raise DomainModelError('Badly formatted name "%s"')
		if scan.group(2) is None or scan.group(2) is None:
			# use implicit pluralization
			self.name = name
			self.plural = pluralize(name)
		else:
			self.name = scan.group(1) + scan.group(2)
			self.plural = scan.group(1) + scan.group(3)
		# replace spaces with underscore to tag this node
		self.tag = self.name.replace(' ','_')
		self.description = description
		self.relationships = []
		for clause in clauses:
			self.relationships.extend(clause)
	def __repr__(self):
		s = '<%s "%s"' % (self.type,self.name)
		for rel in self.relationships:
			s += ' %s' % rel
		s += '>'
		return s
		
class Actor(Node):
	def __init__(self,name,description,*relationships):
		Node.__init__(self,name,description,relationships)

class Noun(Node):
	def __init__(self,name,description,*relationships):
		Node.__init__(self,name,description,relationships)

class DomainModel:
	linkScanner = re.compile('\[(?:\s*([A-Za-z0-9\./:]+)\s+)*?([A-Za-z ]+)\]')
	def __init__(self,name,*nodes):
		self.name = name
		self.nodes = nodes
		self.validate()
	def __repr__(self):
		s = '<Domain Model for "%s">\n' % self.name
		for node in self.nodes:
			s += '  %s\n' % node
		return s
	def validate(self):
		# first pass to build dictionary of model objects
		self.objects = { }
		for node in self.nodes:
			self.objects[node.name.upper()] = node
			# add plural form
			if not node.plural == node.name:
				self.objects[node.plural.upper()] = node
		# second pass to check that all targets are in the dictionary and validate them
		for node in self.nodes:
			for rel in node.relationships:
				target = rel.target
				if not target.name.upper() in self.objects:
					raise DomainModelError('%s refers to non-model object "%s"' %
						(node.name,target.name))
				target.node = self.objects[target.name.upper()]
				target.validate()
	def embedLinks(self,text,baseURL=''):
		result = Div(className='embeddedLinks')
		isLink = False
		fragments = iter(re.split(DomainModel.linkScanner,text))
		for fragment in fragments:
			if isLink:
				url = fragment
				name = fragments.next()
				if url is None:
					url = baseURL + '#' + self.objects[name.upper()].tag
				result.append(A(name,href=url))
			else:
				result.append(fragment)
			isLink = not isLink
		return result
	def exportGlossary(self,filename,title='Glossary',stylesheet='glossary.css'):
		# write an html file containing our glossary
		doc = HTMLDocument(
			Head(title=title,css=stylesheet),
			Body(
				Div(
					Div(title,className='title'),
					id='glossary'
				)
			)
		)
		for name in sorted([node.name for node in self.nodes]):
			node = self.objects[name.upper()]
			doc['glossary'].append(
				Div(
					A(Div(name,className='nodename'),name=node.tag),
					id=node.tag,className='node'
				)
			)
			if len(node.relationships) > 0:
				content = Div(className='relationships')
				lastrel = node.relationships[-1]
				for rel in node.relationships:
					content.append(
						Span(rel.type,Entity('nbsp'),
							A(rel.target.name,href='#'+rel.target.node.tag),
							className='rel'
						)
					)
					if not rel is lastrel:
						content.append(', ')
				doc[node.tag].append(content)
			doc[node.tag].append(Div(self.embedLinks(node.description),className='description'))
		file = open(filename,'w')
		print >> file,doc
		file.close()
	def exportGraph(self,filename,baseURL='glossary.html'):
		# write a vizgraph directed graph representing our objects and relationships
		style = {
			'head': {
				'isA': { Target.ONE: 'normal' },
				'has': { Target.ONE: 'none', Target.MULTIPLE: 'none' }
			},
			'tail': {
				'isA': { Target.ONE: 'none' },
				'has': { Target.ONE: 'odot', Target.MULTIPLE: 'dot' }
			},
			'shape': { 'Actor': 'box', 'Noun': 'ellipse' }
		}
		file = open(filename,'w')
		print >> file, '// Domain Model for "%s"' % self.name
		print >> file, '// Automatically generated on %s' % time.ctime()
		print >> file, 'digraph model {'
		for node in self.nodes:
			print >> file, ('  %s [label="%s",shape=%s,URL="%s#%s"]' %
				(node.tag,node.name,style['shape'][node.type],baseURL,node.tag))
			for rel in node.relationships:
				print >> file, ('    %s -> %s [arrowhead=%s,arrowtail=%s]' %
					(node.tag,rel.target.node.tag,
					style['head'][rel.type][rel.target.number],
					style['tail'][rel.type][rel.target.number]))
		print >> file, '}'
		file.close()

import unittest

class DomainModelTests(unittest.TestCase):
	def test00(self):
		"""Declare domain model clauses"""
		isA("A","B","C")
		has("Driver","Wheels")
	def test01(self):
		"""Declare a domain model node"""
		Actor("Driver",isA("Person"),has("Car Keys","License"))
	def test02(self):
		"""Declare a simple model"""
		self.model = DomainModel('Test Domain Model',
			Actor('Driver',
				"""Person who drives a car""",
				isA('Person')
			),
			Actor('Passenger',
				"""Person who rides in a car""",
				isA('Person')
			),
			Actor('Person',
				"""A human being, capable of driving and being driven"""
			),
			Noun('Car',
				"""A type of vehicle""",
				has('Driver','Passengers')
			)
		)

if __name__ == '__main__':
	unittest.main()