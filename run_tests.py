"""
Finds and runs unit tests

Finds unit tests by recursively searching from the current directory.
Tests are loaded and run using the standard unittest infrastructure.
"""

## @package tops
# Finds and runs unit tests
#
# @author David Kirkby, dkirkby@uci.edu
# @date Created 6-Sep-2008
#
# This project is hosted at http://tops.googlecode.com/

import os
import sys
import unittest

IGNORE_FILES = ['run_tests.py',]

suite = unittest.TestSuite()
debug = False

def visit(arg,dirname,names):
	dotpath = dirname[2:].replace('/','.')
	for (index,name) in enumerate(names):
		if name in ('.svn','run_tests.py'):
			del names[index]
		elif name[-3:] == '.py':
			dotname = '%s.%s' % (dotpath,name[:-3])
			print dotname
			suite.addTest(unittest.defaultTestLoader.loadTestsFromName(dotname))

os.path.walk('.',visit,None)

test_runner = unittest.TextTestRunner()
result = test_runner.run(suite)
if result.failures or result.errors:
	sys.exit(1)
