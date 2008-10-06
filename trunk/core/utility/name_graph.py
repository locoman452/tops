"""
Lightweight object graphs for simple configuration declarations

Supports the implicit construction of object graphs with links defined
by composition (has-a relationships) and named references.
"""

## @package tops.core.utility.name_graph
# Lightweight object graphs for simple configuration declarations
#
# @author David Kirkby, dkirkby@uci.edu
# @date Created 6-Jul-2008
#
# This project is hosted at sdss3.org and tops.googlecode.com


class NameGraphException(Exception):
	def __init__(self,message,target=None):
		Exception.__init__(self, target and message % target or message)
		self.target = target

class InvalidName(NameGraphException):
	pass

class DuplicateName(NameGraphException):
	pass
	
class UnresolvedReference(NameGraphException):
	pass
	

class refByName(str):
	"""
	Declares a reference-by-name to another node within the same graph.
	
	A refByName is a string that identifies a named node within the same
	graph.
	"""
	def __new__(cls,value):
		return str.__new__(cls,value)

class alias(str):
	def __new__(cls,value):
		return str.__new__(cls,value)

class node(object):
	"""
	The base class for all graph nodes.
	
	A lightweight base class for all graph nodes that has no constructor
	or public attributes. A node is created, including references by
	name to other nodes, before it has been bound to any graph. This
	allows a convenient declarative style for specifying
	configuration-type data as nested object declarations.
	
	A node can optionally be named and then referred to by other nodes
	that end up in the same graph. A node's name is implicitly obtained
	from its self.name value when one is present, of basestring type,
	and contains more than whitespace. Names (and aliases -- see below)
	are case sensitive and can be unicode. Invalid names generate an
	exception.
	
	A node's children are defined as its instance variables (obtained
	via self.__dict__). In case any of these variables is a dictionary
	(tested via isinstance(var,dict)) or supports list-indexing
	semantics (len(var)>0 and var[index] defined), then its immediate
	contents are also children. The definition of a node's children only
	extends to one level of container and is not recursive.
	
	Any children of a node that are themselves node instances define
	graph links by composition and will be recursively attached to the
	same graph as their parent. Graph links can also be defined by
	reference wherever a refByName(...) object is declared among a
	node's children. Such references are replaced with actual object
	references when a node is eventually bound to a graph and any
	unresolved references will trigger an exception.
	
	A node can be referenced by aliases in addition to its primary name.
	Any alias(...) object declared among a node's children establishes
	an alias.
	"""
	def __register(self,namespace,name):
		if not isinstance(name,basestring):
			raise InvalidName('invalid node name type: %s',type(name))
		if not len(name.strip()) > 0:
			raise InvalidName('node name cannot be empty: %s',repr(name))
		if name in namespace:
			raise DuplicateName('cannot register duplicate name to same root: "%s"',name)
		namespace[name] = self
	def __addRef(self,base,key,target,reference):
		if target in reference:
			reference[target].append((base,key))
		else:
			reference[target] = [ (base,key) ]
	def __addChild(self,child,namespace,reference):
		child.__parent = self
		child.__bind(namespace,reference)
	def __processItems(self,base,iterable,namespace,reference):
		for key in iterable:
			item = base[key]
			if isinstance(item,node):
				self.__addChild(item,namespace,reference)
			elif isinstance(item,refByName):
				self.__addRef(base,key,item,reference)
			elif isinstance(item,alias):
				self.__register(namespace,item)
	def __bind(self,namespace,reference):
		if 'name' in self.__dict__:
			self.__register(namespace,self.name)
		# loop over all our attributes to find contained nodes, references and aliases
		for key in self.__dict__:
			# ignore our private attributes and any name attribute
			if key.startswith('_node__') or key == 'name':
				continue
			attr = getattr(self,key)
			# add any node attributes
			if isinstance(attr,node):
				self.__addChild(attr,namespace,reference)
			# scan any dictionary attributes for contained nodes
			elif isinstance(attr,dict):
				self.__processItems(attr,attr.iterkeys(),namespace,reference)
			# scan any non-string iterable attributes for contained nodes
			elif not isinstance(attr,basestring):
				try:
					self.__processItems(attr,xrange(len(attr)),namespace,reference)
				except TypeError:
					pass
			# remember a reference by name
			elif isinstance(attr,refByName):
				self.__addRef(self.__dict__,key,attr,reference)
			# register an alias
			elif isinstance(attr,alias):
				self.__register(namespace,attr)
	

def createGraph(root):
	"""
	Infer a graph and resolve any internal references.
	
	Infer a graph of nodes from the root object which must be an
	instance of a node. Can be run multiple times to stay synchronized
	with dynamic changes to the root node but is usually just run once.
	Returns a namespace dictionary that can be safely ignored if you are
	only using the reference-by-name feature of graphs. Raises an
	exception if the graph contains duplicate names or unresolved
	references.
	"""
	if not isinstance(root,node):
		raise NameGraphException('root must be a node')
	namespace = {}
	reference = {}
	# scan the root to populate its namespace and obtain a list of references to be resolved
	root._node__bind(namespace,reference)
	# try to resolve all references against the namespace
	for (target,instances) in reference.iteritems():
		if not target in namespace:
			raise UnresolvedReference(
				'graph contains %d unresolved reference%s to "%s"',
				(len(instances),len(instances)>1 and 's' or '',target)
			)			
		for (base,key) in instances:
			base[key] = namespace[target]
	# Every subnode of the graph should now have a valid _node__parent attribute.
	# Define this for the root also for complete coverage.
	root._node__parent = None
	# Return the namespace dictionary in case the user wants to refer to it later.
	return namespace
	

