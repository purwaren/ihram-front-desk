# -*- coding: utf-8 -*-
# Copyright (c) 2019, PMM and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import json
import datetime
import frappe
from frappe.model.document import Document
from front_desk.front_desk.doctype.folio.folio import create_folio
from front_desk.front_desk.doctype.room_booking.room_booking import update_by_reservation

class Reservation(Document):
	pass

def is_weekday():
	weekno = datetime.datetime.today().weekday()

	if weekno<5:
		return True
	else:
		return False

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
			'account_number': ['like', '1121.0%'], 'account_type': 'Bank'
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

		#update room booking status
		update_by_reservation(reservation_id)

@frappe.whitelist()
def checkout_reservation(reservation_id):
	if frappe.db.get_value('Reservation', reservation_id, 'status') == 'In House':
		reservation = frappe.get_doc('Reservation', reservation_id)
		# Update reservation status to "FINISH"
		reservation.status = "Finish"

		room_stay = frappe.get_doc('Room Stay', {"reservation_id": reservation_id})
		# Update departure time in room stay
		room_stay.departure = frappe.utils.now()
		# room_stay.save()

		reservation.save()

		hotel_room = frappe.get_doc('Hotel Room', room_stay.room_id)
		# Update room_status dari hotel_room menjadi "Vacant Dirty"
		hotel_room.room_status = "Vacant Dirty"
		# TODO: Update Status Availability dari Hotem Room pada hari itu saja.

		## Update room booking status
		update_by_reservation(reservation_id)

def auto_release_reservation_at_six_pm():
	reservation_list = frappe.get_all('Reservation', {'status': 'Created', 'is_guaranteed': 0})
	for reservation in reservation_list:
		reservation_detail_list = frappe.get_all('Reservation Detail', {'parent': reservation.name})
		arrival_expired = False
		for rd in reservation_detail_list:
			if (rd.expected_arrival < frappe.utils.now()):
				arrival_expired = True

		if arrival_expired:
			frappe.db.set_value('Reservation', reservation.name, 'status', 'Cancel')


def auto_room_charge():
	reservation_list = frappe.get_all('Reservation', {'status': 'In House'})
	for reservation in reservation_list:
		create_room_charge(reservation.name)

def create_room_charge(reservation_id):
	room_stay_list = frappe.get_all('Room Stay', filters={"reservation_id": reservation_id}, fields=["name","room_rate", "room_id"])
	cust_name = frappe.get_doc('Customer', frappe.get_doc('Reservation', reservation_id).customer_id).name

	if len(room_stay_list) > 0:
		for room_stay in room_stay_list:
			if (room_stay.departure <= frappe.utils.now()):
				room_rate = frappe.get_doc('Room Rate', {'name':room_stay.room_rate})
				room_name = room_stay.room_id
				remark = 'Auto Room Charge Room:' + room_name
				je_credit_account = frappe.db.get_list('Account', filters={'account_number': '1132.001'})[0].name
				je_debit_account = frappe.db.get_list('Account', filters={'account_number': '4320.001'})[0].name
				if is_weekday():
					today_rate = room_rate.rate_weekday
				else:
					today_rate = room_rate.rate_weekend

				doc_journal_entry = frappe.new_doc('Journal Entry')
				doc_journal_entry.title = 'Auto Room Charge ' + reservation_id + ' Room: ' + room_name
				doc_journal_entry.voucher_type = 'Journal Entry'
				doc_journal_entry.naming_series = 'ACC-JV-.YYYY.-'
				doc_journal_entry.posting_date = datetime.date.today()
				doc_journal_entry.company = frappe.get_doc("Global Defaults").default_company
				doc_journal_entry.total_amount_currency = frappe.get_doc("Global Defaults").default_currency
				doc_journal_entry.remark = remark
				doc_journal_entry.user_remark = remark

				doc_debit = frappe.new_doc('Journal Entry Account')
				doc_debit.account = je_debit_account
				doc_debit.debit = today_rate
				doc_debit.debit_in_account_currency = today_rate
				doc_debit.party_type = 'Customer'
				doc_debit.party = cust_name
				doc_debit.user_remark = remark

				doc_credit = frappe.new_doc('Journal Entry Account')
				doc_credit.account = je_credit_account
				doc_credit.credit = today_rate
				doc_credit.party_type = 'Customer'
				doc_credit.party = cust_name
				doc_credit.credit_in_account_currency = today_rate
				doc_credit.user_remark = remark

				doc_journal_entry.append('accounts', doc_debit)
				doc_journal_entry.append('accounts', doc_credit)

				doc_journal_entry.save()
				doc_journal_entry.submit()

				folio_name = frappe.db.get_value('Folio', {'reservation_id': reservation_id}, ['name'])
				doc_folio = frappe.get_doc('Folio', folio_name)

				doc_folio_transaction = frappe.new_doc('Folio Transaction')
				doc_folio_transaction.folio_id = doc_folio.name
				doc_folio_transaction.amount = today_rate
				doc_folio_transaction.flag = 'Debit'
				doc_folio_transaction.account_id = je_credit_account
				doc_folio_transaction.against_account_id = je_debit_account
				doc_folio_transaction.remark = remark
				doc_folio_transaction.is_void = 0

				doc_folio.append('transaction_detail', doc_folio_transaction)
				doc_folio.save()


