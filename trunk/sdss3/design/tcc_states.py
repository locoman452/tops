"""
TCC operations software state chart specification

A description of the Telescope Control Computer (TCC) operating states
visible to the SDSS-3 operations software. Running this file will
generate an HTML page documenting the state chart defined here.
"""

## @package tops.sdss3.design.tcc_states
# TCC operations software state chart specification
#
# @author David Kirkby, dkirkby@uci.edu
# @date Created 16-Jul-2008
#
# This project is hosted at sdss3.org and tops.googlecode.com

from tops.core.utility.state_chart import *

states = StateChart('TELESCOPE_CONTROL_COMPUTER -> LOGGING_IN',
	State('LOGGING_IN',
		"""
		Attempting to log in to the TCC.
		""",
		On('(login successful)').goto('LOGGED_IN')
	),
	State('LOGGED_IN -> INITIALIZING',
		"""
		Logged in to the TCC.
		""",
		State('INITIALIZING',
			"""
			Attempting to determine if the TCC software is running.
			""",
			On('(software running)').goto('DISCONNECTED'),
			On('(software not running)').goto('STOPPED')
		),
		State('STOPPED',
			"""
			The TCC software is not running but can be started.
			""",
			On('start').goto('STARTING')
		),
		State('STARTING',
			"""
			Starting the TCC software and should be done soon. The TCC
			software is in a fragile state and any interactions from
			another user will likely collide and require a restart.
			""",
			On('(start successful)').goto('DISCONNECTED')
		),
		State('DISCONNECTED',
			"""
			The TCC software is running but we do not have an open
			command interpreter.
			""",
			On('connect').goto('CONNECTED'),
			On('stop').goto('STOPPED')
		),
		State('CONNECTED -> MULTI_USER',
			"""
			Running a TCC command interpreter. Other command
			interpreters may also be running and will need to be stopped
			before the TCC can be used to control the telescope.
			""",
			On('disconnect').goto('DISCONNECTED'),
			State('MULTI_USER',
				"""
				Possibly sharing the TCC software with other users. TCC
				keywords may be read but not changed. No TCC commands
				can be issued.
				""",
				On('(no other users)').goto('SINGLE_USER')
			),
			State('SINGLE_USER -> IDLE',
				"""
				In exclusive control of the TCC software. TCC keywords
				can be changed and TCC commands can be issued.
				""",
				State('IDLE',
					"""
					Ready for tracking. It is now safe to make the TCC
					software available to other users. The secondary
					mirror cannot be focused now.
					""",
					On('share').goto('MULTI_USER'),
					On('start tracking').goto('TRACKING')
				),
				State('TRACKING -> GUIDE_OFF',
					"""
					The telescope is tracking and can be focused and guided.
					""",
					State('GUIDE_OFF',
						"""
						Tracking without active guiding.
						""",
						On('start guiding').goto('GUIDE_ON')
					),
					State('GUIDE_ON',
						"""
						Tracking with active guiding.
						""",
						On('stop guiding').goto('GUIDE_OFF'),
						On('reset tracking').goto('GUIDE_OFF')
					),
					On('stop tracking').goto('IDLE')
				)
			)
		)
	)
)

if __name__ == '__main__':
	import path
	states.exportGraph(path.filepath('tcc_states.dot'))
	states.exportHTML(path.filepath('tcc_states.html'),title='TCC Proxy States',diagram='tcc.png')