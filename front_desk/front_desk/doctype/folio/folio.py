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
def copy_all_trx_from_sales_invoice_to_folio():
	reservation_list = frappe.get_all('Reservation',
									  filters={
										'status': 'In House'
									},
									fields=["*"]
									)
	for reservation in reservation_list:
		copy_trx_from_sales_invoice_to_folio_transaction(reservation.name)

def copy_trx_from_sales_invoice_to_folio_transaction(reservation_id):
	folio_id = frappe.get_doc('Folio', {"reservation_id": reservation_id}).name
	customer_id = frappe.get_doc('Reservation', reservation_id).customer_id
	pos_profile_list = frappe.get_all('POS Profile', filters={"disabled": 0})

	# TODO:
	# for each sales_invoice in all_sales_invoice
	# 	copy needed details from sales_invoice and create new folio transaction with folio_id = folio_id
	# 	?? create new payment entry related to  sales_invoice
	#

	for pos_profile in pos_profile_list:
		if pos_profile:
			sales_invoice_list = frappe.get_all('Sales Invoice',
												filters={
													'customer_name': customer_id,
													'pos_profile': pos_profile,
													'status': 'Unpaid',
												},
												fields=["*"]
												)
			for sales_invoice in sales_invoice_list:
				found_folio = frappe.get_doc('Folio Transaction', {'sales_invoice_id': sales_invoice.name})
				if not found_folio:
					doc_folio = frappe.get_doc('Folio', {'folio_id': folio_id})
					doc = frappe.new_doc('Folio Transaction')
					doc.folio_id = folio_id
					doc.amount = sales_invoice.total
					doc.sales_invoice_id = sales_invoice.name
					doc.total_qty = sales_invoice.total_qty
					doc.pos_profile = pos_profile
					doc.flag = 'Credit'
					doc.account_id = sales_invoice.against_income_account
					doc.against_account_id = sales_invoice.debit_to
					doc.remark = 'Sales Invoice POS ' + pos_profile + ' ID: ' + sales_invoice.name + '  ' + sales_invoice.posting_date
					doc.is_void = 0

					doc_folio.append('transaction_detail', doc)
					doc.save()
