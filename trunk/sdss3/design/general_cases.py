"""
A Domain Model of the SDSS-3 Operations Software Design

A description of the actors and nouns of the SDSS-3 operations software
design, and the relationships between them. Running this file will
generate an HTML glossary and a domain-model graph. This file can also
be included as a module to provide a glossary for other design
documents.
"""

## @package tops.sdss3.design.general_cases
# A Domain Model of the SDSS-3 Operations Software Design
#
# @author David Kirkby, dkirkby@uci.edu
# @date Created 24-Jun-2008
#
# This project is hosted at http://tops.googlecode.com/

from tops.core.design.use_cases import *

cases = UseCases('SDSS3 Operations',
	Scenario('Multi-Instrument Spectroscopic Observing',
		Do('Start a User Session'),
		'''
		[Users]'s [agent] attempts to start the observing [application]. [Session] verifies that
		[user] is an authorized [operator]. [Operator] tells the [application] which [instruments]
		to use for observing.
		[Application] negotiates with [proxies] to form a [partition] for the requested [devices].
		[Application] monitors [device] health via their [proxies].
		''',
		Repeat('Operator Observes with One Plate'),
		'''
		[Operator] quits observing [application] and ends their [session].
		''',
		Alternate('Session is not Authorized to Run Application'),
		Alternate('Requested Device is not Available'),
		Alternate('Malicious User Attempts to Control Telescope'),
		Alternate('Application Crashes'),
		Alternate('Power Outage'),
		Alternate('Network Failure')
	),
	Scenario('Start a User Session',
		'''
		[User] provides user name and password via their [agent].
		[Session] manager compares these against values stored in user's [profile].
		[Session] manager establishes a new [session] and returns one-time credentials to user's [agent].
		[Session] manager records new session creation to a [log stream].
		''',
		Alternate('User Provides Invalid Account Info')
	),
	Scenario('User Provides Invalid Account Info',
		'''
		[Session] manager allows [user] to re-enter account info a limited number of times and either
		creates a new [session] or denies access to the user's [agent]. [Session] manager records failed
		login attempts to a [log stream].
		'''
	),
	Scenario('Session is not Authorized to Run Application',
		'''
		[Session] manager checks if [user]'s [profile] has necessary privilege. [Session] manager asks
		[user] to confirm asserting additional privilege via [agent]. [User] confirms.
		[Session] mamager attaches additional privilege to [session] and launches [application].
		'''
	),
	Scenario('Requested Device is not Available',
		'''
		[Application] determines which [partition] currently has [device]'s [proxy] allocated.
		[Application] tells [user] via [agent] that [device] is unavailable and why.
		[Application] checks if [session] has necessary privilege to remove [device] from its
		current [partition] (possibly interrupting the [application] that is using it). If not,
		[application] checks [user]'s profile to see if necessary privilege could be added to [session].
		[Application] asks [user] if they want to attempt to grab the [device] from its current [partition].
		'''
	),
	Scenario('Operator Observes with One Plate',
		'''
		[Application] continuously monitors environmental and [telescope] parameters and records
		significant changes to a [log stream].
		[Operator] identifies field to observe.
		[Application] slews [telescope] to field via [TCC] [proxy].
		[Application] coordinates pre-exposure calibrations
		(can some of these run in parallel for different instruments?)
		[Operator] checks pre-exposure calibrations, verifies exposure parameters and requests
		that exposures begin.
		[Application] begins exposures via [instrument] [proxies] and monitors exposure times.
		[Application] initiates tracking and guiding via the [TCC] [proxy].
		[Application] verifies that exposures have ended normally.
		[Application] coordinates post-exposure calibrations.
		[Operator] checks post-exposure calibrations and enters comments.
		[Application] records [operator] comments to a [log stream].
		[Application] slews [telescope] to zenith position using [TCC] [proxy].
		[Operator] tells [application] when new cartridge is loaded.
		''',
		Alternate('Device Fault During Exposure'),
		Alternate('Exposure Paused for Weather'),
		Alternate('Calibration Fails'),
		Alternate('TCC Not Responding'),
		Alternate('Guider not Locked onto Field'),
		Alternate('Telescope not Tracking Correctly')
	),
	Scenario('Device Fault During Exposure',
		'''
		[Proxy] detects that [device] is not behaving correctly and signals condition to [application].
		[Application] describes problem to [operator].
		''',
		Do('Instrument Debugging During Observing Night')
	),
	Scenario('Guider not Locked onto Field'),
	Scenario('Telescope not Tracking Correctly'),
	Scenario('Instrument Debugging During Observing Night',
		'''
		[Operator] attempts to identify and fix the problem via the [application].
		In case this is not possible, [application] removes faulty [device] from [partition] and may
		thus be prevented from continuing.
		[Operator] runs a pass-through [application] that provides direct message-level access to
		the [device] through a new [partition]. If the faulty [device] is recovered, it can be added
		back to the original [application]'s [partition], allowing it to resume.
		''',
		Alternate('Session is not Authorized to Run Application'),
		Alternate('Instrument No Longer Available for Observing')
	),
	Scenario('Instrument No Longer Available for Observing'),
	Scenario('TCC Not Responding',
		'''
		[Proxy] is sending no-op commands to [TCC] every 1-10 seconds and detects missing response.
		[Proxy] signals exception to [partition]. [Partition] forwards exception to [application].
		[Application] records fault to a [log stream] and notifies [user] via their [agent].
		[Application] offers user option to restart [TCC] software, reboot [TCC], or quit [application].
		[User] makes selection. If requested, [application] signals [proxy] to make
		appropriate [state chart] transistions to accomplish restart/reboot. If these are successful,
		[application] attempts to proceed.
		'''
	),
	Scenario('Exposure Paused for Weather'),
	Scenario('Calibration Fails'),
	Scenario('Single-Instrument Commissioning / Debugging',
		Do('Start a User Session'),
		'''
		[Instrument expert] launches debugging [application].
		[Instrument expert] selects [instrument] to debug and other [devices] to monitor
		(eg, [TCC], weather).
		[Instrument expert] executes commands from [application]'s [command dictionary], either
		interactively or via a script.
		[Instrument expert] specifies [device] parameters to monitor. [Application] obtains parameter values
		from [proxies] and displays them with realtime updates.
		[Instrument expert] exits debugging [application].
		''',
		Alternate('Session is not Authorized to Run Application'),
		Alternate('User Needs Help Running Application'),
		Alternate('Requested Device is not Available'),
		Alternate('Application Crashes')
	),
	Scenario('User Needs Help Running Application'),
	Scenario('Realtime Operations Monitoring',
		Do('Start a User Session'),
		'''
		[System manager] launches system monitor [application].
		[Application] retrieves list of current [users] from [session] manager.
		[Application] retrieves list of current [applications] from [application] manager.
		[Application] retrieves summary of [device] status from [proxies].
		[Application] displays [user], [application] and [device] info to [system manager].
		[System manager] and [user] chat via text messages.
		[System manager] broadcasts message to all active [users].
		[System manager] exits system monitor [application].
		''',
		Alternate('Session is not Authorized to Run Application'),
		Alternate('Application Crashes')
	),
	Scenario('Playback and Analysis of Earlier Observing',
		Do('Start a User Session'),
		'''
		[Scientist] launches playback application.
		[Scientist] selects observing period and [devices] of interest.
		[Application] retrieves a list of [log stream] and [config data] from the [database].
		[Application] displays list to [scientist]. [Scientist] selects information to review.
		[Application] displays selected information. [Device] data is displayed as a time series
		on a strip chart. [Scientist] filters log messages based on severity and [device].
		[Scientist] exits application.
		''',
		Alternate('Session is not Authorized to Run Application'),
		Alternate('Requested Device is not Available'),
		Alternate('Application Crashes')
	),
	Scenario('Tracking Time Usage in Different Activities',
		'''
		What activities need to be tracked? What time resolution is required? How should results be
		presented? This is a good example of a background [application] without any [user] [roles].
		'''
	),
	Scenario('Malicious User Attempts to Control Telescope'),
	Scenario('Application Crashes'),
	Scenario('Power Outage'),
	Scenario('Network Failure')
)

if __name__ == '__main__':
	cases.exportHTML('web/general-cases.html',model=tops.sdss3.design.model.model,
		title='General Operations Use Cases',stylesheet='cases.css')