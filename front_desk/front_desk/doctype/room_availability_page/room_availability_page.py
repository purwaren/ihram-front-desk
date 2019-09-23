# -*- coding: utf-8 -*-
# Copyright (c) 2019, PMM and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class RoomAvailabilityPage(Document):
	pass

@frappe.whitelist()
def get_room_availability(room_id, date):
	room_stay = frappe.db.sql('SELECT name FROM `tabRoom Stay` WHERE room_id=%s AND %s >= CONVERT(arrival, DATE) AND %s < CONVERT(departure, DATE)', (room_id, date, date))

	if len(room_stay) > 0:
		return 'RS'
	else:
		availability = frappe.db.sql('SELECT room_availability FROM `tabRoom Booking` WHERE status = "Booked" AND room_id = %s AND %s >= start AND %s < end', (room_id, date, date))
		
		if len(availability) > 0:
			return availability
		else:
			return ''