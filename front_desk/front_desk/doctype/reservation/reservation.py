# -*- coding: utf-8 -*-
# Copyright (c) 2019, PMM and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import json
import datetime
import frappe
from frappe.model.document import Document
from front_desk.front_desk.doctype.folio.folio import create_folio

class Reservation(Document):
	pass

@frappe.whitelist()
def check_in(reservation_id_list):
	reservation_id_list = json.loads(reservation_id_list)

	for reservation_id in reservation_id_list:
		if frappe.db.get_value('Reservation', reservation_id, 'status') == 'Created':
			doc = frappe.get_doc('Reservation', reservation_id)
			doc.status = 'Confirmed'
			doc.save()

			create_folio(reservation_id_list)

	url_list = []
	for reservation_id in reservation_id_list:
		url_list.append(frappe.utils.get_url_to_form('Reservation', reservation_id))
	
	return url_list

@frappe.whitelist()
def create_deposit_journal_entry(reservation_id, amount, debit_account_name):
	credit_account_name = get_credit_account_name()

	doc_journal_entry = frappe.new_doc('Journal Entry')
	doc_journal_entry.voucher_type = 'Journal Entry'
	doc_journal_entry.naming_series = 'ACC-JV-.YYYY.-'
	doc_journal_entry.posting_date = datetime.date.today()
	doc_journal_entry.company = frappe.get_doc("Global Defaults").default_company
	doc_journal_entry.remark = 'Deposit ' + reservation_id
	doc_journal_entry.user_remark = 'Deposit ' + reservation_id

	doc_debit = frappe.new_doc('Journal Entry Account')
	doc_debit.account = debit_account_name
	doc_debit.debit = amount
	doc_debit.debit_in_account_currency = amount
	doc_debit.user_remark = 'Deposit ' + reservation_id

	doc_credit = frappe.new_doc('Journal Entry Account')
	doc_credit.account = credit_account_name
	doc_credit.credit = amount
	doc_credit.credit_in_account_currency = amount
	doc_credit.user_remark = 'Deposit ' + reservation_id
	
	doc_journal_entry.append('accounts', doc_debit)
	doc_journal_entry.append('accounts', doc_credit)

	doc_journal_entry.save()
	doc_journal_entry.submit()

	folio_name = frappe.db.get_value('Folio', {'reservation_id': reservation_id}, ['name'])
	doc_folio = frappe.get_doc('Folio', folio_name)

	doc_folio_transaction = frappe.new_doc('Folio Transaction')
	doc_folio_transaction.folio_id = doc_folio.name
	doc_folio_transaction.amount = amount
	doc_folio_transaction.flag = 'Credit'
	doc_folio_transaction.account_id = credit_account_name
	doc_folio_transaction.against_account_id = debit_account_name
	doc_folio_transaction.remark = 'Deposit ' + reservation_id
	doc_folio_transaction.is_void = 0

	doc_folio.append('transaction_detail', doc_folio_transaction)
	doc_folio.save()


def get_credit_account_name():
	temp = frappe.db.get_list('Account',
		filters={
			'account_number': '1172.000'
		}
	)

	if len(temp) > 0:
		return temp[0].name
	else:
		return ''

@frappe.whitelist()
def get_debit_account_name_list():
	debit_account_name_list = []

	temp = frappe.db.get_list('Account',
		filters={
			'account_number': '1111.003'
		}
	)

	if len(temp) > 0:
		debit_account_name_list.append(temp[0].name)
	
	temp = frappe.db.get_list('Account',
		filters={
			'account_number': ['like', '1121.%'], 'account_type': 'Bank'
		}
	)

	for t in temp:
		debit_account_name_list.append(t.name)
	
	return debit_account_name_list

@frappe.whitelist()
def check_out(reservation_id_list):
	reservation_id_list = json.loads(reservation_id_list)
	# TODO: Calculate trx and print receipt


	for reservation_id in reservation_id_list:
		checkout_reservation(reservation_id)

@frappe.whitelist()
def cancel(reservation_id_list):
	reservation_id_list = json.loads(reservation_id_list)

	for reservation_id in reservation_id_list:
		cancel_reservation(reservation_id)

