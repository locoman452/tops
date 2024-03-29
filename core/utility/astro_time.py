"""
Astronomical date and time utilities

Enhancements to the standard datetime package for astronomical applications.
"""

## @package tops.core.utility.astro_time
# Astronomical date and time utilities
#
# @author David Kirkby, dkirkby@uci.edu
# @date Created 29-Jul-2008
#
# This project is hosted at sdss3.org and tops.googlecode.com

from datetime import tzinfo,timedelta,datetime
from math import floor

class AstroTimeException(Exception):
	pass

class AstroTime(datetime):
	"""
	Enhanced version of datetime suitable for astronomical applications.
	
	Wraps the datetime class to add support for leap-second adjustments
	specified via the timezone and conversion to/from Modified Julian
	Date formats.
	"""
	# a datetime whose MJD is exactly 50000.
	mjdEpoch = datetime(1995,10,10)
	def __new__(cls,*args,**kargs):
		"""
		Adds a new types of constructors for up-casting from a datetime object.
		
		AstroTime(datetime=dt)
		AstroTime(datetime=dt,deltasecs=+33)
		"""
		if (len(args) == 0 and 'datetime' in kargs and
			(len(kargs) == 1 or (len(kargs) == 2 and 'deltasecs' in kargs))):
			if not isinstance(kargs['datetime'],datetime):
				raise AstroTimeException('expect datetime instance')
			deltasecs = kargs['deltasecs'] if 'deltasecs' in kargs else 0
			dt = kargs['datetime'] + timedelta(seconds=deltasecs)
			return datetime.__new__(cls,dt.year,dt.month,dt.day,
				dt.hour,dt.minute,dt.second,dt.microsecond,dt.tzinfo)
		else:
			return datetime.__new__(cls,*args,**kargs)
	@staticmethod
	def now(tz=None):
		"""Identical to datetime.now() but returns an AstroTime"""
		dt = AstroTime(datetime=datetime.now(tz))
		delta = dt.__leapseconds(tz)
		return AstroTime(datetime=dt,deltasecs=delta)
	@staticmethod
	def fromtimestamp(timestamp,tz=None):
		"""Identical to datetime.fromtimestamp() but returns an AstroTime"""
		dt = AstroTime(datetime=datetime.fromtimestamp(timestamp,tz))
		delta = dt.__leapseconds(tz)
		return AstroTime(datetime=dt,deltasecs=delta)
	@staticmethod
	def combine(date,time):
		"""Identical to datetime.combine() but returns an AstroTime"""
		return AstroTime(datetime=datetime.combine(date,time))
	def __leapseconds(self,tz,default=0):
		"""Returns the leap-second adjustment of tz or default if none is available"""
		result = default
		try:
			result = tz.leapseconds(self)
		except AttributeError:
			pass
		return result
	def utcoffset(self):
		"""Returns our offset from UTC, including any leap-second adjustments."""
		return datetime.utcoffset(self) + timedelta(seconds=self.__leapseconds(self.tzinfo))
	def utctimetuple(self):
		dt = self - timedelta(seconds=self.__leapseconds(self.tzinfo))
		return dt.utctimetuple()
	def astimezone(self,tz):
		"""
		Identical to datetime.astimezone() but returns an AstroTime.
		
		Performs leap-second adjustments if necessary.
		"""
		delta = self.__leapseconds(tz) - self.__leapseconds(self.tzinfo)
		return AstroTime(datetime=datetime.astimezone(self,tz),deltasecs=delta)
	def timetz(self):
		delta = self.__leapseconds(self.tzinfo,0)
		if not delta == 0:
			raise AstroTimeException('time.time does not support leap seconds')
		return datetime.timetz(self)
	def MJD(self):
		"""Returns the Modified Julian Date corresponding to our date and time."""
		if self.year <= 0:
			raise AstroTimeException("MJD calculations not supported for BC dates")
		(y,m,d) = (self.year,self.month,self.day)
		jd = (367*y - floor(7*(y + floor((m+9)/12))/4) -
			floor(3*(floor((y+(m-9)/7)/100)+1)/4) + floor(275*m/9) + d + 1721028.5)
		mjd = jd - 2400000.5
		(h,m,s,us) = (self.hour,self.minute,self.second,self.microsecond)
		mjd += (h + (m + (s + us/1000000.)/60.)/60.)/24.
		return mjd
	@staticmethod
	def fromMJD(mjd,tz=None):
		"""
		Returns an AstroTime initialized from an MJD value.
		
		No timezone or leap-second adjustments are made since the MJD
		value is assumed to already be in the specified time zone.
		"""
		dt = AstroTime.mjdEpoch.replace(tzinfo=tz) + timedelta(days = mjd - 50000.)
		return AstroTime(datetime=dt)
	def __str__(self):
		formatted = datetime.__str__(self)
		delta = self.__leapseconds(self.tzinfo,None)
		if delta is not None:
			formatted += '%+03d' % self.tzinfo.leapseconds(self)
		formatted += ' MJD %.6f' % self.MJD()
		if self.tzname() is not None:
			formatted += ' %s' % self.tzname()
		return formatted
	def __repr__(self):
		return datetime.__repr__(self).replace('datetime.datetime',self.__class__.__name__)
		
