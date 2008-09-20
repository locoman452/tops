"""
Parses command line options
"""

## @package tops.core.utility.options
# Parses command line options
#
# @author David Kirkby, dkirkby@uci.edu
# @date Created 19-Sep-2008
#
# This project is hosted at http://tops.googlecode.com/

from optparse import OptionParser

theOptions = None
theArgs = None

def initialize():
	"""
	Initializes standard command line options processing
	"""
	# create a new parser
	theParser = OptionParser("usage: %prog [options]")
	# define standard options
	theParser.add_option(
		"--project", action="store", type="string", dest="project",
		help="python module path of project to start, e.g., tops.sdss3"
	)
	theParser.add_option(
		"--verbose", action="store_true", dest="verbose",
		help="generate verbose output"
	)
	theParser.set_defaults(verbose=False)
	global theOptions,theArgs
	(theOptions,theArgs) = theParser.parse_args()

def get(option):
	global theOptions
	assert(theOptions is not None)
	return getattr(theOptions,option,None)
