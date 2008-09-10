"""
Manages the message formats used for distributed archiving

Header records define the numeric data that will be archived once per
session. Update records send the corresponding numeric values with a
timestamp.
"""

## @package tops.core.network.archiving.record
# Manages the message formats used for distributed archiving
#
# @author David Kirkby, dkirkby@uci.edu
# @date Created 22-Aug-2008
#
# This project is hosted at http://tops.googlecode.com/

from math import floor

from archiving_pb2 import Update

class ArchiveRecord(object):
	
	# maintain a counter to provide IDs that are unique within one client session
	id_counter = 0
	
	def __init__(self,name,fields):
		self.name = name
		# take the next counter ID (starting with one)
		self.id_counter += 1
		self.id = self.id_counter
		# initialize our arrays and index lookup hash
		self.indexof = { }
		self.names = [ ]
		self.types = [ ]
		self.values = [ ]
		for (field_name,value_type) in fields:
			self.indexof[field_name] = len(self.names)
			self.names.append(field_name)
			self.types.append(value_type)
			self.values.append(None)

	def appendToHeader(self,hdr):
		r = hdr.records.add()
		r.record_id = self.id
		r.record_name = self.name
		for index in xrange(len(self.names)):
			f = r.fields.add()
			f.field_name = self.names[index]
			vtype = self.types[index]
			f.value_type = vtype.__module__ + '.' + vtype.__name__
			# list any labels associated with this type
			try:
				for label in vtype.labels:
					f.labels.append(label)
			except AttributeError:
				pass
		
	def getUpdate(self,elapsed,fields):
		u = Update()
		u.record_id = self.id
		if elapsed.days:
			u.elapsed_days = elapsed.days
		u.elapsed_seconds = elapsed.seconds
		if elapsed.microseconds:
			# range is 0-999
			u.elapsed_millisecs = int(floor(1e-3*elapsed.microseconds))
		for (field_name,field_value) in fields.iteritems():
			index = self.indexof[field_name]
			self.values[index] = self.types[index](field_value)			
		for value in self.values:
			value.pack(u.values.add())
		return u


import unittest

class RecordTests(unittest.TestCase):	

	import tops.core.utility.data as data
	from archiving_pb2 import Header

 	class truefalse(data.enumerated):
		labels = ('true','false')
		
	def test00_Record(self):
		record = ArchiveRecord("test",[
			("boolean",self.truefalse),
			("vector.x",self.data.double),
			("vector.y",self.data.double),
			("vector.z",self.data.double)
		])
		hdr = self.Header()
		record.appendToHeader(hdr)
		self.assertEqual(len(hdr.records),1)
		self.assertEqual(len(hdr.records[0].fields),4)
		self.assertEqual(hdr.records[0].fields[0].field_name,'boolean')
		self.assertEqual(hdr.records[0].fields[0].labels[0],'true')
		self.assertEqual(hdr.records[0].fields[2].value_type,'tops.core.utility.data.double')
		class elapsed(object):
			days = 0
			seconds = 123
			microseconds = 0
		update = record.getUpdate(elapsed,{
			'boolean': 'false',
			'vector.x': -1.23,
			'vector.y': 0,
			'vector.z': +9.87
		})
		self.assertEqual(len(update.values),4)
		self.assertEqual(update.values[0].unsigned,self.truefalse._values['false'])
		self.assertEqual(update.values[1].double,-1.23)

if __name__ == "__main__":
	unittest.main()
	