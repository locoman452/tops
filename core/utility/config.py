"""
Manages run-time configuration

Provides an interface to run-time configuration parameters stored in INI
files. The normal initialization in a __main__ module is:

  import tops.core.utility.config as config
  verbose = config.initialize()

Once the configuration module has been initialized, parameters for a
named section are retrieved with the get(), getint(), getfloat() and
getboolean() functions, e.g.

  delay = options.get('start','delay')
"""

## @package tops.core.utility.config
# Manages run-time configuration
#
# @author David Kirkby, dkirkby@uci.edu
# @date Created 11-Sep-2008
#
# This project is hosted at http://tops.googlecode.com/

import sys,os,os.path
from ConfigParser import SafeConfigParser,NoOptionError
import tops.core.utility.options as options

theParser = None

class ConfigError(Exception):
	pass

def initialize(prog_name=None):
	"""
	Initializes the configuration module so that options can be read.
	
	Options are stored in INI files and read with a SafeConfigParser.
	Files are (re)read whenever this function is called. Files
	are read in the following order:
	
	  1. tops.core: config.ini
	  2. <project>: config.ini
	  3. command-line config file
	
	<project> is the project module path provided on the command line
	and obtained via the tops.core.utility.options module. The project
	module path can be anywhere on the module search path and does not
	need to be under tops.
	
	The name of the third file to search is an optional command-line
	parameter obtained via the tops.core.utility.options module.
	
	The prog_name parameter is passed to the initialize() method of
	tops.core.utility.options.
	
	Returns the value of the 'verbose' run-time option.
	"""
	# parse the command-line options
	options.initialize(prog_name)
	projectModulePath = options.get('project')
	configOverrides = options.get('config')
	verbose = options.get('verbose')
	# create our options parser	
	global theParser
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
	# finally, use a config overrides file if one was provided
	if configOverrides:
		files.append(configOverrides)
	# run the parser over our file list
	found = theParser.read(files)
	if verbose:
		print 'config: looked for\n ','\n  '.join(files)
		print 'config: found\n ','\n  '.join(found)
	return verbose

def _get(section,option,method="get"):
	global theParser
	if theParser is None:
		raise ConfigError('Must initialize() the configuration module before getting options')
	try:
		getter = getattr(theParser,method)
		return getter(section,option)
	except NoOptionError:
		return None

def get(section,option):
	"""
	Looks up an option from the specified section.
	
	The initialize() function must be called be options can be read.
	Raises an exception if this is not the case. Returns the last value
	of the option read from the configuration files, or None if no value
	was read.
	"""
	return _get(section,option)

def getint(section,option):
	"""
	Coerces the result of a get() call to an integer value.
	"""
	return _get(section,option,"getint")
	
def getfloat(section,option):
	"""
	Coerces the result of a get() call to a floating-point value.
	"""
	return _get(section,option,"getfloat")

def getboolean(section,option):
	"""
	Coerces the result of a get() call to a boolean value.
	"""
	return _get(section,option,"getboolean")
