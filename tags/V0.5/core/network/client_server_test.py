"""
Tests core client-server interaction

Exercises the core client and server base classes using simple header
and message classes that are independent of any protocol buffers.
"""

## @package tops.core.network.test
# Tests core client-server interaction
#
# @author David Kirkby, dkirkby@uci.edu
# @date Created 9-Sep-2008
#
# This project is hosted at sdss3.org and tops.googlecode.com

class TestHeader(object):
	def __init__(self,name=None):
		self.name = name
	def SerializeToString(self):
		return self.name
	def ParseFromString(self,string):
		self.name = string

class TestMessage(object):
	def __init__(self,number=None):
		self.number = number
	def SerializeToString(self):
		return str(self.number)
	def ParseFromString(self,string):
		self.number = float(string)


import client,server

class TestClient(client.Client):
	"""
	Defines a simple client for testing
	
	We only need to specify our header and message types here.
	"""
	Header = TestHeader
	Message = TestMessage

class TestServer(server.Server):
	"""
	Defines a simple server for testing
	
	Implement the connection and protocol methods so that each client
	generates a single line of output that looks something like this:
	{ [header-name] (val1) (val2) ... }
	"""
	Header = TestHeader
	Message = TestMessage
	
	def connectionMade(self):
		sys.stdout.write('{')
		
	def connectionLost(self,reason):
		sys.stdout.write(' }\n')
	
	def handleHeader(self,hdr):
		sys.stdout.write(" [%s]" % hdr.name)

	def handleMessage(self,msg):
		sys.stdout.write(" (%g)" % msg.number)


import unittest
import subprocess
import os
import sys
import signal
import time

class ClientServerTests(unittest.TestCase):
	def test00(self):
		"""Unix client fails with no server listening"""
		client_process = subprocess.Popen("%s %s unixclient" % (sys.executable,__file__),
			shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
		self.assertEqual(client_process.wait(),1)
	def test01(self):
		"""TCP client fails with no server listening"""
		client_process = subprocess.Popen("%s %s tcpclient" % (sys.executable,__file__),
			shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
		self.assertEqual(client_process.wait(),1)
	def test02(self):
		"Unix client communicates successfully with server"
		server_process = subprocess.Popen("%s %s server" % (sys.executable,__file__),
			shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
		time.sleep(1)
		client_process = subprocess.Popen("%s %s unixclient" % (sys.executable,__file__),
			shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
		client_process.wait()
		os.kill(server_process.pid,signal.SIGINT)
		message = server_process.stdout.readline()
		self.assertEqual(client_process.returncode,0)
		self.assertEqual(message,"{ [network-test] (1.23) (-9.87) }\n")


if __name__ == '__main__':

	import sys
	from twisted.internet.protocol import Factory
	from twisted.internet import reactor
	
	assert(len(sys.argv) == 2)
	
	if sys.argv[1] == 'server':
		factory = Factory()
		factory.protocol = TestServer
		reactor.listenTCP(1999,factory)
		reactor.listenUNIX('/tmp/network-test',factory)
		reactor.run()

	elif sys.argv[1] == 'unixclient':
		c = TestClient('/tmp/network-test','',0)
		c.sendHeader(TestHeader('network-test'))
		c.sendMessage(TestMessage(1.23))
		c.sendMessage(TestMessage(-9.87))
		c.close()

	elif sys.argv[1] == 'tcpclient':
		c = TestClient(None,'localhost',1999)
		c.sendHeader(TestHeader('network-test'))
		c.sendMessage(TestMessage(1.23))
		c.sendMessage(TestMessage(-9.87))
		c.close()
		
	elif sys.argv[1] == 'test':
		__file__ = sys.argv[0]
		del sys.argv[1]
		unittest.main()
