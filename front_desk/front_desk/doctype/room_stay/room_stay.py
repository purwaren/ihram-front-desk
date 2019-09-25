# -*- coding: utf-8 -*-
# Copyright (c) 2019, PMM and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import datetime
import frappe
from frappe.model.document import Document
from front_desk.front_desk.doctype.hotel_bill.hotel_bill import is_this_weekday

class RoomStay(Document):
	pass

@frappe.whitelist()
def validate_special_charge(docname):
	doc = frappe.get_doc('Room Stay', docname)
	room_rate_doc = frappe.get_doc('Room Rate', doc.room_rate)

	je_credit_account = frappe.db.get_list('Account', filters={'account_number': '1132.001'})[0].name
	je_debit_account = frappe.db.get_list('Account', filters={'account_number': '4320.001'})[0].name
	cust_name = frappe.get_doc('Customer', frappe.get_doc('Reservation', doc.reservation_id).customer_id).name
	ec_percentage = frappe.db.get_value('Early Check In Percentage', {'early_checkin_name': doc.early_checkin_rate},
									 ['early_checkin_percentage'])
	lc_percentage = frappe.db.get_value('Late Check Out Percentage', {'late_checkout_name': doc.late_checkout_rate},
									 ['late_checkout_percentage'])
	ec_remark = 'Early Check In Room ' + doc.room_id + ": " + doc.early_checkin_rate + " ( " + str(
		ec_percentage) + "% of Room Rate)"
	lc_remark = 'Late Check Out Room ' + doc.room_id + ": " + doc.late_checkout_rate + " ( " + str(
		lc_percentage) + "% of Room Rate)"
	exist_folio_trx_ec = frappe.db.exists('Folio Transaction', {'remark': ec_remark})
	exist_folio_trx_lc = frappe.db.exists('Folio Transaction', {'remark': lc_remark})

	if doc.is_early_checkin == 1 and not exist_folio_trx_ec:
		if is_this_weekday(doc.arrival):
			special_charge_amount = room_rate_doc.rate_weekday * ec_percentage/100.0
		else:
			special_charge_amount = room_rate_doc.rate_weekend * ec_percentage/100.0

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

		folio_name = frappe.db.get_value('Folio', {'reservation_id': doc.reservation_id}, ['name'])
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

	if doc.is_late_checkout == 1 and not exist_folio_trx_lc:

		if is_this_weekday(doc.departure):
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

		folio_name = frappe.db.get_value('Folio', {'reservation_id': doc.reservation_id}, ['name'])
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

def get_room_book_list(filters):
	room_book_list = list(frappe.db.sql("SELECT rb.room_id FROM `tabRoom Booking` AS rb LEFT JOIN `tabReservation Detail` AS rd ON rb.reference_name = rd.name WHERE (rd.parent != %s) AND (rb.status =	 'Booked') AND ((%s >= rb.start AND %s < rb.end) OR (%s > rb.start AND %s <= rb.end) OR (%s <= rb.start AND %s >= rb.end))", (filters.get('parent'), filters.get('arrival'), filters.get('arrival'), filters.get('departure'), filters.get('departure'), filters.get('arrival'), filters.get('departure'))))
	room_book_list.extend(list(frappe.db.sql("SELECT rs.room_id FROM `tabRoom Stay` AS rs LEFT JOIN `tabReservation` AS r ON rs.reservation_id = r.name WHERE (rs.parent != %s) AND (r.status = 'Confirmed' OR r.status = 'In House') AND ((%s >= CONVERT(rs.arrival, DATE) AND %s < CONVERT(rs.departure, DATE)) OR (%s > CONVERT(rs.arrival, DATE) AND %s <= CONVERT(rs.departure, DATE)) OR (%s <= CONVERT(rs.arrival, DATE) AND %s >= CONVERT(rs.departure, DATE)))", (filters.get('parent'), filters.get('arrival'), filters.get('arrival'), filters.get('departure'), filters.get('departure'), filters.get('arrival'), filters.get('departure')))))
	
	return room_book_list

@frappe.whitelist()
def get_room_available(doctype, txt, searchfield, start, page_len, filters):
	room_list = list(frappe.db.sql("select name, room_type, bed_type, allow_smoke from `tabHotel Room`"))
	room_book_list = get_room_book_list(filters)

	for room_book in room_book_list:
		for i in range(len(room_list)):
			if room_list[i][0] == room_book[0]:
				del room_list[i]
				break

	return room_list