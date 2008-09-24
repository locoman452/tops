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
import getpass

if __name__ == '__main__':
	
	# bootstrap our module path
	tops_path = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
	try:
		env_path = os.environ['PYTHONPATH']
		print 'start: PYTHONPATH is already set...will try that.'
	except KeyError:
		print 'start: Setting PYTHONPATH = %s' % tops_path
		sys.path.insert(1,tops_path)
		os.environ['PYTHONPATH'] = tops_path
	try:
		from tops.core.utility import config,secret
	except ImportError:
		if env_path:
			print 'start: Import failed with PYTHONPATH = \n',env_path
			sys.exit(1)
		else:
			print 'start: Unable to bootstrap module path. Please check your installation.'
			sys.exit(2)
		
	# load our run-time configuration
	verbose = config.initialize('start')
	
	# prompt for the decryption passphrase used for private data if requested
	private_key = None
	if config.getboolean('start','get_passphrase'):
		passphrase = getpass.getpass('Enter the pass phrase: ')
		engine = secret.SecretEngine(passphrase=passphrase)
		private_key = engine.key
		del engine
	
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
				print 'start: Unable to import service %s' % service_name
				sys.exit(-1)
			path = sys.modules[service_name].__file__
			# check that a readable file exists at this path
			if not os.path.isfile(path):
				print 'start: Mo such file %s' % path
				sys.exit(-2)
			if verbose:
				print 'start: Located %s at %s' % (service_name,path)
			services[launch_order] = (service_name,path)

	# start the services
	if verbose:
		print 'start: Running python as %s' % sys.executable
	ordered = [services[order] for order in sorted(services)]
	pidlist = [ ]
	delay = config.getfloat('start','delay')
	if private_key:
		stdin = subprocess.PIPE
		sys.argv.append('--readkey')
	else:
		stdin = None
	for (service,path) in ordered:
		args = [sys.executable,path]
		args.extend(sys.argv[1:])
		try:
			process = subprocess.Popen(args,shell=False,stdin=stdin)
			print 'start: service %s is pid %d' % (service,process.pid)
			# write the private key via stdout if necessary
			if private_key:
				process.stdin.write(private_key+'\n')
			# give the service's initialization code a chance to complete
			time.sleep(delay)
			# check that the process is still running before continuing
			if process.poll() is not None:
				print 'start: Service did not start successfully'
				break
			else:
				pidlist.append(str(process.pid))
		except OSError:
			print 'start: Unable to execute "%s"' % command
	
	# Save the list of process IDs we have just started
	if len(pidlist) > 0:
		pidlist.reverse()
		pidfile = config.getfilename('start','pidfile') or 'pidlist'
		pidfile = file(pidfile,'w')
		print >> pidfile, ' '.join(pidlist)
		pidfile.close()
		print 'start: Services can be killed with: kill -INT `cat %s`' % pidfile.name