@frappe.whitelist()
def get_empty_array(doctype, txt, searchfield, start, page_len, filters):
	return []

@frappe.whitelist()
def get_room_available(doctype, txt, searchfield, start, page_len, filters):
	room_list = list(frappe.db.sql("select name, room_type, bed_type, allow_smoke from `tabHotel Room` where allow_smoke = %s", (filters.get('allow_smoke'))))
	room_book_list = list(frappe.db.sql("SELECT room_id FROM `tabReservation Detail` AS rd LEFT JOIN `tabReservation` AS r ON rd.parent = r.name where (rd.parent != %s) and (r.status = 'Created') and ((rd.expected_arrival >= %s and rd.expected_arrival < %s) or (rd.expected_departure > %s and rd.expected_departure <= %s) or (rd.expected_arrival <= %s and rd.expected_departure >= %s))", (filters.get('parent'), filters.get('expected_arrival'), filters.get('expected_departure'), filters.get('expected_arrival'), filters.get('expected_departure'), filters.get('expected_arrival'), filters.get('expected_departure'))))
	room_book_list.extend(list(frappe.db.sql("SELECT room_id FROM `tabRoom Stay` AS rs LEFT JOIN `tabReservation` AS r ON rs.reservation_id = r.name where (rs.parent != %s) and (r.status = 'Confirmed' or r.status = 'In House') and ((CONVERT(rs.arrival, DATE) >= %s and CONVERT(rs.arrival, DATE) < %s) or (CONVERT(rs.departure, DATE) > %s and CONVERT(rs.departure, DATE) <= %s) or (CONVERT(rs.arrival, DATE) <= %s and CONVERT(rs.departure, DATE) >= %s))", (filters.get('parent'), filters.get('expected_arrival'), filters.get('expected_departure'), filters.get('expected_arrival'), filters.get('expected_departure'), filters.get('expected_arrival'), filters.get('expected_departure')))))

	for room_book in room_book_list:
		for i in range(len(room_list)):
			if room_list[i][0] == room_book[0]:
				del room_list[i]
				break

	return room_list