import unittest

class NameGraphTests(unittest.TestCase):
	class NamedNode(node):
		def __init__(self,name):
			# named node should define a name attribute but does not need to call node.__init__()
			self.name = name
	class AnonNode(node):
		# a node does not need to be named, in which case it cannot be referenced by name
		pass
	class ContainerNode(node):
		def __init__(self,name,attr,*args,**kargs):
			self.name = name
			self.attr = attr
			self.args = list(args)
			self.kargs = kargs.copy()
	def test01_nodes(self):
		"""Create named and anonymous nodes"""
		named = NameGraphTests.NamedNode('named')
		unicode_named = NameGraphTests.NamedNode(u'named')
		anon = NameGraphTests.AnonNode()
	def test02_name_type_error(self):
		"""Node name must be a basestring"""
		self.assertRaises(InvalidName,
			lambda: createGraph(NameGraphTests.NamedNode(123))
		)
	def test03_name_empty_error(self):
		"""Node name must be non-empty"""
		self.assertRaises(InvalidName,
			lambda: createGraph(NameGraphTests.NamedNode(' \t'))
		)
	def test04_bind_leaf_node(self):
		"""Leaf node has no descendents"""
		namespace = createGraph(NameGraphTests.AnonNode())
		self.assertEqual(namespace.keys(),[])
	def test05_bind_empty_container(self):
		"""Empty container node"""
		namespace = createGraph(NameGraphTests.ContainerNode('container',"ABC"))
		self.assertEqual(namespace.keys(),['container'])
	def test06_bind_attr(self):
		"""Node contains via attribute reference"""
		namespace = createGraph(
			NameGraphTests.ContainerNode('container',NameGraphTests.NamedNode('child'))
		)
		self.assertEqual(namespace.keys(),{'container':0,'child':0}.keys())
	def test07_bind_list(self):
		"""Node contains recusively via a list attribute"""
		namespace = createGraph(
			NameGraphTests.ContainerNode('container',"ABC",
				NameGraphTests.NamedNode('list1'),'not a node',NameGraphTests.NamedNode('list2')
			)
		)
		self.assertEqual(namespace.keys(),{'container':0,'list1':0,'list2':0}.keys())
	def test08_bind_dict(self):
		"""Node contains recursively via a dictionary attribute"""
		namespace = createGraph(
			NameGraphTests.ContainerNode('container',"ABC",
				arg1=NameGraphTests.NamedNode('dict1'),
				arg2='not a node',arg3=NameGraphTests.AnonNode()
			)
		)
		self.assertEqual(namespace.keys(),{'container':0,'dict1':0}.keys())
	def test09_backwards_attr_ref(self):
		"""Backwards reference by name from attribute"""
		g = NameGraphTests.ContainerNode('parent',"ABC",
			NameGraphTests.NamedNode('child'),
			NameGraphTests.ContainerNode('container',refByName('child'))
		)
		createGraph(g)
		self.assertEqual(id(g.args[0]),id(g.args[1].attr))
	def test10_backwards_list_ref(self):
		"""Backwards reference by name from list"""
		g = NameGraphTests.ContainerNode('parent',"ABC",
			NameGraphTests.NamedNode('child'),
			NameGraphTests.ContainerNode('container','ABC',
				refByName('child')
			)
		)
		createGraph(g)
		self.assertEqual(id(g.args[0]),id(g.args[1].args[0]))
	def test11_backwards_dict_ref(self):
		"""Backwards reference by name from dictionary"""
		g = NameGraphTests.ContainerNode('parent',"ABC",
			NameGraphTests.NamedNode('child'),
			NameGraphTests.ContainerNode('container','ABC',
				arg0=refByName('child')
			)
		)
		createGraph(g)
		self.assertEqual(id(g.args[0]),id(g.args[1].kargs['arg0']))
	def test12_forwards_ref(self):
		"""Forwards reference by name"""
		g = NameGraphTests.ContainerNode('parent',"ABC",
			refByName('child'),
			NameGraphTests.NamedNode('child')
		)
		createGraph(g)
		self.assertEqual(id(g.args[0]),id(g.args[1]))
	def test13_duplicate_name(self):
		"""Duplicate name not allowed"""
		g = NameGraphTests.ContainerNode('parent',"ABC",
			NameGraphTests.NamedNode('child'),
			NameGraphTests.NamedNode('child')
		)
		self.assertRaises(DuplicateName,lambda: createGraph(g))
	def test14_unresolved_ref(self):
		"""Unresolved reference by name not allowed"""
		g = NameGraphTests.ContainerNode('parent',"ABC",
			NameGraphTests.NamedNode('child1'),
			refByName('child2')
		)
		self.assertRaises(UnresolvedReference,lambda: createGraph(g))
	def test15_multiple_refs(self):
		"""Multiple references to same name"""
		g = NameGraphTests.ContainerNode('parent',
			refByName('child'),
			NameGraphTests.NamedNode('child'),
			refByName('child')
		)
		createGraph(g)
		self.assertEqual(id(g.attr),id(g.args[0]))
		self.assertEqual(id(g.args[1]),id(g.args[0]))
	def test16_aliases(self):
		"""Node name aliases"""
		g = NameGraphTests.ContainerNode('parent',"ABC",
			NameGraphTests.ContainerNode('container',alias('collection'),alt=alias('group')),
			refByName('collection'),
			refByName('group')
		)
		createGraph(g)
		self.assertEqual(id(g.args[0]),id(g.args[1]))
		self.assertEqual(id(g.args[0]),id(g.args[2]))
		
if __name__ == '__main__':
	unittest.main()