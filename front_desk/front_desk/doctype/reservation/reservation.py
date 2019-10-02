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
from front_desk.front_desk.doctype.hotel_bill.hotel_bill import create_hotel_bill
from front_desk.front_desk.doctype.room_stay.room_stay import add_early_checkin
from front_desk.front_desk.doctype.room_stay.room_stay import add_late_checkout

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
def get_folio_url(reservation_id):
	return frappe.utils.get_url_to_form('Folio', frappe.db.get_value('Folio',
															{'reservation_id': reservation_id},
															['name'])
										)

@frappe.whitelist()
def get_hotel_bill_url(reservation_id):
	create_hotel_bill(reservation_id)
	return frappe.utils.get_url_to_form('Hotel Bill', frappe.db.get_value('Hotel Bill', {'reservation_id': reservation_id}, ['name']))

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
def get_debit_account(doctype, txt, searchfield, start, page_len, filters):
	debit_account = []

	temp = frappe.db.get_list('Account',
		filters={
			'account_number': '1111.003'
		}
	)

	if len(temp) > 0:
		debit_account.append([temp[0].name])
	
	temp = frappe.db.get_list('Account',
		filters={
			'account_number': ['like', '1121.0%'], 'account_type': 'Bank'
		}
	)

	for t in temp:
		debit_account.append([t.name])

	return debit_account

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

@frappe.whitelist()
def auto_release_reservation_at_six_pm():
	reservation_list = frappe.get_all('Reservation', {'status': 'Created', 'is_guaranteed': 0})
	for reservation in reservation_list:
		reservation_detail_list = frappe.get_all('Reservation Detail', filters={'parent': reservation.name}, fields=['expected_arrival'])
		arrival_expired = False
		for rd in reservation_detail_list:
			if rd.expected_arrival < datetime.datetime.today().date():
				arrival_expired = True

		if arrival_expired:
			frappe.db.set_value('Reservation', reservation.name, 'status', 'Cancel')


def auto_room_charge():
	reservation_list = frappe.get_all('Reservation', {'status': 'In House'})
	for reservation in reservation_list:
		create_room_charge(reservation.name)

