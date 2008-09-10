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

class CoordinateSystem(data.enumerated):
	labels = ('ICRS','FK5','FK4','Gal','Geo','None','Topo','Obs','Phys','Mount','Inst','GImage')

#########################################################################
# Configure the proxy's main event loop here.
#########################################################################

from tops.core.utility.astro_time import AstroTime,TAI,UTC
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
			'obj.coordsys': packet.coordSys.rstrip('\x00'), # remove trailing pad bytes
			'obj.netpos.axis1': packet.objNetPosAxis1,
			'obj.netpos.axis2': packet.objNetPosAxis2
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
				#('slew_end_time',TAIMJD),
				('obj.coordsys',CoordinateSystem),
				('obj.netpos.axis1',data.double),
				('obj.netpos.axis2',data.double)
			)
		)
	)
	listener.start()