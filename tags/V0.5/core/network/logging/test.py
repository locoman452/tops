"""
Tests the distributed logging infrastructure

Implements a logging producer client to send a stream of logging
messages. Running this module tests the producer code and that a server
is running and correctly handles the messages.
"""

## @package tops.core.network.logging.test
# Tests the distributed logging infrastructure
#
# @author David Kirkby, dkirkby@uci.edu
# @date Created 6-Aug-2008
#
# This project is hosted at sdss3.org and tops.googlecode.com

if __name__ == "__main__":

	# load our run-time configuration
	import tops.core.utility.config as config
	verbose = config.initialize()

	import tops.core.network.logging.producer as logging
	
	logging.initialize('log.client.test')

	from time import sleep

	log = logging.getLogger('proxy.tcc')
	log.setLevel(logging.DEBUG)

	extra = { 'SaveContext':True }

	for (level) in (logging.DEBUG,logging.INFO,logging.WARNING,logging.ERROR,logging.CRITICAL):
		log.log(level,"This message has level %s",logging.getLevelName(level),extra=extra)
		sleep(0.5)
		logging.log(level,"This message has level %s",logging.getLevelName(level),extra=extra)
		sleep(0.5)

	try:
		raise Exception("something bad happened")
	except:
		logging.exception('Uh-oh!')
	
	# Test a log message with unicode
	sleep(1.0)
	unicode_msg = u'\u00b1\u0394\u03d3 sin(2\u03b2) \u00a9 360\u00b0 \u2207\u221e\u2211\u2202'
	logging.error(unicode_msg)

	# Test a log message with embedded quotes
	sleep(1.0)
	logging.error('He\'s supposed to have said "I didn\'t say that"')

	# Test a log message with embedded control sequences
	sleep(1.0)
	logging.error('This message contains TWO\t\tTABS and a\nsecond line with \\TWO\\ backslashes')

	logging.shutdown()
