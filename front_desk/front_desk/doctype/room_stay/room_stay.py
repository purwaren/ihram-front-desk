# -*- coding: utf-8 -*-
# Copyright (c) 2019, PMM and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import datetime
import frappe
from frappe.model.document import Document
from front_desk.front_desk.doctype.hotel_bill.hotel_bill import is_this_weekday
from front_desk.front_desk.doctype.folio.folio import get_folio_name

class RoomStay(Document):
	pass

@frappe.whitelist()
def get_room_stay_by_name(name):
	return frappe.get_doc('Room Stay', name)

def get_room_stay_name_by_parent(parent, parentfield, parenttype):
	return frappe.db.get_value('Room Stay', {'parent':parent, 'parentfield':parentfield, 'parenttype':parenttype}, ['name'])

@frappe.whitelist()
def change_parent(parent_now, parentfield_now, parenttype_now, parent_new, parentfield_new, parenttype_new):
	frappe.db.sql('UPDATE `tabRoom Stay` SET parent=%s, parentfield=%s, parenttype=%s WHERE parent=%s AND parentfield=%s AND parenttype=%s', (parent_new, parentfield_new, parenttype_new, parent_now, parentfield_now, parenttype_now))

@frappe.whitelist()
def add_early_checkin(room_stay_id):
	frappe.msgprint("masuk early checkin")
	room_stay = frappe.get_doc('Room Stay', room_stay_id)

	if room_stay.is_early_checkin == 1:
		frappe.msgprint("masuk early checkin == 1")
		ec_percentage = frappe.db.get_value('Early Check In Percentage',
											{'early_checkin_name': room_stay.early_checkin_rate},
											['early_checkin_percentage'])
		ec_remark = 'Early Check In Room ' + room_stay.room_id + ": " + room_stay.early_checkin_rate + " ( " + str(
			ec_percentage) + "% of Room Rate)"
		exist_folio_trx_ec = frappe.db.exists('Folio Transaction', {'parent':get_folio_name(room_stay.reservation_id), 'remark': ec_remark})
		frappe.msgprint(exist_folio_trx_ec)
		if not exist_folio_trx_ec:
			frappe.msgprint("masuk not exist folio trx buat ec")
			je_credit_account = frappe.db.get_list('Account', filters={'account_number': '1132.001'})[0].name
			je_debit_account = frappe.db.get_list('Account', filters={'account_number': '4320.001'})[0].name
			cust_name = frappe.get_doc('Customer', frappe.get_doc('Reservation', room_stay.reservation_id).customer_id).name
			room_rate_doc = frappe.get_doc('Room Rate', room_stay.room_rate)
			if is_this_weekday(room_stay.arrival):
				frappe.msgprint("masuk weekday arrival")
				special_charge_amount = room_rate_doc.rate_weekday * ec_percentage/100.0
			else:
				frappe.msgprint("masuk weekend arrival")
				special_charge_amount = room_rate_doc.rate_weekend * ec_percentage/100.0
			frappe.msgprint("charge amount = " + str(special_charge_amount))
			doc_journal_entry = frappe.new_doc('Journal Entry')
			doc_journal_entry.title = ec_remark
			doc_journal_entry.voucher_type = 'Journal Entry'
			doc_journal_entry.naming_series = 'ACC-JV-.YYYY.-'
			doc_journal_entry.posting_date = datetime.date.today()
			doc_journal_entry.company = frappe.get_doc("Global Defaults").default_company
			doc_journal_entry.total_amount_currency = frappe.get_doc("Global Defaults").default_currency
			doc_journal_entry.remark = ec_remark
			doc_journal_entry.user_remark = ec_remark

			doc_debit = frappe.new_doc('Journal Entry Account')
			doc_debit.account = je_debit_account
			doc_debit.debit = special_charge_amount
			doc_debit.party_type = 'Customer'
			doc_debit.party = cust_name
			doc_debit.debit_in_account_currency = special_charge_amount
			doc_debit.user_remark = ec_remark

			doc_credit = frappe.new_doc('Journal Entry Account')
			doc_credit.account = je_credit_account
			doc_credit.credit = special_charge_amount
			doc_credit.party_type = 'Customer'
			doc_credit.party = cust_name
			doc_credit.credit_in_account_currency = special_charge_amount
			doc_credit.user_remark = ec_remark

			doc_journal_entry.append('accounts', doc_debit)
			doc_journal_entry.append('accounts', doc_credit)

			doc_journal_entry.save()
			doc_journal_entry.submit()

			folio_name = get_folio_name(room_stay.reservation_id)
			doc_folio = frappe.get_doc('Folio', folio_name)

			doc_folio_transaction = frappe.new_doc('Folio Transaction')
			doc_folio_transaction.folio_id = doc_folio.name
			doc_folio_transaction.amount = special_charge_amount
			doc_folio_transaction.flag = 'Debit'
			doc_folio_transaction.account_id = je_debit_account
			doc_folio_transaction.against_account_id = je_credit_account
			doc_folio_transaction.remark = ec_remark
			doc_folio_transaction.is_special_charge = 1
			doc_folio_transaction.is_void = 0

			doc_folio.append('transaction_detail', doc_folio_transaction)
			doc_folio.save()