ZERO = timedelta(0)

class CoordinatedUniversalTime(tzinfo):
	"""
	A timezone class for tagging a datetime as being in UTC.
	"""
	def utcoffset(self,dt):
		return ZERO
	def dst(self,dt):
		return ZERO
	def tzname(self,dt):
		return 'UTC'
	def leapseconds(self,dt):
		return int(0)

UTC = CoordinatedUniversalTime()

class InternationalAtomicTime(CoordinatedUniversalTime):
	"""
	A timezone class for tagging a datetime as being in TAI and converting to/from TAI.
	"""
	def tzname(self,dt):
		return 'TAI'
	def leapseconds(self,dt):
		if dt.year < 2006:
			raise AstroTimeException("Leap seconds not tabulated before 2006")
		return int(+33)

TAI = InternationalAtomicTime()

import unittest

class AstroTimeTests(unittest.TestCase):
	def test00_AstroTime(self):
		"""Special AstroTime constructors"""
		dt = datetime.now()
		dt1 = AstroTime(datetime=dt)
		dt2 = AstroTime(datetime=dt,deltasecs=+10)
		self.assertEqual(dt2 - dt1,timedelta(seconds=+10))
		dt3 = AstroTime(datetime=dt,deltasecs=-10)
		self.assertEqual(dt3 - dt1,timedelta(seconds=-10))
		self.assertRaises(AstroTimeException,lambda: AstroTime(datetime='invalid'))
		self.assertRaises(TypeError,lambda: AstroTime(deltasecs=0))
	def test01_AstroTime(self):
		"""AstroTime constructor tests without timezone"""
		args = (2008,7,24,1,2,3,4)
		dt1 = datetime(*args)
		dt2 = AstroTime(*args)
		self.assertEqual(dt1.timetuple(),dt2.timetuple())
		self.assertEqual(dt1.utctimetuple(),dt2.utctimetuple())
		self.assertNotEqual(str(dt1),str(dt2))
		self.assertNotEqual(repr(dt1),repr(dt2))
	def test02_AstroTime(self):
		"""AstroTime constructor tests using UTC"""
		args = (2008,7,24,1,2,3,4,UTC)
		dt1 = datetime(*args)
		dt2 = AstroTime(*args)
		self.assertEqual(dt1.timetuple(),dt2.timetuple())
		self.assertEqual(dt1.utctimetuple(),dt2.utctimetuple())
		self.assertNotEqual(str(dt1),str(dt2))
		self.assertNotEqual(repr(dt1),repr(dt2))
	def test03_AstroTime(self):
		"""AstroTime constructor tests using TAI"""
		args = (2008,7,24,1,2,3,4,TAI)
		dt1 = datetime(*args)
		dt2 = AstroTime(*args)
		self.assertEqual(dt1.timetuple(),dt2.timetuple())
		self.assertNotEqual(dt1.utctimetuple(),dt2.utctimetuple())
		self.assertNotEqual(str(dt1),str(dt2))
		self.assertNotEqual(repr(dt1),repr(dt2))
	def test04_AstroTime(self):
		"""AstroTime leap second adjustments"""
		utc = AstroTime(2008,7,24,1,2,3,4,UTC)
		tai = utc.astimezone(TAI)
		offset = timedelta(seconds=+33)
		self.assertEqual(utc.utcoffset(),ZERO)
		self.assertEqual(tai.utcoffset(),offset)
		self.assertEqual(utc.utctimetuple(),tai.utctimetuple())
		self.assertNotEqual(utc.timetuple(),tai.timetuple())
		self.assertEqual(utc.timetuple(),tai.astimezone(UTC).timetuple())
		self.assertEqual(tai-utc,offset)
	def test05_AstroTime(self):
		"""AstroTime static methods"""
		dt1 = AstroTime.now(UTC)
		dt2 = AstroTime.now(TAI)
		self.assert_(dt2 - dt1 >= timedelta(seconds=+33))
		ts = 1234567890
		dt1 = AstroTime.fromtimestamp(ts,UTC)
		dt2 = AstroTime.fromtimestamp(ts,TAI)
		self.assertEqual(dt1.utctimetuple(),dt2.utctimetuple())
		self.assertNotEqual(dt1.timetuple(),dt2.timetuple())
	def test06_AstroTime(self):
		"""AstroTime MJD calculations"""
		dt1 = AstroTime(2008,7,24,12,tzinfo=TAI)
		self.assertEqual(dt1.MJD(),54671.5)
		dt2 = AstroTime.fromMJD(dt1.MJD(),TAI)
		self.assertEqual(dt1.timetuple(),dt2.timetuple())
		dt3 = AstroTime.fromMJD(dt1.MJD(),UTC)
		self.assertEqual(dt1.timetuple(),dt3.timetuple())
		self.assertNotEqual(dt1.utctimetuple(),dt3.utctimetuple())

if __name__ == '__main__':
	unittest.main()