@frappe.whitelist()
def create_room_charge(reservation_id):
	room_stay_list = frappe.get_all('Room Stay',
									filters={"reservation_id": reservation_id},
									fields=["name","room_rate", "room_id", "departure","discount_percentage"]
									)
	cust_name = frappe.get_doc('Customer', frappe.get_doc('Reservation', reservation_id).customer_id).name

	if len(room_stay_list) > 0:
		for room_stay in room_stay_list:
			# add special charge if any
			add_early_checkin(room_stay.name)
			add_late_checkout(room_stay.name)

			# create room charge, if today is not departure day yet
			if room_stay.departure > datetime.datetime.today():
				room_rate = frappe.get_doc('Room Rate', {'name':room_stay.room_rate})
				room_name = room_stay.room_id
				if not room_stay.discount_percentage:
					room_stay_discount = 0
				else:
					room_stay_discount = float(room_stay.discount_percentage) / 100.0
				amount_multiplier = 1 - room_stay_discount
				room_rate_breakdown = frappe.get_all('Room Rate Breakdown', filters={'parent':room_stay.room_rate}, fields=['*'])
				remark = 'Auto Room Charge:' + room_name + " - " + datetime.datetime.today().strftime("%d/%m/%Y")
				je_credit_account = frappe.db.get_list('Account', filters={'account_number': '1132.001'})[0].name
				je_debit_account = frappe.db.get_list('Account', filters={'account_number': '4320.001'})[0].name

				# define room rate for folio transaction. If room stay discount exist, apply the discount
				if is_weekday():
					today_rate = room_rate.rate_weekday * amount_multiplier
				else:
					today_rate = room_rate.rate_weekend * amount_multiplier
				for rrbd_item in room_rate_breakdown:
					rrbd_remark = rrbd_item.breakdown_name + ' of Auto Room Charge:' + room_name + " - " + datetime.datetime.today().strftime("%d/%m/%Y")
					# Weekday room charge
					if is_weekday():
						# exclude the weekend rate
						if rrbd_item.breakdown_name != 'Weekend Rate':
							# define each of every rate breakdown amount. If room stay discount exist, apply the discount
							rrbd_rate_amount = amount_multiplier * float(rrbd_item.breakdown_amount) * float(rrbd_item.breakdown_qty)

							# Create Journal Entry
							doc_journal_entry = frappe.new_doc('Journal Entry')
							doc_journal_entry.title = rrbd_item.breakdown_name + ' of Auto Room Charge:' + reservation_id + ': ' + room_name
							doc_journal_entry.voucher_type = 'Journal Entry'
							doc_journal_entry.naming_series = 'ACC-JV-.YYYY.-'
							doc_journal_entry.posting_date = datetime.date.today()
							doc_journal_entry.company = frappe.get_doc("Global Defaults").default_company
							doc_journal_entry.total_amount_currency = frappe.get_doc("Global Defaults").default_currency
							doc_journal_entry.remark = rrbd_remark
							doc_journal_entry.user_remark = rrbd_remark
							# Journal Entry Account: Debit
							doc_debit = frappe.new_doc('Journal Entry Account')
							doc_debit.account = rrbd_item.breakdown_account
							doc_debit.debit = rrbd_rate_amount
							doc_debit.debit_in_account_currency = rrbd_rate_amount
							doc_debit.party_type = 'Customer'
							doc_debit.party = cust_name
							doc_debit.user_remark = rrbd_remark
							# Journal Entry Account: Credit
							doc_credit = frappe.new_doc('Journal Entry Account')
							doc_credit.account = je_credit_account
							doc_credit.credit = rrbd_rate_amount
							doc_credit.party_type = 'Customer'
							doc_credit.party = cust_name
							doc_credit.credit_in_account_currency = rrbd_rate_amount
							doc_credit.user_remark = rrbd_remark
							# Append debit and credit to Journal Account
							doc_journal_entry.append('accounts', doc_debit)
							doc_journal_entry.append('accounts', doc_credit)
							# Save and Submit Journal Entry
							doc_journal_entry.save()
							doc_journal_entry.submit()
					# Weekend room charge
					else:
						# exclude the weekday rate
						if rrbd_item.breakdown_name != 'Weekday Rate':
							# define each of every rate breakdown amount. If room stay discount exist, apply the discount
							rrbd_rate_amount = amount_multiplier * float(rrbd_item.breakdown_amount) * float(rrbd_item.breakdown_qty)
							# Create Journal Entry
							doc_journal_entry = frappe.new_doc('Journal Entry')
							doc_journal_entry.title = rrbd_item.breakdown_name + ' of Auto Room Charge:' + reservation_id + ': ' + room_name
							doc_journal_entry.voucher_type = 'Journal Entry'
							doc_journal_entry.naming_series = 'ACC-JV-.YYYY.-'
							doc_journal_entry.posting_date = datetime.date.today()
							doc_journal_entry.company = frappe.get_doc("Global Defaults").default_company
							doc_journal_entry.total_amount_currency = frappe.get_doc("Global Defaults").default_currency
							doc_journal_entry.remark = rrbd_remark
							doc_journal_entry.user_remark = rrbd_remark
							# Journal Entry Account: Debit
							doc_debit = frappe.new_doc('Journal Entry Account')
							doc_debit.account = rrbd_item.breakdown_account
							doc_debit.debit = rrbd_rate_amount
							doc_debit.debit_in_account_currency = rrbd_rate_amount
							doc_debit.party_type = 'Customer'
							doc_debit.party = cust_name
							doc_debit.user_remark = rrbd_remark
							# Journal Entry Account: Credit
							doc_credit = frappe.new_doc('Journal Entry Account')
							doc_credit.account = je_credit_account
							doc_credit.credit = rrbd_rate_amount
							doc_credit.party_type = 'Customer'
							doc_credit.party = cust_name
							doc_credit.credit_in_account_currency = rrbd_rate_amount
							doc_credit.user_remark = rrbd_remark
							# Append debit and credit to Journal Account
							doc_journal_entry.append('accounts', doc_debit)
							doc_journal_entry.append('accounts', doc_credit)
							# Save and Submit Journal Entry
							doc_journal_entry.save()
							doc_journal_entry.submit()

				# Create Folio Transaction of Room Charge
				folio_name = frappe.db.get_value('Folio', {'reservation_id': reservation_id}, ['name'])
				doc_folio = frappe.get_doc('Folio', folio_name)

				doc_folio_transaction = frappe.new_doc('Folio Transaction')
				doc_folio_transaction.folio_id = doc_folio.name
				doc_folio_transaction.amount = today_rate
				doc_folio_transaction.room_stay_id = room_stay.name
				doc_folio_transaction.room_rate = room_stay.room_rate
				doc_folio_transaction.flag = 'Debit'
				doc_folio_transaction.account_id = je_debit_account
				doc_folio_transaction.against_account_id = je_credit_account
				doc_folio_transaction.remark = remark
				doc_folio_transaction.is_void = 0
				doc_folio_transaction.transaction_detail = room_rate.breakdown_summary

				doc_folio.append('transaction_detail', doc_folio_transaction)
				doc_folio.save()

