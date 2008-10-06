"""
MARVELS use cases of the SDSS-3 Operations Software Design

A description of the MARVELS use cases of the SDSS-3 operations software
design. Running this file will generate an HTML page documenting the use
cases defined here.
"""

## @package tops.sdss3.design.marvels_cases
# MARVELS use cases of the SDSS-3 Operations Software Design
#
# @author David Kirkby, dkirkby@uci.edu
# @date Created 26-Jun-2008
#
# This project is hosted at sdss3.org and tops.googlecode.com

from tops.core.design.use_cases import *

cases = UseCases('MARVELS Operations',
	Scenario('MARVELS Observing',
		Do('Afternoon Checkouts'),
		Do('Begin Night Startup'),
		Repeat('Radial Velocity Exposures with One Cartridge'),
		Do('Preselection Exposure Sequence'),
		Do('End Night Shutdown'),
		Alternate('Control Computer not Responding'),
		Alternate('Fiber Plugged to Wrong Star'),
		Alternate('Fiber Dropped Out of its Hole'),
		Alternate('Mountain Intranet Failure'),
		Alternate('Internet Link to Outside World Fails'),
		Alternate('Moutain Sitewide Power Failure'),
		Alternate('Instrument Room Climate Control Failure'),
		Alternate('Hard Disk Failure'),
		Alternate('Minor Earthquake During Exposure'),
		Alternate('Failure of Component within Enclosure'),
		Alternate('Failure of Instrument Environmental Controls'),
		Alternate('Failure of Module in Instrument Control Rack')
	),
	Scenario('Afternoon Checkouts',
		'''
		[Operator] initiates checks of previous night's data transfer and log info.
		[Application] reports results of running checks.
		[Operator] verifies plate plugging activities and plate availability (via software?)
		[Operator] connects MARVELS fibers to calibration box (via software?)
		[Operator] loads first radial velocity cartridge for the night.
		[Operator] launches MARVELS observing [application].
		[Operator] tells [application] to prepare for calibration images.
		[Application] checks that Fiber Source is Calibration Box (redundant).
		[Application] checks instrument and operations system health.
		[Application] takes dark image.
		[Operator] tells [application] to prepare for observing.
		[Application] checks SDSS spectrograph health.
		'''
	),
	Scenario('Begin Night Startup',
		Repeat('Tungsten Lamp Calibration with Iodine Cell and Interferometer Fringes',count=5),
		'''
		[Operator] requests QA checks of TIO images (advanced check on interferometer health).
		[Application] returns QA check results.
		[Operator] takes 5x spectra of tungsten lamp, ThAr arc lamp, with and without interferometer fringes.
		[Operator] connects fibers to first field on installed cartridge.
		[Operator] initiates flat field calibration for first field.
		[Application] checks that Fiber Source is Telescope  (redundant).
		[Application] Take 5 min. telescope flat lamp exposure to test for fibre dropping/bad connections.
		[Operator] connects fibers to second field on installed cartridge.
		[Operator] initiates flat field calibration for second field.
		[Application] checks that Fiber Source is Telescope (redundant).
		[Application] Take 5 min. telescope flat lamp exposure to test for fibre dropping/bad connections.
		[Operator] connects fibers to calbox.
		[Operator] initiates tungsten lamp calibrations with iodine cell and without interferometer fringes.
		[Application] checks that Fiber Source is Calibration Box (redundant).
		[Application] takes 5x spectra of tungsten lamp with iodine cell, without interferometer fringes.
		''',
		Repeat('Tungsten Lamp Calibration with Iodine Cell and Interferometer Fringes',count=5),
		Do('Tungsten Lamp Calibration with Iodine Cell and Interferometer Fringes'),
		'''
		Enclosure roll off (in paralell?).
		SDSS dewar filling (in parallel?).
		'''
	),
	Scenario('Tungsten Lamp Calibration with Iodine Cell and Interferometer Fringes',
		'''
		This would be useful to flesh out since it happens so often...
		''',
		Alternate('Calibration Light Burns Out')
	),
	Scenario('Radial Velocity Exposures with One Cartridge',
		'''
		[Operator] initiates new cartridge sequence.
		[Application] slews [telescope] to zenith via its [proxy].
		[Operator] installs next cartridge and informs [Application] when it is ready.
		''',
		Do('Tungsten Lamp Calibration with Iodine Cell and Interferometer Fringes'),		
		Repeat('Radial Velocity Exposure',count=2),
		Alternate('Bad Weather During Exposures')
	),
	Scenario('Bad Weather During Exposures',
		'''
		Weather [proxy] reports threatening clouds on weather map.
		[Application] pauses exposure if one is in progress and notifies [user].
		Application stows [telescope] via its [proxy].
		[User] connect fibers to calbox.
		[Application] removes [telescope] enclosure via its [proxy].
		''',
		Do('Tungsten Lamp Calibration with Iodine Cell and Interferometer Fringes')		
	),
	Scenario('Radial Velocity Exposure',
		'''
		[Operator] connects fibers to next field on installed cartridge.
		[Operator] initiates RV exposure (or should this happen automatically?)
		[Application] checks that Fiber Source is Telescope (redundant).
		[Application] slews [telescope] to the field and focuses [telescope].
		[Operator] sets exposure time and initiates exposure.
		[Application] waits for exposure to end automatically (under control of MARVELS timer)
		[Application] runs MARVELS-QA software to check for sufficient flux, etc, and presents results to [operator].
		[Operator] examines QA checks and enters exposure comment.
		[Operator] connects fibers to calbox.
		''',
		Do('Store Telescope Data in FITS Header'),
		Do('Tungsten Lamp Calibration with Iodine Cell and Interferometer Fringes')
	),
	Scenario('Store Telescope Data in FITS Header',
		'''
		[Application] logs the relevant [telescope] parameters to the [database] during the exposure.
		After the exposure, the [MARVELS] control computer queries the [database] for the [telescope]
		parameters at a specific time.
		'''
	),
	Scenario('Preselection Exposure Sequence',
		'''
		[Operator] initiates preselection exposure.
		[Application] slews [telescope] to zenith via its [proxy].
		[Operator] connects MARVELS_PRESELECTION cartridge to SDSS spectrograph.
		[Operator] initiates SDSS spectrograph precalibrations.
		[Application] runs SDSS spectrograph precalibrations.
		[Application] slews [telescope] to appropriate field and focuses [telescope] via its [proxy].
		[Operator] initiates preselection exposures (or should this happen automatically?)
		[Application] waits for exposure sequence to complete (under MARVELS control).
		Sequence consits of 15x 7sec. exposures and 5x 12sec. exposures.
		[Application] run SDSS spectrograph postcalibrations and presents results to [operator].
		[Application] Runs SDSS-QA software (son-of-spectro) and presents results to [operator]
		[Operator] examines results and enters exposure comment.
		'''
	),
	Scenario('End Night Shutdown',
		'''
		[Operator] initiates end of night shutdown sequence.
		[Application] stows [telescope] via its [proxy].
		[Application] fills (drains?) SDSS dewar.
		[Application] monitors transfer of all data from the night to the staging area on sdsshost2
		and reports any anomalies to the [operator].
		[Application] records end of night summary to its [log stream].
		[Operator] schedules plates for next night, possibly by running automated scheduling software on QA logs
		Close software for MARVELS Interface Server.
		[Application] initiates sdsshost2 apotransfer mirroring process to Science Archive Server, monitors
		its progress, and records any anomalies in its [log stream].
		'''
	),
	Scenario('Daytime Maintenance',
		'''
		[Instrument expert] controls MARVELS instrument via MARVELS dedicated GUI by putting the
		MARVELS [proxy] in its "MANUAL" state.
		MARVELS [device] is not available to [applications] until released by [instrument expert]
		(by putting MARVELS [proxy] in its "ACQUIRED" state).
		Should its parameters be readable during this time for monitoring and/or archiving?
		Are there routine daytime maintenance tasks that should be migrated to the central operations software?
		'''
	),
	Scenario('Daytime Sky Calibration',
		'''
		Normally done over lunch. [Application] monitors environmental parameters throughout the day.
		'''
	),
	Scenario('Inteferometer Delay Measurement',
		'''
		This will be monthly or less frequent and occur during daytime. There will be nothing to record
		during the calibration.
		'''
	),
	Scenario('CCD Flushing',
		'''
		This will occur every 3-6 months and involves opening the CCD enclosure and pumping for a few hours
		to remove the accumulated air. The [application] should log pressures (and flows?) to the
		[database] during this procedure.
		'''
	),
	Scenario('Calibration Light Burns Out',
		'''
		How does the [proxy] detect this condition? [Application] informs [user] and instructs them to
		replace lamp in calibration box. Calibration box is in instrument room.
		''',
		Do('Enter Instrument Room')
	),
	Scenario('Enter Instrument Room',
		'''
		[Operator] informs [application] that someone will be entering instrument room. [Application]
		logs this to a [log stream] and broadcasts message to all current [users]. [Application] notifies
		all relevant [proxies]. [Application] displays instructions to [user]. [Application] pauses or stops
		instrument operations that might be affected by vibrations or environmental changes in instrument room.
		Telescope operations are not affected.
		'''
	),
	Scenario('Control Computer not Responding',
		'''
		[Proxy] is continuously sending no-op commands to MARVELS control computer and detects a
		missing response. [Proxy] informs [application] via its [partition]. [Application] informs [user]
		and logs condition in a [log stream]. [Application] attemps to restore communications with control
		computer via [state chart] transitions through the MARVELS [proxy]. If this fails, [application]
		displays instructions on rebooting the control computer to [user]. [User] follows instructions.
		[Application] waits for control computer to come back online then resumes normal [proxy] communications.
		'''
	),
	Scenario('Fiber Plugged to Wrong Star',
		'''
		Brian says we won't learn this until at least 2 days after exposure was taken. Would it be possible
		(and helpful) to detect this during post-exposure data quality checks? Plate will need to be replugged
		and remapped, then scheduled for another exposure (always?)
		'''
	),
	Scenario('Fiber Dropped Out of its Hole'),
	Scenario('Mountain Intranet Failure'),
	Scenario('Internet Link to Outside World Fails'),
	Scenario('Moutain Sitewide Power Failure',
		'''
		Mountain is on generator power. How long will this last? How will operations software know
		this has happened? Does generator/UPS have a software interface? Priority is to maintain
		instrument room climate control, and environmental control of instrument enclosure and
		iodine reference cell. Should an explicit hardware checklist [application] be run after power
		is restored to check for hard disk failures, etc?
		''',
		Do('Wait for Instrument to Reach Environmental Equilibrium')
	),
	Scenario('Wait for Instrument to Reach Environmental Equilibrium',
		'''
		[Application] reads acceptable environmental ranges [config data]. [Application] monitors
		environmentals via MARVELS [proxy] and records values to a [log stream]. [Application] informs
		[user] of progress towards equilibrium.
		'''
	),
	Scenario('Instrument Room Climate Control Failure'),
	Scenario('Hard Disk Failure',
		'''
		[Application] detects that control computer is not responding or operating normally via
		its [proxy]. [Operator] may need to replace drive with an on-site spare and restore program
		and data files from a backup. If failed disk is redundant, [application] informs [system manager]
		that daytime service is needed and tries to continue.
		'''
	),
	Scenario('Minor Earthquake During Exposure',
		'''
		How will operations software know about this? Is there any onsite seismic monitoring? Any
		current exposure should be marked as suspect and followed by calibrations and QA checks.
		'''
	),
	Scenario('Failure of Component within Enclosure'),
	Scenario('Failure of Instrument Environmental Controls'),
	Scenario('Failure of Module in Instrument Control Rack')
)

if __name__ == '__main__':
	import path
	from tops.sdss3.design.model import model
	cases.exportHTML(path.filepath('marvels_cases.html'),model=model,
		title='MARVELS Operations Use Cases',stylesheet='cases.css')