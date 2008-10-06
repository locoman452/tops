"""
Design file path utility

Ensures that the web content corresponding to SDSS-3 design files are
exported to a web/ subdirectory of sdss3.design.
"""

## @package tops.sdss3.design.path
# Design file path utility
#
# @author David Kirkby, dkirkby@uci.edu
# @date Created 8-Sep-2008
#
# This project is hosted at sdss3.org and tops.googlecode.com

import sys
import os.path

if __name__ == '__main__':
	__file__ = sys.argv[0]

# write design files to a web/ subdirectory of our own path
mypath = os.path.dirname(__file__)
webpath = os.path.join(mypath,'web')
assert(os.path.isdir(webpath))

export_count = 0

def filepath(filename):
	global export_count
	if export_count == 0:
		print 'Exporting SDSS-3 design web content to',webpath
	export_count += 1
	print '  %s' % filename
	return os.path.join(webpath,filename)