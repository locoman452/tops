"""
Defines the Telescope Control Computer UDP broadcast packet format

Provides a wrapper for a TCC UDP packet with support for packing and
unpacking into a buffer, and generating random packets for testing.
Running this module will start a TCC UDP simulator on port 1201.
"""

## @package tops.sdss3.tcc.broadcast
# Defines the Telescope Control Computer UDP broadcast packet format
#
# @author David Kirkby, dkirkby@uci.edu
# @date Created 29-Jul-2008
#
# This project is hosted at http://tops.googlecode.com/

from struct import Struct
from random import random
from tops.core.utility.astro_time import AstroTime,TAI

portMap = { '2.5m': 1200, '3.5m': 1235, 'simulator': 1201 }

class PacketError(Exception):
	pass

class Packet(object):
	
	version = (2,2)
	head = Struct('!4I')
	data = Struct('!2d8s9di4x12d8x')
	fields = [
		'timestamp','slewEndTime','coordSys','epoch','objAxis1Pos','objAxis1Vel',
		'objAxis2Pos','objAxis2Vel','boreXPos','boreXVel','boreYPos',
		'boreYVel','rotType','rotPos','rotVel','objAngPos','objAngVel','spiderAngPos',
		'spiderAngVel','tccAzPos','tccAzVel','tccAltPos','tccAltVel','tccRotPos','tccRotVel'
	]
	
	def __init__(self,*values):
		if len(values) != len(self.fields):
			raise PacketError('got %d field values but expected %d' %
				(len(values),len(self.fields)))
		self.values = tuple(values)

	def __getattr__(self,name):
		if name not in self.fields:
			raise AttributeError('no such Packet field named "%s"' % name)
		return self.values[self.fields.index(name)]

	def __str__(self):
		format = '%%%ds: %%s\n' % max((len(f) for f in self.fields))
		result = ''
		for i in xrange(len(self.fields)):
			result += format % (self.fields[i],str(self.values[i]))
		return result[:-1] # remove trailing newline

	@staticmethod
	def read(buffer):
		"""Reads a packet from the specified buffer."""
		# read the header first
		if len(buffer) < 16:
			raise PacketError('buffer is too small to contain a packet: %d bytes' % len(buffer))
		(size,typecode,major,minor) = Packet.head.unpack(buffer[0:16])
		# perform header checks
		if not (major,minor) == Packet.version:
			raise PacketError('cannot unpack unrecognized packet version %d.%d' % (major,minor))
		if not size == Packet.head.size + Packet.data.size:
			raise PacketError('got unexpected header size %d (expected %d)' %
				(size,Packet.head.size+Packet.data.size))
		if not len(buffer) == size:
			raise PacketError('got unexpected buffer size %d (expected %d)' %
				(len(buffer),size))
		# unpack the data and use it to try and create a new packet
		return Packet(*Packet.data.unpack(buffer[16:]))

	def write(self,typecode=0xdeadbeef):
		"""Writes this packet to a buffer."""
		return (self.head.pack(self.head.size+self.data.size,typecode,*self.version) + 
			self.data.pack(*self.values))

	@staticmethod
	def generate():
		"""Returns a randomly generated packet."""
		timestamp = AstroTime.now(TAI).MJD()
		slewEndTime = float('nan')
		coordSys = 'Mount'
		random9 = [random() for i in range(9)]
		rotType = int(1234)
		random12 = [random() for i in range(12)]
		values = [timestamp,slewEndTime,coordSys] + random9 + [rotType] + random12
		return Packet(*values)


import socket
import time

class Broadcaster(object):
	"""
	Broadcasts UDP packets to simulate the TCC.
	"""
	def __init__(self,port):
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.socket.connect(("<broadcast>",port))
		self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

	def transmit(self):
		p = Packet.generate()
		print 'Transmitting',len(p.write()),'bytes'
		self.socket.send(p.write())
		
	def transmitPeriodically(self,interval=1.0):
		try:
			while True:
				self.transmit()
				time.sleep(interval)
		except KeyboardInterrupt:
			print 'bye'

if __name__ == '__main__':
	b = Broadcaster(port=portMap['simulator'])
	b.transmitPeriodically()
	#b.transmit()
