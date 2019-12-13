# -*- coding: utf-8 -*-
# Copyright (c) 2019, PMM and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import front_desk.front_desk.doctype.room_stay.room_stay as room_stay
import front_desk.front_desk.doctype.reservation.reservation as reservation

class MoveRoom(Document):
	pass

@frappe.whitelist()
def process_move_room(initial_room_stay_name):
	move_room_name = frappe.db.get_value('Move Room', {'initial_room_stay':initial_room_stay_name}, ['name'])
	is_guest_request = frappe.db.get_value('Move Room', {'initial_room_stay': initial_room_stay_name}, ['guest_request'])
	replacement_room_stay_name = room_stay.get_room_stay_name_by_parent(move_room_name, 'room_stay', 'Move Room')

	initial_room_stay = frappe.get_doc('Room Stay', initial_room_stay_name)
	old__initial_room_stay_bill_amount = initial_room_stay.total_bill_amount
	replacement_room_stay = frappe.get_doc('Room Stay', replacement_room_stay_name)

	frappe.db.set_value('Hotel Room', initial_room_stay.room_id, 'room_status', 'Vacant Dirty')
	frappe.db.set_value('Hotel Room', replacement_room_stay.room_id, 'room_status', 'Occupied Clean')

	initial_room_stay.departure = replacement_room_stay.arrival
	# calculate total bill amount karena departure berubah
	initial_room_stay.total_bill_amount = room_stay.calculate_room_stay_bill(str(initial_room_stay.arrival), str(initial_room_stay.departure), initial_room_stay.room_rate, initial_room_stay.discount_percentage, initial_room_stay.actual_weekday_rate, initial_room_stay.actual_weekend_rate)
	initial_room_stay.old_total_bill_amount = old__initial_room_stay_bill_amount
	initial_room_stay.save()

	# calculate new total bill if guest_request == 1
	if is_guest_request == 1:
		new_initial_room_stay_bill_amount = frappe.db.get_value('Room Stay', {'name':initial_room_stay_name}, ['total_bill_amount'])
		replacement_room_stay_bill_amount = frappe.db.get_value('Room Stay', {'name':replacement_room_stay_name}, ['total_bill_amount'])

		diff = replacement_room_stay_bill_amount + new_initial_room_stay_bill_amount - old__initial_room_stay_bill_amount

		if diff > 0:
			replacement_room_stay.room_bill_paid_id = None

	replacement_room_stay.parent = replacement_room_stay.reservation_id
	replacement_room_stay.parenttype = 'Reservation'
	replacement_room_stay.idx = initial_room_stay.idx
	replacement_room_stay.save()

	frappe.db.sql('UPDATE `tabMove Room` SET replacement_room_stay=%s WHERE name=%s', (replacement_room_stay_name, move_room_name))

	if is_guest_request == 1 and diff > 0:
		# trigger recalculate_room_bill_amount
		reservation.recalculate_room_bill_amount_after_guest_requested_move_room(initial_room_stay.reservation_id)

def fill_actual_room_rate(doc, method):
	room_stay = doc.get('room_stay')
	if len(room_stay) > 0:
		for rs_item in room_stay:
			if rs_item.override_rate == 0:
				rs_item.actual_weekday_rate = rs_item.weekday_rate
				rs_item.actual_weekend_rate = rs_item.weekend_rate
			else:
				if rs_item.actual_weekday_rate == 0 and rs_item.actual_weekend_rate == 0:
					rs_item.override_rate = 0
				if rs_item.actual_weekday_rate == 0:
					rs_item.actual_weekday_rate = rs_item.weekday_rate
				if rs_item.actual_weekend_rate == 0:
					rs_item.actual_weekend_rate = rs_item.weekend_rate