@frappe.whitelist()
def get_room_available_by_room_type(doctype, txt, searchfield, start, page_len, filters):
	room_list = list(frappe.db.sql("select name, room_type, bed_type, allow_smoke from `tabHotel Room` where allow_smoke = %s and room_type = %s", (filters.get('allow_smoke'), filters.get('room_type'))))
	room_book_list = list(frappe.db.sql("SELECT room_id FROM `tabReservation Detail` AS rd LEFT JOIN `tabReservation` AS r ON rd.parent = r.name where (rd.parent != %s) and (r.status = 'Created') and ((rd.expected_arrival >= %s and rd.expected_arrival < %s) or (rd.expected_departure > %s and rd.expected_departure <= %s) or (rd.expected_arrival <= %s and rd.expected_departure >= %s))", (filters.get('parent'), filters.get('expected_arrival'), filters.get('expected_departure'), filters.get('expected_arrival'), filters.get('expected_departure'), filters.get('expected_arrival'), filters.get('expected_departure'))))
	room_book_list.extend(list(frappe.db.sql("SELECT room_id FROM `tabRoom Stay` AS rs LEFT JOIN `tabReservation` AS r ON rs.reservation_id = r.name where (rs.parent != %s) and (r.status = 'Confirmed' or r.status = 'In House') and ((CONVERT(rs.arrival, DATE) >= %s and CONVERT(rs.arrival, DATE) < %s) or (CONVERT(rs.departure, DATE) > %s and CONVERT(rs.departure, DATE) <= %s) or (CONVERT(rs.arrival, DATE) <= %s and CONVERT(rs.departure, DATE) >= %s))", (filters.get('parent'), filters.get('expected_arrival'), filters.get('expected_departure'), filters.get('expected_arrival'), filters.get('expected_departure'), filters.get('expected_arrival'), filters.get('expected_departure')))))
	
	for room_book in room_book_list:
		for i in range(len(room_list)):
			if room_list[i][0] == room_book[0]:
				del room_list[i]
				break

	return room_list

@frappe.whitelist()
def get_room_available_by_room_type_bed_type(doctype, txt, searchfield, start, page_len, filters):
	room_list = list(frappe.db.sql("select name, room_type, bed_type, allow_smoke from `tabHotel Room` where allow_smoke = %s and room_type = %s and bed_type = %s", (filters.get('allow_smoke'), filters.get('room_type'), filters.get('bed_type'))))
	room_book_list = list(frappe.db.sql("SELECT room_id FROM `tabReservation Detail` AS rd LEFT JOIN `tabReservation` AS r ON rd.parent = r.name where (rd.parent != %s) and (r.status = 'Created') and ((rd.expected_arrival >= %s and rd.expected_arrival < %s) or (rd.expected_departure > %s and rd.expected_departure <= %s) or (rd.expected_arrival <= %s and rd.expected_departure >= %s))", (filters.get('parent'), filters.get('expected_arrival'), filters.get('expected_departure'), filters.get('expected_arrival'), filters.get('expected_departure'), filters.get('expected_arrival'), filters.get('expected_departure'))))
	room_book_list.extend(list(frappe.db.sql("SELECT room_id FROM `tabRoom Stay` AS rs LEFT JOIN `tabReservation` AS r ON rs.reservation_id = r.name where (rs.parent != %s) and (r.status = 'Confirmed' or r.status = 'In House') and ((CONVERT(rs.arrival, DATE) >= %s and CONVERT(rs.arrival, DATE) < %s) or (CONVERT(rs.departure, DATE) > %s and CONVERT(rs.departure, DATE) <= %s) or (CONVERT(rs.arrival, DATE) <= %s and CONVERT(rs.departure, DATE) >= %s))", (filters.get('parent'), filters.get('expected_arrival'), filters.get('expected_departure'), filters.get('expected_arrival'), filters.get('expected_departure'), filters.get('expected_arrival'), filters.get('expected_departure')))))
	
	for room_book in room_book_list:
		for i in range(len(room_list)):
			if room_list[i][0] == room_book[0]:
				del room_list[i]
				break

	return room_list

@frappe.whitelist()
def get_room_type_available(doctype, txt, searchfield, start, page_len, filters):
	room_list = get_room_available(doctype, txt, searchfield, start, page_len, filters)

	tmp = []
	for room in room_list:
		tmp.append(room[1])
	
	tmp = list(set(tmp))

	room_type_list = []
	for t in tmp:
		room_type_list.append([t])

	return room_type_list

@frappe.whitelist()
def get_bed_type_available(doctype, txt, searchfield, start, page_len, filters):
	room_list = get_room_available(doctype, txt, searchfield, start, page_len, filters)

	tmp = []
	for room in room_list:
		if room[1] == filters.get('room_type'):
			tmp.append(room[2])
	
	tmp = list(set(tmp))

	bed_type_list = []
	for t in tmp:
		bed_type_list.append([t])

	return bed_type_list