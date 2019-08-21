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
	for reservation_id in reservation_id_list:
		if not frappe.db.exists({'doctype': 'Folio', 'reservation_id': reservation_id}):
			reservation = frappe.get_doc('Reservation', reservation_id)

			doc = frappe.new_doc('Folio')
			doc.customer_id = reservation.customer_id
			doc.reservation_id = reservation_id
			doc.insert()

def get_folio_name(reservation_id):
	return frappe.db.get_list('Folio',
		filters={
			'reservation_id': reservation_id
		}
	)[0].name

@frappe.whitelist()
def get_total_folio_transaction(reservation_id):
	folio = frappe.get_doc('Folio', {"reservation_id": reservation_id})
	folio_id = folio.name
	folio_transaction_list = frappe.get_all('Folio Transaction',
											filters={
												"folio_id": folio_id,
												"flag": "Credit"
											},
											fields=["amount"]
											)
	total = 0
	for item in folio_transaction_list:
		total = total + item.amount

	return total

@frappe.whitelist()
def copy_trx_from_sales_invoice(reservation_id):
	folio_id = frappe.get_doc('Folio', {"reservation_id": reservation_id}).name
	customer_id = frappe.get_doc('Reservation', reservation_id).customer_id
	pos_profile_list = frappe.get_all('POS Profile', filters={"disabled": 0})

	# TODO:
	# for each sales_invoice in all_sales_invoice
	# 	copy needed details from sales_invoice and create new folio transaction with folio_id = folio_id
	# 	?? create new payment entry related to  sales_invoice
	#
