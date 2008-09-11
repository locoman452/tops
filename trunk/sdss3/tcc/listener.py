"""
Implements a read-only proxy for the TCC's periodic UDP broadcasts

Defines the custom data types associated with the TCC's UDP broadcasts,
and implements a proxy that listens for UDP broadcasts and forwards
updates to the archiving server.

Refer to the proxy declaration below for details of its operating states
and archive records. Running this module will start the proxy and so
requires that the logging and archiving servers are already up.
"""

## @package tops.sdss3.tcc.listener
# Implements a read-only proxy for the TCC's periodic UDP broadcasts
#
# @author David Kirkby, dkirkby@uci.edu
# @date Created 18-Aug-2008
#
# This project is hosted at http://tops.googlecode.com/

from tops.core.network.proxy import *

#########################################################################
# Define custom data types here
#########################################################################

from tops.core.utility.astro_time import AstroTime,TAI,UTC

class TAIMJD(AstroTime):
	__metaclass__ = ValueType

	def pack(self,buffer):
		buffer.double = self

	@classmethod
	def unpack(cls,buffer):
		return cls(AstroTime.fromMJD(packet.timestamp,TAI))

class CoordinateSystem(data.enumerated):
	labels = ('ICRS','FK5','FK4','Gal','Geo','None','Topo','Obs','Phys','Mount','Inst','GImage')

class RotationType(data.enumerated):
	labels = ('None','Obj','Horiz','Phys','Mount')

#########################################################################
# Configure the proxy's main event loop here.
#########################################################################

import broadcast
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor

class BroadcastListener(DatagramProtocol):
	
	def __init__(self,timeout):
		self.hosts = []
		self.timeout = timeout
		self.pending = None
	
	def doTimeout(self):
		self.pending = None
		listener.do("timeout")
	
	def datagramReceived(self, data, (host, port)):
		packet = broadcast.Packet.read(data)
		when = AstroTime.fromMJD(packet.timestamp,TAI)
		if host not in self.hosts:
			logging.info('Received first packet from %s with timestamp %s',host,when)
			self.hosts.append(host)
		# If the listener is WAITING, a new packet triggers 'got_packet'.
		# Otherwise, it resets the timeout callback.
		if listener.getState() == 'WAITING':
			listener.do('got_packet')
		else:
			if self.pending:
				self.pending.cancel()
			self.pending = reactor.callLater(self.timeout,self.doTimeout)
		# Update the archiver
		utc = when.astimezone(UTC)
		archiving.update(utc,'broadcast',{
			'slewEndTime':		packet.slewEndTime,
			'obj.coordsys': 	packet.coordSys.rstrip('\x00'), # remove trailing pad bytes
			'epoch':			packet.epoch,
			'obj.axis1.pos':	packet.objAxis1Pos,
			'obj.axis1.vel':	packet.objAxis1Vel,
			'obj.axis2.pos':	packet.objAxis2Pos,
			'obj.axis2.vel':	packet.objAxis2Vel,
			'bore.x.pos':		packet.boreXPos,
			'bore.x.vel':		packet.boreXVel,
			'bore.y.pos':		packet.boreYPos,
			'bore.y.vel':		packet.boreYVel,
			'rot.type':			packet.rotType,
			'rot.pos':			packet.rotPos,
			'rot.vel':			packet.rotVel,
			'obj.ang.pos':		packet.objAngPos,
			'obj.ang.vel':		packet.objAngVel,
			'spider.ang.pos':	packet.spiderAngPos,
			'spider.ang.vel':	packet.spiderAngVel,
			'tcc.az.pos':		packet.tccAzPos,
			'tcc.az.vel':		packet.tccAzVel,
			'tcc.alt.pos':		packet.tccAltPos,
			'tcc.alt.vel':		packet.tccAltVel,
			'tcc.rot.pos':		packet.tccRotPos,
			'tcc.rot.vel':		packet.tccRotVel
		})

def configure():
	"""
	Perform startup configuration of the listener proxy.
	"""
	port = broadcast.portMap['simulator']
	logging.info("Will listen for UDP broadcasts on port %d",port)
	reactor.listenUDP(port,BroadcastListener(timeout=5))
	
#########################################################################
# Define the proxy's states and data here. The top-level name
# determines this proxy's name for logging and archiving via
# name.lower().replace('_",'.'), i.e., "AAA_BBB" -> "aaa.bbb"
#########################################################################

if __name__ == "__main__":
	initialize()
	listener = Proxy('TCC_LISTENER -> WAITING',
		ProxyState('WAITING',
			"""
			Waiting for TCC broadcasts to begin or resume.
			""",
			On('got_packet').goto('LISTENING')
		),
		ProxyState('LISTENING',
			"""
			Listening to periodic TCC broadcasts.
			""",
			On('timeout').goto('WAITING'),
			Monitor('broadcast',
				('slewEndTime',		data.double),				
				('obj.coordSys',	CoordinateSystem),
				('epoch',			data.double),
				('obj.axis1.pos',	data.double),
				('obj.axis1.vel',	data.double),
				('obj.axis2.pos',	data.double),
				('obj.axis2.vel',	data.double),
				('bore.x.pos',		data.double),
				('bore.x.vel',		data.double),
				('bore.y.pos',		data.double),
				('bore.y.vel',		data.double),
				('rot.type',		data.int),     # RotationType
				('rot.pos',			data.double),
				('rot.vel',			data.double),
				('obj.ang.pos',		data.double),
				('obj.ang.vel',		data.double),
				('spider.ang.pos',	data.double),
				('spider.ang.vel',	data.double),
				('tcc.az.pos',		data.double),
				('tcc.az.vel',		data.double),
				('tcc.alt.pos',		data.double),
				('tcc.alt.vel',		data.double),
				('tcc.rot.pos',		data.double),
				('tcc.rot.vel',		data.double)
			)
		)
	)
	listener.start()