@frappe.whitelist()
def get_status(reservation_id_list):
	reservation_id_list = json.loads(reservation_id_list)
	for reservation_id in reservation_id_list:
		reservation = frappe.get_doc('Reservation', reservation_id, fields=['status'])
	return reservation.status

@frappe.whitelist()
def cancel_reservation(reservation_id):
	if frappe.db.get_value('Reservation', reservation_id, 'status') == 'Created':
		reservation = frappe.get_doc('Reservation', reservation_id)
		reservation.status = "Cancel"
		reservation.save()

@frappe.whitelist()
def checkout_reservation(reservation_id):
	if frappe.db.get_value('Reservation', reservation_id, 'status') == 'In House':
		reservation = frappe.get_doc('Reservation', reservation_id)
		# Update reservation status to "FINISH"
		reservation.status = "Finish"
		reservation.save()

		room_stay = frappe.get_doc('Room Stay', {"reservation_id": reservation_id})
		# Update departure time in room stay
		room_stay.departure = frappe.utils.now()
		room_stay.save()
		hotel_room = frappe.get_doc('Hotel Room', room_stay.room_id)
		# Update room_status dari hotel_room menjadi "Vacant Dirty"
		hotel_room.room_status = "Vacant Dirty"
		# Update status dari hotel_room menjadi "OO"
		hotel_room.status = "OO"
		hotel_room.save()


def auto_room_charge():
	reservation_list = frappe.get_all('Reservation', {'status': 'In House'})
	for reservation in reservation_list:
		create_room_charge(reservation.name)

def create_room_charge(reservation_id):
	room_stay_list = frappe.get_all('Room Stay', {"reservation_id": reservation_id}, fields=["*"])
	for room_stay in room_stay_list:
		room_rate = frappe.get_doc('Room Rate', room_stay.room_rate, fields=['*'])
		je_credit_account = frappe.db.get_list('Account', filters={'account_number': '1132.001'})[0].name
		je_debit_account = frappe.db.get_list('Account', filters={'account_number': '4320.001'})[0].name

		doc_journal_entry = frappe.new_doc('Journal Entry')
		doc_journal_entry.voucher_type = 'Journal Entry'
		doc_journal_entry.naming_series = 'ACC-JV-.YYYY.-'
		doc_journal_entry.posting_date = datetime.date.today()
		doc_journal_entry.company = frappe.get_doc("Global Defaults").default_company
		doc_journal_entry.total_amount_currency = frappe.get_doc("Global Defaults").default_currency
		doc_journal_entry.remark = 'Auto Room Charge ' + reservation_id
		doc_journal_entry.user_remark = 'Auto Room Charge ' + reservation_id

		doc_debit = frappe.new_doc('Journal Entry Account')
		doc_debit.account = je_debit_account
		doc_debit.debit = room_rate.rate
		doc_debit.debit_in_account_currency = room_rate.rate
		doc_debit.user_remark = 'Auto Room Charge ' + reservation_id

		doc_credit = frappe.new_doc('Journal Entry Account')
		doc_credit.account = je_credit_account
		doc_credit.credit = room_rate.rate
		doc_credit.credit_in_account_currency = room_rate.rate
		doc_credit.user_remark = 'Auto Room Charge ' + reservation_id

		doc_journal_entry.append('accounts', doc_debit)
		doc_journal_entry.append('accounts', doc_credit)

		doc_journal_entry.save()
		doc_journal_entry.submit()

		folio_name = frappe.db.get_value('Folio', {'reservation_id': reservation_id}, ['name'])
		doc_folio = frappe.get_doc('Folio', folio_name)

		doc_folio_transaction = frappe.new_doc('Folio Transaction')
		doc_folio_transaction.folio_id = doc_folio.name
		doc_folio_transaction.amount = room_rate.rate
		doc_folio_transaction.flag = 'Debit'
		doc_folio_transaction.account_id = je_credit_account
		doc_folio_transaction.against_account_id = je_debit_account
		doc_folio_transaction.remark = 'Auto Room Charge ' + reservation_id
		doc_folio_transaction.is_void = 0

		doc_folio.append('transaction_detail', doc_folio_transaction)
		doc_folio.save()


