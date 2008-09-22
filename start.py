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
import time

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
		import tops.core.utility.config as config
	except ImportError:
		if env_path:
			print 'Unable to import TOPS modules with current value of PYTHONPATH:\n',env_path
			sys.exit(1)
		else:
			print 'Unable to bootstrap TOPS module path. Please check your installation.'
			sys.exit(2)
		
	# load our run-time configuration
	verbose = config.initialize('start')
	
	# collect a list of services to start and perform some checks
	services = { }
	for section in config.theParser.sections():
		service_name = config.get(section,'service')
		launch_order = config.getint(section,'launch_order')
		if service_name and launch_order and config.getboolean(section,'enable'):
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
			if verbose:
				print 'start: located %s at %s' % (service_name,path)
			services[launch_order] = (service_name,path)

	# start the services
	if verbose:
		print 'start: running python as %s' % sys.executable
	ordered = [services[order] for order in sorted(services)]
	pidlist = [ ]
	delay = config.getfloat('start','delay')
	for (service,path) in ordered:
		args = [sys.executable,path]
		args.extend(sys.argv[1:])
		try:
			process = subprocess.Popen(args,shell=False)
			print 'start: service %s is pid %d' % (service,process.pid)
			# give the service's initialization code a chance to complete
			time.sleep(delay)
			# check that the process is still running before continuing
			if process.poll() is not None:
				print 'start: service did not start successfully'
				break
			else:
				pidlist.append(str(process.pid))
		except OSError:
			print 'start: unable to execute "%s"' % command
	
	# Save the list of process IDs we have just started
	pidlist.reverse()
	pidfile = config.get('start','pidfile') or 'pidlist'
	pidpath = os.path.dirname(pidfile)
	if not os.path.exists(pidpath):
		os.makedirs(pidpath)
	pidfile = file(pidfile,'w')
	print >> pidfile, ' '.join(pidlist)
	pidfile.close()
	print 'start: services can be killed with: kill -INT `cat %s`' % pidfile.name