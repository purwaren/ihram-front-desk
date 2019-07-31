# -*- coding: utf-8 -*-
# Copyright (c) 2019, PMM and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import json
import frappe
from frappe.model.document import Document

class Folio(Document):
	pass

def create_folio(reservation_id_list):
	reservation_id_list = json.loads(reservation_id_list)

	for reservation_id in reservation_id_list:
		if not frappe.db.exists({'doctype': 'Folio', 'reservation_id': reservation_id}):
			reservation = frappe.get_doc('Reservation', reservation_id)

			doc = frappe.new_doc('Folio')
			doc.customer_id = reservation.customer_id
			doc.reservation_id = reservation_id
			doc.insert()

@frappe.whitelist()
def get_folio_name(reservation_id):
	return frappe.db.get_list('Folio',
		filters={
			'reservation_id': reservation_id
		}
	)[0].name