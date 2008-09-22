"""
Starts the telescope operations software

Starts the processes specified in the run-time configuration files for
the specified project. See http://code.google.com/p/tops/wiki/Running
for details.

Note that this program is normally invoked via the start shell script.
"""

## @package tops.start
# Starts the telescope operations software
#
# @author David Kirkby, dkirkby@uci.edu
# @date Created 19-Sep-2008
#
# This project is hosted at http://tops.googlecode.com/

import sys
import os.path
import subprocess

if __name__ == '__main__':
	
	# bootstrap our module path
	tops_path = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
	env_path = os.getenv('PYTHONPATH')
	if env_path:
		print 'PYTHONPATH is already set...will try that.'
	else:
		sys.path.insert(1,tops_path)
		os.putenv('PYTHONPATH',tops_path)
	try:
		import tops.core.utility.options as options
		import tops.core.utility.config as config
	except ImportError:
		if env_path:
			print 'Unable to import TOPS modules with current value of PYTHONPATH:\n',env_path
			sys.exit(1)
		else:
			print 'Unable to bootstrap TOPS module path. Please check your installation.'
			sys.exit(2)
		
	# load our run-time configuration
	options.initialize('start')
	verbose = options.get('verbose')
	config.initialize(options.get('project'),verbose)
	
	# collect a list of services to start and perform some checks
	services = { }
	for section in config.theParser.sections():
		service_name = config.get(section,'service')
		launch_order = config.get(section,'launch_order')
		if service_name and launch_order and config.get(section,'enable') == 'True':
			# convert this service name to a filesystem path
			try:
				__import__(service_name,globals(),locals(),['__file__'],-1)
			except ImportError:
				print 'start: unable to import service %s' % service_name
				sys.exit(-1)
			path = sys.modules[service_name].__file__
			# check that a readable file exists at this path
			if not os.path.isfile(path):
				print 'start: no such file %s' % path
				sys.exit(-2)
			services[launch_order] = (service_name,path)

	sys.exit(0)

	# start the services
	ordered = [services[order] for order in sorted(services,key=int)]
	for (service,path) in ordered:
		args = [sys.executable,path]
		args.extend(sys.argv[1:])
		try:
			process = subprocess.Popen(args,shell=False)
			print 'start: service %s is pid %d' % (service,process.pid)
		except OSError:
			print 'start: unable to execute "%s"' % command
