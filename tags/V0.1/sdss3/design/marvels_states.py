"""
MARVELS operations software state chart specification

A description of the MARVELS operating states visible to the SDSS-3
operations software. Running this file will generate an HTML page
documenting the state chart defined here.
"""

## @package tops.sdss3.design.marvels_states
# MARVELS operations software state chart specification
#
# @author David Kirkby, dkirkby@uci.edu
# @date Created 4-Jul-2008
#
# This project is hosted at http://tops.googlecode.com/

from tops.core.utility.state_chart import *

states = StateChart('MARVELS -> CONNECTING',
	State('CONNECTING',
		"""
		Attempting to connect to the MARVELS controller and determine if
		it is available for remote operations.
		""",
		On('(is busy)').goto('EXPERT_BUSY'),
		On('(is available)').goto('AVAILABLE')
	),
	State('AVAILABLE',
		"""
		MARVELS is not being used and is available for either expert or
		remote operations. Whoever acquires MARVELS first will need to
		release it before it becomes available again.
		""",
		On('(expert acquire)').goto('EXPERT_BUSY'),
		On('acquire').goto('REMOTE')
	),
	State('EXPERT_BUSY',
		"""
		MARVELS is being used by an expert using a local software
		interface and will not be available until it they have released
		it.
		""",
		On('(is available)').goto('AVAILABLE')
	),
	State('REMOTE -> ACQUIRED',
		"""
		MARVELS is reserved for remote operations and must be released
		before an expert can use its local software interface.
		""",
		State('ACQUIRED',
			"""
			MARVELS is ready to be configured. It is also in a safe
			state for releasing to other users.
			""",
			On('configure').goto('CONFIGURING'),
			On('release').goto('AVAILABLE')
		),
		State('CONFIGURING',
			"""
			MARVELS is being configured and should soon be ready.
			""",
			On('(configured)').goto('READY')
		),
		State('READY',
			"""
			MARVELS is ready to take an exposure. It is also in a safe
			state for releasing to other users.
			""",
			On('expose').goto('EXPOSING'),
			On('release').goto('AVAILABLE')
		),
		State('EXPOSING',
			"""
			MARVELS is taking an exposure that will end automatically
			when a timer expires, but can also be stopped manually. An
			exposure cannot be paused.
			""",
			On('stop').goto('READING_OUT'),
			On('(timer)').goto('READING_OUT')
		),
		State('READING_OUT',
			"""
			MARVELS is reading out the previous exposure and should be
			done soon.
			""",
			On('(readout done)').goto('READY')
		),
		On('abort').goto('ABORTED'),
		On('(exception)').goto('FAULT'),
		On('park').goto('PARKING')
	),
	State('ABORTED',
		"""
		A non-recoverable MARVELS controller error occured during remote
		operations. A reset will attempt to re-establish communications.
		""",
		On('reset').goto('CONNECTING')
	),
	State('FAULT',
		"""
		A MARVELS controller error occured that may be recoverable by
		using the controller directly. If a recover is successful,
		remote operations will resume where they left off.
		""",
		On('(recover successful)').goto('recall(REMOTE)'),
		On('(recover failed)').goto('ABORTED')
	),
	State('PARKING',
		"""
		MARVELS is being reset to a well-defined state, perhaps in an
		attempt to recover from an error condition.
		""",
		On('parked').goto('AVAILABLE')
	)
)

if __name__ == '__main__':
	import path
	states.exportGraph(path.filepath('marvels_states.dot'))
	states.exportHTML(path.filepath('marvels_states.html'),
		title='MARVELS Proxy States',diagram='marvels.png')