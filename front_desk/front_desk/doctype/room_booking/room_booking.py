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

@frappe.whitelist()
def get_empty_array(doctype, txt, searchfield, start, page_len, filters):
	return []

def get_room_book_list(filters):
	room_book_list = list(frappe.db.sql("SELECT rb.room_id FROM `tabRoom Booking` AS rb LEFT JOIN `tabReservation Detail` AS rd ON rb.reference_name = rd.name WHERE (rd.parent != %s) AND (rb.status =	'Booked') AND (rb.start != rb.end) AND ((%s >= rb.start AND %s < rb.end) OR (%s > rb.start AND %s <= rb.end) OR (%s < rb.start AND %s > rb.end))", (filters.get('parent'), filters.get('start'), filters.get('start'), filters.get('end'), filters.get('end'), filters.get('start'), filters.get('end'))))
	room_book_list.extend(list(frappe.db.sql("SELECT rs.room_id FROM `tabRoom Stay` AS rs LEFT JOIN `tabReservation` AS r ON rs.reservation_id = r.name WHERE (rs.parent != %s) AND (r.status = 'Confirmed' OR r.status = 'In House') AND (CONVERT(rs.arrival, DATE) != CONVERT(rs.departure, DATE)) AND ((%s >= CONVERT(rs.arrival, DATE) AND %s < CONVERT(rs.departure, DATE)) OR (%s > CONVERT(rs.arrival, DATE) AND %s <= CONVERT(rs.departure, DATE)) OR (%s < CONVERT(rs.arrival, DATE) AND %s > CONVERT(rs.departure, DATE)))", (filters.get('parent'), filters.get('start'), filters.get('start'), filters.get('end'), filters.get('end'), filters.get('start'), filters.get('end')))))

	return room_book_list

@frappe.whitelist()
def get_room_available(doctype, txt, searchfield, start, page_len, filters):
	room_list = []

	if filters.get('start') and filters.get('end'):
		if filters.get('allow_smoke'):
			if filters.get('room_type'):
				if filters.get('bed_type'):
					room_list = list(frappe.db.sql("select name, room_type, bed_type, allow_smoke from `tabHotel Room` where allow_smoke = %s and room_type = %s and bed_type = %s", (filters.get('allow_smoke'), filters.get('room_type'), filters.get('bed_type'))))
				else:
					room_list = list(frappe.db.sql("select name, room_type, bed_type, allow_smoke from `tabHotel Room` where allow_smoke = %s and room_type = %s", (filters.get('allow_smoke'), filters.get('room_type'))))
			else:
				room_list = list(frappe.db.sql("select name, room_type, bed_type, allow_smoke from `tabHotel Room` where allow_smoke = %s", (filters.get('allow_smoke'))))
		else:
			room_list = list(frappe.db.sql("select name, room_type, bed_type, allow_smoke from `tabHotel Room`"))
	
	room_book_list = get_room_book_list(filters)

	for room_book in room_book_list:
		for i in range(len(room_list)):
			if room_list[i][0] == room_book[0]:
				del room_list[i]
				break

	return room_list

@frappe.whitelist()
def get_room_type_available(doctype, txt, searchfield, start, page_len, filters):
	room_list = get_room_available(doctype, txt, searchfield, start, page_len, filters)

	tmp = []
	for room in room_list:
		tmp.append(room[1])

	tmp = list(set(tmp))

	room_type_list = []
	for t in tmp:
		room_type_list.append([t])

	return room_type_list

@frappe.whitelist()
def get_bed_type_available(doctype, txt, searchfield, start, page_len, filters):
	room_list = get_room_available(doctype, txt, searchfield, start, page_len, filters)

	tmp = []
	for room in room_list:
		if room[1] == filters.get('room_type'):
			tmp.append(room[2])

	tmp = list(set(tmp))

	bed_type_list = []
	for t in tmp:
		bed_type_list.append([t])

	return bed_type_list

@frappe.whitelist()
def is_available(room_id, start, end):
	result = frappe.db.sql('SELECT room_id FROM `tabRoom Booking` WHERE %s = room_id AND status = "Booked" AND (start != end) AND ((%s >= start AND %s < end) OR (%s > start AND %s <= end) OR (%s < start AND %s > end))', (room_id, start, start, end, end, start, end))
	if result:
		return False
	else:
		result = frappe.db.sql("SELECT rs.room_id FROM `tabRoom Stay` AS rs LEFT JOIN `tabReservation` AS r ON rs.reservation_id = r.name WHERE %s = rs.room_id AND (r.status = 'Confirmed' OR r.status = 'In House') AND (CONVERT(rs.arrival, DATE) != CONVERT(rs.departure, DATE)) AND ((%s >= CONVERT(rs.arrival, DATE) AND %s < CONVERT(rs.departure, DATE)) OR (%s > CONVERT(rs.arrival, DATE) AND %s <= CONVERT(rs.departure, DATE)) OR (%s < CONVERT(rs.arrival, DATE) AND %s > CONVERT(rs.departure, DATE)))", (room_id, start, start, end, end, start, end))
		if result:
			return False
		else:
			return True