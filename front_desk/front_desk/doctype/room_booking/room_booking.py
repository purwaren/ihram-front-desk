# -*- coding: utf-8 -*-
# Copyright (c) 2019, PMM and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from datetime import timedelta

class RoomBooking(Document):
	pass

@frappe.whitelist()
def manage_by_reservation(reservation_name):
	frappe.db.sql("UPDATE `tabRoom Booking` SET is_cancel=1 WHERE reference_type='Reservation' AND reference_name=%s", (reservation_name))

	reservation_detail_list = frappe.db.get_list('Reservation Detail', 
		filters={
			'parent': reservation_name
		},
		fields=['name', 'expected_arrival', 'expected_departure', 'room_id']
	)
	for reservation_detail in reservation_detail_list:
		while reservation_detail.expected_arrival < reservation_detail.expected_departure:
			room_booking_name = frappe.db.get_value('Room Booking', 
				{'reference_type':'Reservation', 'reference_name':reservation_name, 'date':reservation_detail.expected_arrival, 'room_id':reservation_detail.room_id}, 
				['name']
			)

			if room_booking_name is None:
				doc = frappe.new_doc('Room Booking')

				doc.date = reservation_detail.expected_arrival
				doc.room_id = reservation_detail.room_id
				doc.availability = 'RS'
				doc.reference_type = 'Reservation'
				doc.reference_name = reservation_name
				doc.note = ''
				doc.is_cancel = 0
				
				doc.insert()
			else:
				frappe.db.set_value('Room Booking', room_booking_name, 'is_cancel', 0)
			
			reservation_detail.expected_arrival = reservation_detail.expected_arrival + timedelta(days=1)