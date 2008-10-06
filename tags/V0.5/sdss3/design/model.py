"""
A Domain Model of the SDSS-3 Operations Software Design

A description of the actors and nouns of the SDSS-3 operations software
design, and the relationships between them. Running this file will
generate an HTML glossary and a domain-model graph. This file can also
be included as a module to provide a glossary for other design
documents.
"""

## @package tops.sdss3.design.model
# A Domain Model of the SDSS-3 Operations Software Design
#
# @author David Kirkby, dkirkby@uci.edu
# @date Created 24-Jun-2008
#
# This project is hosted at sdss3.org and tops.googlecode.com

from tops.core.design.domain_model import *

model = DomainModel('SDSS-3 Operations Software',
	Actor('Operator',
		"""
		Person in charge of routine night-time operations.
		""",
		isA('User')
	),
	Actor('System Manager',
		"""
		Person responsible for monitoring and maintaining the operations
		hardware and software system.
		""",
		isA('User')
	),
	Actor('Instrument Expert',
		"""
		Person responsible for maintaining and debugging one or more
		[instruments] and the [telescope] infrastructure, usually during day
		shift.
		""",
		isA('User')
	),
	Actor('Scientist',
		"""
		Person interested in observing strategy and analyzing exposures.
		""",
		isA('User')
	),
	Actor('User',
		"""
		Person who interacts with the operations software.
		""",
		has('Sessions','Profile','Agent')
	),
	Noun('Agent',
		"""
		Software running on behalf of a [user] on their local computer.
		Could be a dedicated program or else a web browser. Interacts
		with the operations software via network protocols.
		"""
		),
	Noun('Session',
		"""
		A [user]'s transient interaction with a single [application]. A
		session does not automatically have the full privileges of its
		[user] (to facilitate resource sharing). One [user] may have
		multiple overlapping sessions at once. A [user] must
		authenticate themselves in order to establish a session. All
		session activities are centrally logged.
		""",
		has('Log Stream')
	),
	Noun('Profile',
		"""
		The information needed to authenticate a [user] as well as the
		privileges they are authorized to attach to one of their
		[sessions]. [Application] preferences might also be here.
		"""
	),
	Noun('Role',
		"""
		A well-defined set of [user] responsibilities and privileges for
		a particular [application]. An [application] might have zero,
		one, or several roles. Examples: an observing [application]
		might define 'pilot' and 'navigator' roles.
		""",
		has('Session')
	),
	Noun('Application',
		"""
		A program to perform a well-defined subset of operations tasks,
		that may or may not require [user] interaction. Applications are
		coordinated so that at most one has write/control access to any
		external [device] at any time.
		""",
		has('Roles',one('Config Data'),'Log Stream','Partition','Command Dictionary')
	),
	Noun('Log Stream',
		"""
		A unified stream of log messages and parameter values that is
		available for real-time display and monitoring and also archived
		for offline playback.
		"""
	),
	Noun('Config Data(:)', # Data is its own plural
		"""
		The persistent information needed to configure an [application].
		Changes to configuration are tracked and can be rolled back. The
		ability to change configuration is limited to certain [users].
		"""
	),
	Noun('Command Dictionary',
		"""
		The list of actions that an [application] can perform on behalf
		of a user, including the documentation of these actions.
		"""
	),
	Noun('Partition',
		"""
		A subset of all available [devices], with each [device] acquired
		in either read-only or read-write mode. Only one partition may
		have read-write access to a [device] at a time. There is a
		one-to-one mapping between a running instance of an
		[application] and a partition. Partitions are dynamic, by
		design, but a particular [application] might be written to
		always use the same [devices].
		""",
		has('Proxies','Log Stream')
	),
	Noun('Proxy',
		"""
		Software running on the operations host that encapsulates the
		behavior of a [device] in a uniform way for the higher-level
		operations software. Only those aspects of the [device] that
		[applications] might need to control or monitor need to captured
		by the proxy. Each proxy translates between the uniform protocol
		used by [applications] and the protocol of a specific [device].
		A proxy summarizes the health of its [device] in a uniform way.
		""",
		has('State Chart','Data Dictionary')
	),
	Noun('State Chart',
		"""
		A hierarchical representation of the internal states of a
		[device] that [applications] and [users] need to be aware of and
		the actions that cause changes to this state. Changes of state
		are triggered by [applications], possibly under [user] control.
		"""
	),
	Noun('Data Dictionary',
		"""
		A description of the internal parameters of a [device] that
		[applications] and [users] need to be aware of, including their
		range or allowed states, units, and documentation. Any
		[application] can read any of the parameters associated with its
		[partition]. Some parameters can addtionally be written, but by
		at most one [application] at a time.
		"""
	),
	Actor('Database',
		"""
		The persistent store of data related to the operations software.
		Access is controlled via specific [applications]. Could be
		implemented with an SQL relational database but this is not a
		requirement. Must have high availability and reliable backups.
		Read and write bandwidths are expected to be modest.
		""",
		has(multiple('Config Data'),'Log Streams')
	),
	Actor('Device',
		"""
		An autonomous external component of the operations system with a
		well-defined communications channel and protocol. Devices might
		be hardware or external software. Each device interfaces with
		the operations software via an instance of a [proxy].
		""",
		has('Proxy')
	),
	Actor('TCC',
		"""
		The Telescope Control Computer (TCC) is dedicated to controlling
		the [telescope]. A dedicated VMS workstation running multiple
		processes and supporting multiple interactive or network command
		sessions. TCC documentation is
		[http://www.apo.nmsu.edu/Telescopes/TCC/index.html available online].
		""",
		isA('Device')
	),
	Actor('MARVELS',
		"""
		The Multiobject APO Radial Velocity Exoplanet Large-Area Survey
		[instrument] and its associated control computer.
		""",
		isA('Instrument')
	),
	Actor('Instrument',
		"""
		A piece of equipment that records the light from fibers
		installed at the focal plane (an 'exposure'). Instruments
		generally need calibrating before and after science exposures
		and their exposures can be checked for data quality.
		""",
		isA('Device')
	),
	Actor('Telescope',
		"""
		The optics, mechanics and control and monitoring system of the APO
		2.5m telescope. The operations software interfaces to the telescope
		via the [TCC].
		""",
		isA('Device')
	)
)

if __name__ == '__main__':
	import path
	model.exportGraph(path.filepath('sdss3model.dot'))
	model.exportGlossary(path.filepath('glossary.html'),
		title='SDSS3 Operations Software Glossary',
		stylesheet='glossary.css')