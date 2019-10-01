# -*- coding: utf-8 -*-
# Copyright (c) 2019, PMM and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import front_desk.front_desk.doctype.room_stay.room_stay as room_stay

class MoveRoom(Document):
	pass

@frappe.whitelist()
def process_move_room(initial_room_stay_name):
	move_room_name = frappe.db.get_value('Move Room', {'initial_room_stay':initial_room_stay_name}, ['name'])
	replacement_room_stay_name = room_stay.get_room_stay_name_by_parent(move_room_name, 'room_stay', 'Move Room')

	initial_room_stay = frappe.get_doc('Room Stay', initial_room_stay_name)
	replacement_room_stay = frappe.get_doc('Room Stay', replacement_room_stay_name)

	frappe.db.set_value('Hotel Room', initial_room_stay.room_id, 'room_status', 'Vacant Dirty')
	frappe.db.set_value('Hotel Room', replacement_room_stay.room_id, 'room_status', 'Occupied Clean')

	initial_room_stay.departure = replacement_room_stay.arrival
	# calculate total bill amount karena departure berubah
	initial_room_stay.total_bill_amount = room_stay.calculate_room_stay_bill(str(initial_room_stay.arrival), str(initial_room_stay.departure), initial_room_stay_name)
	initial_room_stay.save()

	replacement_room_stay.parent = replacement_room_stay.reservation_id
	replacement_room_stay.parenttype = 'Reservation'
	replacement_room_stay.idx = initial_room_stay.idx
	replacement_room_stay.save()

	frappe.db.sql('UPDATE `tabMove Room` SET replacement_room_stay=%s WHERE name=%s', (replacement_room_stay_name, move_room_name))