@frappe.whitelist()
def create_special_charge(reservation_id):
	room_stay_list = frappe.get_all('Room Stay',
									filters={"reservation_id": reservation_id},
									fields=["name", "room_rate", "room_id", "departure"]
									)
	if len(room_stay_list) > 0:
		for room_stay in room_stay_list:
			add_early_checkin(room_stay.name)
			add_late_checkout(room_stay.name)

def auto_additional_charge():
	reservation_list = frappe.get_all('Reservation', {'status': 'In House'})
	for reservation in reservation_list:
		create_additional_charge(reservation.name)

@frappe.whitelist()
def create_additional_charge(reservation_id):
	ac_list = frappe.get_all('Additional Charge',
							 filters={'parent': reservation_id},
							 fields=['*']
							 )
	if len(ac_list) > 0:
		for ac_item in ac_list:
			cust_name = frappe.get_doc('Customer', frappe.get_doc('Reservation', reservation_id).customer_id).name
			je_credit_account = frappe.db.get_list('Account', filters={'account_number': '1132.001'})[0].name
			je_debit_account = frappe.db.get_list('Account', filters={'account_number': '4320.001'})[0].name
			remark = ac_item.name + " -  Additional Charge " + reservation_id + " " + ac_item.ac_description
			folio_name = frappe.db.get_value('Folio', {'reservation_id': reservation_id}, ['name'])
			doc_folio = frappe.get_doc('Folio', folio_name)

			exist_folio_trx_ac = frappe.db.exists('Folio Transaction',
												  {'parent': doc_folio.name,
												   'remark': remark})
			if not exist_folio_trx_ac:
				doc_journal_entry = frappe.new_doc('Journal Entry')
				doc_journal_entry.title = ac_item.name + " Additional Charge of Reservation: " + reservation_id
				doc_journal_entry.voucher_type = 'Journal Entry'
				doc_journal_entry.naming_series = 'ACC-JV-.YYYY.-'
				doc_journal_entry.posting_date = datetime.date.today()
				doc_journal_entry.company = frappe.get_doc("Global Defaults").default_company
				doc_journal_entry.total_amount_currency = frappe.get_doc("Global Defaults").default_currency
				doc_journal_entry.remark = remark
				doc_journal_entry.user_remark = remark

				doc_debit = frappe.new_doc('Journal Entry Account')
				doc_debit.account = je_debit_account
				doc_debit.debit = ac_item.ac_amount
				doc_debit.debit_in_account_currency = ac_item.ac_amount
				doc_debit.party_type = 'Customer'
				doc_debit.party = cust_name
				doc_debit.user_remark = remark

				doc_credit = frappe.new_doc('Journal Entry Account')
				doc_credit.account = je_credit_account
				doc_credit.credit = ac_item.ac_amount
				doc_credit.party_type = 'Customer'
				doc_credit.party = cust_name
				doc_credit.credit_in_account_currency = ac_item.ac_amount
				doc_credit.user_remark = remark

				doc_journal_entry.append('accounts', doc_debit)
				doc_journal_entry.append('accounts', doc_credit)

				doc_journal_entry.save()
				doc_journal_entry.submit()

				doc_folio_transaction = frappe.new_doc('Folio Transaction')
				doc_folio_transaction.folio_id = doc_folio.name
				doc_folio_transaction.amount = ac_item.ac_amount
				doc_folio_transaction.flag = 'Debit'
				doc_folio_transaction.account_id = je_debit_account
				doc_folio_transaction.against_account_id = je_credit_account
				doc_folio_transaction.remark = remark
				doc_folio_transaction.is_additional_charge = 1
				doc_folio_transaction.is_void = 0

				doc_folio.append('transaction_detail', doc_folio_transaction)
				doc_folio.save()

def calculate_room_bill_amount(doc, method):
	room_bill_amount = 0.0
	room_stay = doc.get('room_stay')
	if len(room_stay) > 0:
		for rs_item in room_stay:
			room_bill_amount = room_bill_amount + rs_item.total_bill_amount

	doc.room_bill_amount = room_bill_amount