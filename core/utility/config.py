"""
Manages run-time configuration

Provides an interface to run-time configuration parameters stored in INI
files.
"""

## @package tops.core.utility.config
# Manages run-time configuration
#
# @author David Kirkby, dkirkby@uci.edu
# @date Created 11-Sep-2008
#
# This project is hosted at http://tops.googlecode.com/

from ConfigParser import SafeConfigParser,NoOptionError

import sys,os,os.path

theParser = None

class ConfigError(Exception):
	pass

def initialize(projectModulePath=None,verbose=False):
	"""
	Initializes the configuration module so that options can be read.
	
	Options are stored in INI files and read with a SafeConfigParser.
	Files are (re)read whenever this function is called. Files
	are read in the following order:
	
	  tops.core: config.ini
	  <project>: config.ini
	  $CWD: tops-config.ini
	
	where <project> is the optional projectModulPath provided, e.g.
	"tops.sdss3". The project module path can be anywhere on PYTHONPATH
	and does not need to be under tops. The $CWD is obtained with
	os.getcwd().
	"""
	global theParser
	# create a new parser
	theParser = SafeConfigParser()
	# first, search the core config file
	from tops.core import __path__ as core_path
	files = [ os.path.join(core_path[0],'config.ini') ]
	# next, try a project-specific config file
	if projectModulePath:
		try:
			__import__(projectModulePath,globals(),locals(),['__path__'],-1)
			proj_path = sys.modules[projectModulePath].__path__
			files.append(os.path.join(proj_path[0],'config.ini'))
		except ImportError:
			raise ConfigError('Cannot import from project path: %s' % projectModulePath)
	# finally, look in the current working dir
	files.append(os.path.join(os.getcwd(),'tops-config.ini'))
	found = theParser.read(files)
	if verbose:
		print 'config: looked for\n ','\n  '.join(files)
		print 'config: found\n ','\n  '.join(found)	


def get(section,option):
	"""
	Looks up an option from the specified section.
	
	The initialize() function must be called be options can be read.
	Raises an exception if this is not the case. Returns the last value
	of the option read from the configuration files, or None if no value
	was read.
	"""
	global theParser
	if theParser is None:
		raise ConfigError('Must initialize() the configuration module before getting options')
	try:
		return theParser.get(section,option)
	except NoOptionError:
		return None