@frappe.whitelist()
def add_late_checkout(room_stay_id):
	frappe.msgprint("masuk late checkout")
	room_stay = frappe.get_doc('Room Stay', room_stay_id)

	if room_stay.is_late_checkout == 1:
		frappe.msgprint("masuk late checkout == 1")
		lc_percentage = frappe.db.get_value('Late Check Out Percentage',
											{'late_checkout_name': room_stay.late_checkout_rate},
											['late_checkout_percentage'])
		lc_remark = 'Late Check Out Room ' + room_stay.room_id + ": " + room_stay.late_checkout_rate + " ( " + str(
			lc_percentage) + "% of Room Rate)"
		exist_folio_trx_lc = frappe.db.exists('Folio Transaction', {'parent':get_folio_name(room_stay.reservation_id), 'remark': lc_remark})
		if not exist_folio_trx_lc:
			frappe.msgprint("masuk not exist folio trx untuk lc")
			je_credit_account = frappe.db.get_list('Account', filters={'account_number': '1132.001'})[0].name
			je_debit_account = frappe.db.get_list('Account', filters={'account_number': '4320.001'})[0].name
			cust_name = frappe.get_doc('Customer', frappe.get_doc('Reservation', room_stay.reservation_id).customer_id).name
			room_rate_doc = frappe.get_doc('Room Rate', room_stay.room_rate)

			if is_this_weekday(room_stay.departure):
				special_charge_amount = room_rate_doc.rate_weekday * lc_percentage / 100.0
			else:
				special_charge_amount = room_rate_doc.rate_weekend * lc_percentage / 100.0

			doc_journal_entry = frappe.new_doc('Journal Entry')
			doc_journal_entry.title = lc_remark
			doc_journal_entry.voucher_type = 'Journal Entry'
			doc_journal_entry.naming_series = 'ACC-JV-.YYYY.-'
			doc_journal_entry.posting_date = datetime.date.today()
			doc_journal_entry.company = frappe.get_doc("Global Defaults").default_company
			doc_journal_entry.total_amount_currency = frappe.get_doc("Global Defaults").default_currency
			doc_journal_entry.remark = lc_remark
			doc_journal_entry.user_remark = lc_remark

			doc_debit = frappe.new_doc('Journal Entry Account')
			doc_debit.account = je_debit_account
			doc_debit.debit = special_charge_amount
			doc_debit.party_type = 'Customer'
			doc_debit.party = cust_name
			doc_debit.debit_in_account_currency = special_charge_amount
			doc_debit.user_remark = lc_remark

			doc_credit = frappe.new_doc('Journal Entry Account')
			doc_credit.account = je_credit_account
			doc_credit.credit = special_charge_amount
			doc_credit.party_type = 'Customer'
			doc_credit.party = cust_name
			doc_credit.credit_in_account_currency = special_charge_amount
			doc_credit.user_remark = lc_remark

			doc_journal_entry.append('accounts', doc_debit)
			doc_journal_entry.append('accounts', doc_credit)

			doc_journal_entry.save()
			doc_journal_entry.submit()

			folio_name = get_folio_name(room_stay.reservation_id)
			doc_folio = frappe.get_doc('Folio', folio_name)

			doc_folio_transaction = frappe.new_doc('Folio Transaction')
			doc_folio_transaction.folio_id = doc_folio.name
			doc_folio_transaction.amount = special_charge_amount
			doc_folio_transaction.flag = 'Debit'
			doc_folio_transaction.account_id = je_debit_account
			doc_folio_transaction.against_account_id = je_credit_account
			doc_folio_transaction.remark = lc_remark
			doc_folio_transaction.is_special_charge = 1
			doc_folio_transaction.is_void = 0

			doc_folio.append('transaction_detail', doc_folio_transaction)
			doc_folio.save()
