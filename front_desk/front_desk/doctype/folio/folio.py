# -*- coding: utf-8 -*-
# Copyright (c) 2019, PMM and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import json
import frappe
import datetime
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

def get_account(account_type, pos_profile, is_checkout=False):
	account_name = ''
	if not is_checkout:
		if account_type == 'Debit':
			account = frappe.db.get_list('Account', filters={'account_number': '4110.000'})
			if len(account) > 0:
				account_name = account[0].name
		elif account_type == 'Credit':
			account = frappe.db.get_list('Account', filters={'account_number': '1132.001'})
			if len(account) > 0:
				account_name = account[0].name

	else:
		if account_type == 'Debit':
			account = frappe.db.get_list('Account', filters={'account_number': '4110.000'})
			if len(account) > 0:
				account_name = account[0].name
		if account_type == 'Cebit':
			if pos_profile == 'Front Office':
				account = frappe.db.get_list('Account', filters={'account_number': '1111.003'})
				if len(account) > 0:
					account_name = account[0].name
			elif pos_profile == 'Kitchen':
				account = frappe.db.get_list('Account', filters={'account_number': '1111.004'})
				if len(account) > 0:
					account_name = account[0].name
			elif pos_profile == 'F&B':
				account = frappe.db.get_list('Account', filters={'account_number': '1111.005'})
				if len(account) > 0:
					account_name = account[0].name
			elif pos_profile == 'Housekeeping':
				account = frappe.db.get_list('Account', filters={'account_number': '1111.006'})
				if len(account) > 0:
					account_name = account[0].name

	return account_name

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
				if not frappe.db.exists('Folio Transaction', {'sales_invoice_id': sales_invoice.name}):
					doc_folio = frappe.get_doc('Folio', {'name': folio_id})
					doc = frappe.new_doc('Folio Transaction')
					doc.folio_id = folio_id
					doc.amount = sales_invoice.total
					doc.sales_invoice_id = sales_invoice.name
					doc.total_qty = sales_invoice.total_qty
					doc.pos_profile = pos_profile.name
					doc.flag = 'Debit'
					doc.account_id = sales_invoice.against_income_account
					doc.against_account_id = sales_invoice.debit_to
					doc.remark = 'Sales Invoice POS ' + pos_profile.name + ' ID: ' + sales_invoice.name
					doc.is_void = 0

					doc_folio.append('transaction_detail', doc)
					doc_folio.save()

def copy_trx_from_folio_transaction_to_journal_entry(reservation_id):
	# copy the folio transactions which not have entry yet in General Ledger. i.e: Room charge transactions

	folio_id = frappe.get_doc('Folio', {"reservation_id": reservation_id}).name
	folio_trx_list = frappe.get_all('Folio Transaction', filters={'folio_id': folio_id}, fields=["*"])
	for folio_trx in folio_trx_list:
		if folio_trx.sales_invoice_id is None:
			credit_account_name = folio_trx.account_id
			debit_account_name = folio_trx.against_account_id
			doc_journal_entry = frappe.new_doc('Journal Entry')
			doc_journal_entry.voucher_type = 'Journal Entry'
			doc_journal_entry.naming_series = 'ACC-JV-.YYYY.-'
			doc_journal_entry.posting_date = datetime.date.today()
			doc_journal_entry.company = frappe.get_doc("Global Defaults").default_company
			doc_journal_entry.remark = folio_trx.remark
			doc_journal_entry.user_remark = folio_trx.remark

			doc_debit = frappe.new_doc('Journal Entry Account')
			doc_debit.account = debit_account_name
			doc_debit.debit = folio_trx.amount
			doc_debit.debit_in_account_currency = folio_trx.amount
			doc_debit.user_remark = folio_trx.remark

			doc_credit = frappe.new_doc('Journal Entry Account')
			doc_credit.account = credit_account_name
			doc_credit.credit = folio_trx.amount
			doc_credit.credit_in_account_currency = folio_trx.amount
			doc_credit.user_remark = folio_trx.remark

			doc_journal_entry.append('accounts', doc_debit)
			doc_journal_entry.append('accounts', doc_credit)

			doc_journal_entry.save()
			doc_journal_entry.submit()

def finalize_sales_invoice_from_folio(reservation_id):
	folio_id = frappe.get_doc('Folio', {"reservation_id": reservation_id}).name
	folio_trx_list = frappe.get_all('Folio Transaction', filters={'folio_id': folio_id}, fields=["*"])
	for folio_trx in folio_trx_list:
		if folio_trx.sales_invoice_id is not None:
			sales_invoice_found = frappe.get_doc('Sales Invoice', {'name': folio_trx.sales_invoice_id})
			debit_account_name = sales_invoice_found.debit_to
			credit_account_name = get_account('Credit', folio_trx.pos_profile, True)
			doc_journal_entry = frappe.new_doc('Journal Entry')
			doc_journal_entry.voucher_type = 'Journal Entry'
			doc_journal_entry.naming_series = 'ACC-JV-.YYYY.-'
			doc_journal_entry.posting_date = datetime.date.today()
			doc_journal_entry.company = frappe.get_doc("Global Defaults").default_company
			doc_journal_entry.remark = 'Payment Entry for ' + folio_trx.remark
			doc_journal_entry.user_remark = 'Payment Entry for ' + folio_trx.remark

			doc_debit = frappe.new_doc('Journal Entry Account')
			doc_debit.account = debit_account_name
			doc_debit.debit = folio_trx.amount
			doc_debit.debit_in_account_currency = folio_trx.amount
			doc_debit.user_remark = 'Payment Entry for ' + folio_trx.remark

			doc_credit = frappe.new_doc('Journal Entry Account')
			doc_credit.account = credit_account_name
			doc_credit.credit = folio_trx.amount
			doc_credit.credit_in_account_currency = folio_trx.amount
			doc_credit.user_remark = 'Payment Entry for ' + folio_trx.remark

			doc_journal_entry.append('accounts', doc_debit)
			doc_journal_entry.append('accounts', doc_credit)

			doc_journal_entry.save()
			doc_journal_entry.submit()

			sales_invoice_found.status = 'Paid'
			sales_invoice_found.save()
