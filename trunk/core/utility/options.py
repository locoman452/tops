"""
Parses command line options

Provides standardized command-line options processing for TOPS services.
Most run-time configuration is specified by INI files and accessed via
the tops.core.utility.config module, so the main purpose of command-line
options is to bootstrap the file-based configuration. In particular, the
"project" option determines which project-specific INI file is read and
so must be obtained via the command line.
"""

## @package tops.core.utility.options
# Parses command line options
#
# @author David Kirkby, dkirkby@uci.edu
# @date Created 19-Sep-2008
#
# This project is hosted at http://tops.googlecode.com/

import sys
from optparse import OptionParser

theOptions = None
theArgs = None

def initialize(prog_name=None):
	"""
	Initializes standard command line options processing
	"""
	# create a new parser
	theParser = OptionParser("usage: %s [options]" % (prog_name or '%prog'))
	# define standard options
	theParser.add_option(
		"--verbose", action="store_true", dest="verbose",
		help="generate verbose output"
	)
	theParser.add_option(
		"--project", action="store", type="string", dest="project",
		help="python module path of project to start, e.g., tops.sdss3"
	)
	theParser.add_option(
		"--config", action="store", type="string", dest="config",
		help="path of an INI file containing run-time configuration parameters that will override the defaults"
	)
	theParser.add_option(
		"--readkey", action="store_true", dest="readkey",
		help="read private data key from stdin"
	)
	theParser.set_defaults(verbose=False,readkey=False)
	global theOptions,theArgs
	(theOptions,theArgs) = theParser.parse_args()
	# read the private data key now if requested
	if theOptions.readkey:
		theOptions.key = sys.stdin.readline().strip()

def get(option):
	global theOptions
	assert(theOptions is not None)
	return getattr(theOptions,option,None)
