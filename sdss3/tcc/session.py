"""
Implements a read-write proxy for the TCC command interpreter

Defines the custom data types associated with the TCC's command
interpreter, and implements a proxy that can issue commands via a telnet
session.

Refer to the proxy declaration below for details of its operating states
and archive records. Running this module will start the proxy and so
requires that the logging and archiving servers are already up.
"""

## @package tops.sdss3.tcc.session
# Implements a read-write proxy for the TCC command interpreter
#
# @author David Kirkby, dkirkby@uci.edu
# @date Created 13-Sep-2008
#
# This project is hosted at http://tops.googlecode.com/

#from tops.core.network.proxy import *

from tops.core.network.telnet import TelnetSession

class VMSSession(TelnetSession):

	login_prompt = 'Username: '
	password_prompt = 'Password: '
	command_prompt = '$ '


from getpass import getpass
from twisted.internet import reactor
from tops.core.network.telnet import prepareTelnetSession

if __name__ == "__main__":
	
	(hostname,port,username) = ('localhost',23,'david')
	password = getpass('Enter password for %s@%s: ' % (username,hostname))
	
	prepareTelnetSession(FTPSession('FTP',username,password,debug=False),hostname,port)
	prepareTelnetSession(LocalhostSession('localhost',username,password,debug=False),hostname,port)
	
	reactor.callLater(1.9,ftp_commands)
	reactor.callLater(2.0,localhost_commands)
	reactor.callLater(3.0,reactor.stop)
	
	reactor.run()
