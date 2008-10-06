"""
Utilities related to network resource names

Defines the allowed format of a network resource name and provides
a pattern-matching utility class.
"""

## @package tops.core.network.naming
# Utilities related to network resource names
#
# @author David Kirkby, dkirkby@uci.edu
# @date Created 10-Sep-2008
#
# This project is hosted at sdss3.org and tops.googlecode.com

import re

class NamingException(Exception):
	pass

class ResourceName(str):
	"""
	Represents a valid network resource name.
	
	A valid name consists of one or more elements separated by '.' where
	each element uses only the characters A-Z and a-z. For example,
	'aaa.bbb.ccc' or 'aaa'. A valid name cannot begin or end with '.'
	Names are case-sensitive.
	"""
	element = '[A-Za-z]+'
	separator = '.'
	validPath = re.compile(r"%s(\%s%s)*" % (element,separator,element))

	def __new__(cls,name):
		valid = cls.validPath.match(name)
		if not valid or valid.end() < len(name):
			raise NamingException('Illegal resource name: "%s"' % name)
		return str.__new__(cls,name)


class ResourceNamePattern(str):
	"""
	Represents a pattern for matching resource names.
	
	A valid pattern looks like a valid source name but with zero or more
	elements entirely replaced with the wildcard '*'. For example,
	'aaa', 'aaa.*.ccc', or '*.bbb.*'. A wildcard represents any valid
	source name so that 'aaa.*' matches 'aaa.bbb' and 'aaa.bbb.ccc' but
	not 'aaa'. Multiple patterns can be combined with a logical OR using
	a comma-separated list. For example, 'aaa.*.ccc,xxx'.
	"""
	wildcard = '*'
	separator = ','
	element = r"(\%s|%s)" % (wildcard,ResourceName.element)
	validPattern = re.compile(r"%s(\%s%s)*" % (element,ResourceName.separator,element))

	def __new__(cls,patternlist=wildcard):
		"""
		The default pattern matches all valid source names.
		"""
		return str.__new__(cls,patternlist)

	def __init__(self,patternlist=wildcard):
		"""
		The default pattern matches all valid source names.
		"""
		self.patterns = []
		for pattern in patternlist.split(self.separator):
			valid = self.validPattern.match(pattern)
			if not valid or valid.end() < len(pattern):
				raise NamingException('Illegal resource pattern: "%s"' % pattern)
			self.patterns.append(pattern
				.replace(ResourceName.separator,r"\%s" % ResourceName.separator)
				.replace(self.wildcard,ResourceName.validPath.pattern))
		self.pattern = re.compile('(%s)' % ')|('.join(self.patterns))

	def matches(self,name):
		"""
		Returns True if name matches our pattern, otherwise False.
		
		Name can either be a ResourceName or a simple string type.
		"""
		match = self.pattern.match(name)
		return match is not None and match.end() == len(name)
		

import unittest

class NamingTests(unittest.TestCase):
	def test00(self):
		"""Construct valid resource names"""
		ResourceName("aaa")
		ResourceName("Aaa.bBb")
		ResourceName("AAA.BBB.CCC")
	def test01(self):
		"""Construct invalid resource names"""
		self.assertRaises(NamingException,lambda: ResourceName("123"))
		self.assertRaises(NamingException,lambda: ResourceName("a_b"))
		self.assertRaises(NamingException,lambda: ResourceName("."))
		self.assertRaises(NamingException,lambda: ResourceName("aaa."))
		self.assertRaises(NamingException,lambda: ResourceName(".aaa"))
		self.assertRaises(NamingException,lambda: ResourceName("aaa.bbb."))
		self.assertRaises(NamingException,lambda: ResourceName(".aaa.bbb"))
		self.assertRaises(NamingException,lambda: ResourceName("aaa..bbb"))
	def test02(self):
		"""Construct valid resource name patterns"""
		ResourceNamePattern("aaa")
		ResourceNamePattern("aaa.bbb")
		ResourceNamePattern("*")
		ResourceNamePattern("*.*") # this one is redundant but legal
		ResourceNamePattern("*.*.*") # this one is redundant but legal
		ResourceNamePattern("aaa.*")
		ResourceNamePattern("*.bbb")
		ResourceNamePattern("aaa.*.ccc")
		ResourceNamePattern("*.bbb.*")
		ResourceNamePattern("aaa.*.ccc,*.bbb.*,xyz.*")
	def test03(self):
		"""Run successful resource name pattern matches"""
		pat = ResourceNamePattern("aaa.*.ccc,*.bbb.*,xyz.*")
		self.assertEqual(pat.matches("aaa.bbb.ccc"),True)
		self.assertEqual(pat.matches("aaa.bbb.xxx.ccc"),True)
		self.assertEqual(pat.matches("aaa.xxx.bbb.ccc"),True)
		self.assertEqual(pat.matches("aaa.aaa.ccc"),True)
		self.assertEqual(pat.matches("aaa.ccc.ccc"),True)
		self.assertEqual(pat.matches("xxx.bbb.xxx"),True)
		self.assertEqual(pat.matches("bbb.bbb.xxx"),True)
		self.assertEqual(pat.matches("xxx.bbb.bbb"),True)
		self.assertEqual(pat.matches("bbb.bbb.bbb"),True)
		self.assertEqual(pat.matches("xxx.yyy.bbb.xxx"),True)
		self.assertEqual(pat.matches("xxx.bbb.yyy.xxx"),True)
		self.assertEqual(pat.matches("xyz.aaa"),True)
		self.assertEqual(pat.matches("xyz.aaa.bbb"),True)
		self.assertEqual(pat.matches("xyz.aaa.ccc"),True)
		self.assertEqual(pat.matches("xyz.xyz"),True)
		self.assertEqual(pat.matches("xyz.xyz.xyz"),True)
	def test04(self):
		"""Run unsuccessful resource name pattern matches"""
		pat = ResourceNamePattern("aaa.*.ccc,*.bbb.*,xyz.*")
		self.assertEqual(pat.matches("aaa"),False)
		self.assertEqual(pat.matches("bbb"),False)
		self.assertEqual(pat.matches("ccc"),False)
		self.assertEqual(pat.matches("aaa.ccc"),False)
		self.assertEqual(pat.matches("aaa.bbb"),False)
		self.assertEqual(pat.matches("bbb.ccc"),False)
		self.assertEqual(pat.matches("xyz"),False)
		self.assertEqual(pat.matches("aaa.xyz"),False)
		self.assertEqual(pat.matches("xyz"),False)

if __name__ == '__main__':
	unittest.main()