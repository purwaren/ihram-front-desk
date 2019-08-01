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
	# TODO: Calculate trx and print receipt

	# Update reservation status to "FINISH"
	reservation_id_list = json.loads(reservation_id_list)

	for reservation_id in reservation_id_list:
		reservation = frappe.get_doc('Reservation', reservation_id)
		reservation.status = "Finish"
		reservation.save()

	# TODO: Update room_status dari hotel_room menjadi "Vacant Dirty"
	
	# TODO: Update status dari hotel_room menjadi "OO"
