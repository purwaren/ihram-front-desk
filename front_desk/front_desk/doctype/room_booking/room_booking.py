# -*- coding: utf-8 -*-
# Copyright (c) 2019, PMM and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from datetime import datetime
from datetime import timedelta
import json

class RoomBooking(Document):
	pass

@frappe.whitelist()
def update_by_reservation(reservation_name):
	status = frappe.db.get_value('Reservation', reservation_name, 'status')

	reservation_detail_list = frappe.db.get_all('Reservation Detail', 
		filters={
			'parent': reservation_name
		},
		fields=['name', 'expected_arrival', 'expected_departure', 'room_id']
	)

	room_stay_list = frappe.db.get_all('Room Stay', 
		filters={
			'parent': reservation_name
		},
		fields=['name', 'arrival', 'departure', 'room_id']
	)

	if status == 'Cancel':
		for reservation_detail in reservation_detail_list:
			frappe.db.sql('UPDATE `tabRoom Booking` SET status="Canceled" WHERE reference_type="Reservation Detail" AND reference_name=%s', (reservation_detail.name))
	elif status == 'Finish':
		for reservation_detail in reservation_detail_list:
			frappe.db.sql('UPDATE `tabRoom Booking` SET status="Finished" WHERE reference_type="Reservation Detail" AND reference_name=%s', (reservation_detail.name))
	else:
		for reservation_detail in reservation_detail_list:
			room_booking_name = frappe.db.get_value('Room Booking', 
				{'reference_type':'Reservation Detail', 'reference_name':reservation_detail.name}, 
				['name']
			)

			if room_booking_name is None:
				doc = frappe.new_doc('Room Booking')

				doc.start = reservation_detail.expected_arrival
				doc.end = reservation_detail.expected_departure
				doc.room_id = reservation_detail.room_id
				doc.room_availability = 'RS'
				doc.note = ''
				doc.reference_type = 'Reservation Detail'
				doc.reference_name = reservation_detail.name
				doc.status = 'Booked'
				
				doc.insert()
			else:
				stayed = False

				for room_stay in room_stay_list:
					if reservation_detail.room_id == room_stay.room_id and reservation_detail.expected_arrival < room_stay.departure.date():
						frappe.db.update('Room Booking', room_booking_name, 'status', 'Stayed')
						stayed = True
						break
				
				if not stayed:
					frappe.db.sql('UPDATE `tabRoom Booking` SET start=%s, end=%s, room_id=%s, room_availability="RS", note="", status="Booked" WHERE name=%s', (reservation_detail.expected_arrival, reservation_detail.expected_departure, reservation_detail.room_id, room_booking_name))

@frappe.whitelist()
def cancel_by_reservation(reservation_detail_list):
	reservation_detail_list = json.loads(reservation_detail_list)
	for reservation_detail in reservation_detail_list:
		frappe.db.sql('UPDATE `tabRoom Booking` SET status="Canceled" WHERE reference_type="Reservation Detail" AND reference_name=%s', (reservation_detail['name']))