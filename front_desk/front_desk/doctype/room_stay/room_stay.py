# -*- coding: utf-8 -*-
# Copyright (c) 2019, PMM and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
import datetime
from frappe.model.document import Document

class RoomStay(Document):
	pass

def create_room_stay(reservation_id_list):
	reservation_id_list = json.loads(reservation_id_list)

	url_list = []
	for reservation_id in reservation_id_list:
		nama = 'RS-' + reservation_id

		if not frappe.db.exists('Room Stay', nama):
			doc = frappe.new_doc('Room Stay')
			doc.nama = nama
			doc.reservation_id = reservation_id
			doc.insert()

		url_list.append(frappe.utils.get_url_to_form('Room Stay', nama))
	
	return url_list

@frappe.whitelist()
def create_deposit_journal_entry(reservation_id, amount, debit_account_name, credit_account_name):
	doc = frappe.new_doc('Journal Entry')
	doc.voucher_type = 'Journal Entry'
	doc.naming_series = 'ACC-JV-.YYYY.-'
	doc.posting_date = datetime.date.today()
	doc.company = 'IHRAM'
	doc.remark = 'Deposit ' + reservation_id
	doc.user_remark = 'Deposit ' + reservation_id

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
	
	doc.append('accounts', doc_debit)
	doc.append('accounts', doc_credit)

	doc.save()
	doc.submit()

@frappe.whitelist()
def get_credit_account_name():
	return frappe.db.get_list('Account',
		filters={
			'account_number': '1172.000'
		}
	)[0].name

@frappe.whitelist()
def get_debit_account_name_list():
	debit_account_name_list = []
	debit_account_name_list.append(frappe.db.get_list('Account', filters={'account_number': '1111.00211'})[0].name)
	
	temp = frappe.db.get_list('Account', filters={'account_number': ['like', '1121.%'], 'account_type': 'Bank'})
	for t in temp:
		debit_account_name_list.append(t.name)
	
	return debit_account_name_list