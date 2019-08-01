# -*- coding: utf-8 -*-
# Copyright (c) 2019, PMM and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import json
import frappe
from frappe.model.document import Document
from front_desk.front_desk.doctype.room_stay.room_stay import create_room_stay
from front_desk.front_desk.doctype.folio.folio import create_folio

class Reservation(Document):
	pass

@frappe.whitelist()
def check_in(reservation_id_list):
	create_folio(reservation_id_list)
	return create_room_stay(reservation_id_list)

@frappe.whitelist()
def check_out(reservation_id_list):
	reservation_id_list = json.loads(reservation_id_list)
	# TODO: Calculate trx and print receipt


	for reservation_id in reservation_id_list:
		reservation = frappe.get_doc('Reservation', reservation_id)
		# Update reservation status to "FINISH"
		reservation.status = "Finish"
		reservation.save()

		room_stay = frappe.get_doc('Room Stay', {"reservation_id": reservation_id})
		hotel_room = frappe.get_doc('Hotel Room', room_stay.room_id)
		# Update room_status dari hotel_room menjadi "Vacant Dirty"
		hotel_room.room_status = "Vacant Dirty"
		# Update status dari hotel_room menjadi "OO"
		hotel_room.status = "OO"
		hotel_room.save()


