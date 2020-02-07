# -*- coding: utf-8 -*-
# Copyright (c) 2020, PMM and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import datetime
from frappe.model.document import Document

class DayendClose(Document):
	pass

@frappe.whitelist()
def is_there_open_dayend_close():
	if frappe.get_all('Dayend Close', {'is_closed': 0}):
		return 1
	else:
		return 2

def fetch_problematic_reservation(audit_date):
	reservation_to_returned = []

	reservation_list = frappe.get_all('Reservation', {'status': 'Reserved'})
	for reservation in reservation_list:
		keys = ['reservation_id', 'description']
		problematic_reservation = dict.fromkeys(keys, None)
		reservation_detail_list = frappe.get_all('Reservation Detail', filters={'parent': reservation.name}, fields=['*'])
		for rd_item in reservation_detail_list:
			if rd_item.expected_arrival == audit_date:
				problematic_reservation['reservation_id'] = reservation.name
				problematic_reservation['description'] = 'Must Check In Today'
				reservation_to_returned.append(problematic_reservation)

	return reservation_to_returned

def fetch_problematic_room_stay(audit_date):
	room_stay_to_returned = []

	room_stay_list = frappe.get_all('Room Stay', filters={'status': 'Checked In'}, fields=['*'])
	for room_stay in room_stay_list:
		keys = ['room_stay_id', 'description']
		problematic_room_stay = dict.fromkeys(keys, None)
		if room_stay.departure.date() == audit_date:
			problematic_room_stay['room_stay_id'] = room_stay.name
			problematic_room_stay['description'] = 'Must Check Out Today'
			room_stay_to_returned.append(problematic_room_stay)

	return  room_stay_to_returned

@frappe.whitelist()
def precheck_dayend_close(audit_date):
	audit_date_object = datetime.datetime.strptime(audit_date, '%Y-%m-%d').date()
	return fetch_problematic_reservation(audit_date_object), fetch_problematic_room_stay(audit_date_object)

