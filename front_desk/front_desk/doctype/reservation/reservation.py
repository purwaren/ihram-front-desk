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
from front_desk.front_desk.doctype.hotel_bill.hotel_bill import get_mode_of_payment_account
from front_desk.front_desk.doctype.room_stay.room_stay import add_early_checkin
from front_desk.front_desk.doctype.room_stay.room_stay import add_late_checkout
from front_desk.front_desk.doctype.room_stay.room_stay import get_rate_after_tax
from front_desk.front_desk.doctype.room_stay.room_stay import calculate_room_stay_bill
from front_desk.front_desk.doctype.room_rate.room_rate import rewrite_breakdown_summary


class Reservation(Document):
	pass


def is_weekday():
	weekno = datetime.datetime.today().weekday()

	if weekno < 5:
		return True
	else:
		return False


@frappe.whitelist()
def check_in(reservation_id_list):
	reservation_id_list = json.loads(reservation_id_list)

	for reservation_id in reservation_id_list:
		if frappe.db.get_value('Reservation', reservation_id, 'status') == 'Reserved':
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
	return frappe.utils.get_url_to_form('Hotel Bill',
										frappe.db.get_value('Hotel Bill', {'reservation_id': reservation_id}, ['name']))


@frappe.whitelist()
def create_deposit_journal_entry(reservation_id, amount, debit_account_name):
	credit_account_name = get_credit_account_name()
	folio_name = frappe.db.get_value('Folio', {'reservation_id': reservation_id}, ['name'])
	remark = 'Deposit ' + reservation_id
	exist_deposit_folio_trx = frappe.db.exists('Folio Transaction', {'parent': folio_name, 'remark': remark})

	if not exist_deposit_folio_trx:
		# JOURNAL ENTRY CREATION: DEPOSIT
		doc_journal_entry = frappe.new_doc('Journal Entry')
		doc_journal_entry.voucher_type = 'Journal Entry'
		doc_journal_entry.naming_series = 'ACC-JV-.YYYY.-'
		doc_journal_entry.posting_date = datetime.date.today()
		doc_journal_entry.company = frappe.get_doc("Global Defaults").default_company
		doc_journal_entry.remark = remark
		doc_journal_entry.user_remark = remark

		doc_debit = frappe.new_doc('Journal Entry Account')
		doc_debit.account = debit_account_name
		doc_debit.debit = amount
		doc_debit.debit_in_account_currency = amount
		doc_debit.user_remark = remark

		doc_credit = frappe.new_doc('Journal Entry Account')
		doc_credit.account = credit_account_name
		doc_credit.credit = amount
		doc_credit.credit_in_account_currency = amount
		doc_credit.user_remark = remark

		doc_journal_entry.append('accounts', doc_debit)
		doc_journal_entry.append('accounts', doc_credit)

		doc_journal_entry.save()
		doc_journal_entry.submit()

		doc_folio = frappe.get_doc('Folio', folio_name)

		doc_folio_transaction = frappe.new_doc('Folio Transaction')
		doc_folio_transaction.folio_id = doc_folio.name
		doc_folio_transaction.amount = amount
		doc_folio_transaction.amount_after_tax = amount
		doc_folio_transaction.flag = 'Credit'
		doc_folio_transaction.account_id = credit_account_name
		doc_folio_transaction.against_account_id = debit_account_name
		doc_folio_transaction.remark = remark
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
	if frappe.db.get_value('Reservation', reservation_id, 'status') == 'Reserved':
		reservation = frappe.get_doc('Reservation', reservation_id)
		reservation.status = "Cancel"
		# TODO: free room in tabRoom Booking
		reservation.save()

		# update room booking status
		update_by_reservation(reservation_id)


@frappe.whitelist()
def checkout_reservation(reservation_id):
	is_bill_paid = frappe.db.get_value('Hotel Bill', {'reservation_id': reservation_id}, ['is_paid'])
	reservation = frappe.get_doc('Reservation', reservation_id)
	if frappe.db.get_value('Reservation', reservation_id, 'status') == 'In House':
		if is_using_city_ledger(reservation_id):
			input_city_ledger_payment_to_journal_entry(reservation_id)

		if float(reservation.room_bill_amount) == 0:
			if is_bill_paid == 1:
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
				hotel_room.save()

				# Update room booking status
				update_by_reservation(reservation_id)

				# Update Room Bill Amount and Hotel Bill Amount
				rba = 0.0
				hba = 0.0

				folio = frappe.get_doc('Folio', {'reservation_id': reservation_id})
				folio_trx = folio.get('transaction_detail')
				for ft_item in folio_trx:
					if "Auto Room Charge:" in ft_item.remark:
						rba += ft_item.amount_after_tax

				hotel_bill = frappe.get_doc('Hotel Bill', {'reservation_id': reservation_id})
				bill_breakdown = hotel_bill.get('bill_breakdown')
				for bb_item in bill_breakdown:
					if bb_item.is_folio_trx_pairing == 1 and bb_item.is_tax_item == 0 and bb_item.is_excluded == 0:
						hba += bb_item.breakdown_grand_total

				frappe.db.set_value('Folio', folio.name, 'room_bill_amount', rba)
				frappe.db.set_value('Folio', folio.name, 'hotel_bill_amount', hba)
				return 1
			else:
				return 0
		else:
			return 2


@frappe.whitelist()
def auto_release_reservation_at_six_pm():
	reservation_list = frappe.get_all('Reservation', {'status': 'Reserved', 'is_guaranteed': 0})
	for reservation in reservation_list:
		reservation_detail_list = frappe.get_all('Reservation Detail', filters={'parent': reservation.name},
												 fields=['expected_arrival'])
		arrival_expired = False
		for rd in reservation_detail_list:
			if rd.expected_arrival < datetime.datetime.today().date():
				arrival_expired = True
				room_booking_id = frappe.db.get_value('Room Booking', {'reference_name': rd.name}, ['name'])
				if room_booking_id:
					frappe.db.set_value('Room Booking', room_booking_id, 'status', 'Canceled')

		if arrival_expired:
			frappe.db.set_value('Reservation', reservation.name, 'status', 'Cancel')
			update_by_reservation(reservation.name)


def auto_room_charge():
	reservation_list = frappe.get_all('Reservation', {'status': 'In House'})
	for reservation in reservation_list:
		create_room_charge(reservation.name)


@frappe.whitelist()
def create_room_charge(reservation_id):
	room_stay_list = frappe.get_all('Room Stay', filters={"reservation_id": reservation_id}, fields=["*"])
	cust_name = frappe.get_doc('Customer', frappe.get_doc('Reservation', reservation_id).customer_id).name

	if len(room_stay_list) > 0:
		for room_stay in room_stay_list:
			# check if this room_stay is moved, if the moving took part in the same day, do not charge the room
			room_is_moved_at_the_same_day = False
			is_moved = frappe.db.exists('Move Room', {'initial_room_stay': room_stay.name})
			if is_moved and room_stay.departure.date() == room_stay.arrival.date():
				room_is_moved_at_the_same_day = True

			# add special charge if any
			add_early_checkin(room_stay.name)
			add_late_checkout(room_stay.name)

			# create room charge, if today is not departure day yet and the room_stay is not moved at the same day
			if room_stay.arrival <= datetime.datetime.today() and room_stay.departure > datetime.datetime.today() and not room_is_moved_at_the_same_day:
				room_rate = frappe.get_doc('Room Rate', {'name': room_stay.room_rate})
				room_name = room_stay.room_id
				if not room_stay.discount_percentage:
					room_stay_discount = 0
				else:
					room_stay_discount = float(room_stay.discount_percentage) / 100.0
				amount_multiplier = 1 - room_stay_discount
				room_rate_breakdown = frappe.get_all('Room Rate Breakdown', filters={'parent': room_stay.room_rate},
													 fields=['*'])
				remark = 'Auto Room Charge:' + room_name + " - " + datetime.datetime.today().strftime("%d/%m/%Y")
				je_debit_account = frappe.db.get_list('Account', filters={'account_number': '2121.002'})[0].name
				je_credit_account = frappe.db.get_list('Account', filters={'account_number': '4320.001'})[0].name

				# define room rate for folio transaction. If room stay discount exist, apply the discount
				if is_weekday():
					today_rate = room_rate.rate_weekday * amount_multiplier
					today_rate_after_tax = get_rate_after_tax(room_rate.name, 'Weekday Rate',
															  room_stay.discount_percentage, room_stay.actual_weekday_rate)
				else:
					today_rate = room_rate.rate_weekend * amount_multiplier
					today_rate_after_tax = get_rate_after_tax(room_rate.name, 'Weekend Rate',
															  room_stay.discount_percentage, room_stay.actual_weekend_rate)
				# !!IMPORTANTE!! sepertinya masukin ke journal entry ketika billing selesai saja. pas saat ini cukup create folio transaction yang sesuai jumlahnya after tax
				# for rrbd_item in room_rate_breakdown:
				# 	rrbd_remark = rrbd_item.breakdown_name + ' of Auto Room Charge:' + room_name + " - " + datetime.datetime.today().strftime("%d/%m/%Y")
				# 	# Weekday room charge
				# 	if is_weekday():
				# 		# exclude the weekend rate
				# 		if rrbd_item.breakdown_name != 'Weekend Rate':
				# 			# define each of every rate breakdown amount. If room stay discount exist, apply the discount
				# 			rrbd_rate_amount = amount_multiplier * float(rrbd_item.breakdown_amount) * float(rrbd_item.breakdown_qty)
				#
				# 			# Create Journal Entry
				# 			doc_journal_entry = frappe.new_doc('Journal Entry')
				# 			doc_journal_entry.title = rrbd_item.breakdown_name + ' of Auto Room Charge:' + reservation_id + ': ' + room_name
				# 			doc_journal_entry.voucher_type = 'Journal Entry'
				# 			doc_journal_entry.naming_series = 'ACC-JV-.YYYY.-'
				# 			doc_journal_entry.posting_date = datetime.date.today()
				# 			doc_journal_entry.company = frappe.get_doc("Global Defaults").default_company
				# 			doc_journal_entry.total_amount_currency = frappe.get_doc("Global Defaults").default_currency
				# 			doc_journal_entry.remark = rrbd_remark
				# 			doc_journal_entry.user_remark = rrbd_remark
				# 			# Journal Entry Account: Debit
				# 			doc_debit = frappe.new_doc('Journal Entry Account')
				# 			doc_debit.account = je_debit_account
				# 			doc_debit.debit = rrbd_rate_amount
				# 			doc_debit.debit_in_account_currency = rrbd_rate_amount
				# 			doc_debit.party_type = 'Customer'
				# 			doc_debit.party = cust_name
				# 			doc_debit.user_remark = rrbd_remark
				# 			# Journal Entry Account: Credit
				# 			doc_credit = frappe.new_doc('Journal Entry Account')
				# 			doc_credit.account = rrbd_item.breakdown_account
				# 			doc_credit.credit = rrbd_rate_amount
				# 			doc_credit.party_type = 'Customer'
				# 			doc_credit.party = cust_name
				# 			doc_credit.credit_in_account_currency = rrbd_rate_amount
				# 			doc_credit.user_remark = rrbd_remark
				# 			# Append debit and credit to Journal Account
				# 			doc_journal_entry.append('accounts', doc_debit)
				# 			doc_journal_entry.append('accounts', doc_credit)
				# 			# Save and Submit Journal Entry
				# 			doc_journal_entry.save()
				# 			doc_journal_entry.submit()
				# 	# Weekend room charge
				# 	else:
				# 		# exclude the weekday rate
				# 		if rrbd_item.breakdown_name != 'Weekday Rate':
				# 			# define each of every rate breakdown amount. If room stay discount exist, apply the discount
				# 			rrbd_rate_amount = amount_multiplier * float(rrbd_item.breakdown_amount) * float(rrbd_item.breakdown_qty)
				# 			# Create Journal Entry
				# 			doc_journal_entry = frappe.new_doc('Journal Entry')
				# 			doc_journal_entry.title = rrbd_item.breakdown_name + ' of Auto Room Charge:' + reservation_id + ': ' + room_name
				# 			doc_journal_entry.voucher_type = 'Journal Entry'
				# 			doc_journal_entry.naming_series = 'ACC-JV-.YYYY.-'
				# 			doc_journal_entry.posting_date = datetime.date.today()
				# 			doc_journal_entry.company = frappe.get_doc("Global Defaults").default_company
				# 			doc_journal_entry.total_amount_currency = frappe.get_doc("Global Defaults").default_currency
				# 			doc_journal_entry.remark = rrbd_remark
				# 			doc_journal_entry.user_remark = rrbd_remark
				# 			# Journal Entry Account: Debit
				# 			doc_debit = frappe.new_doc('Journal Entry Account')
				# 			doc_debit.account = rrbd_item.breakdown_account
				# 			doc_debit.debit = rrbd_rate_amount
				# 			doc_debit.debit_in_account_currency = rrbd_rate_amount
				# 			doc_debit.party_type = 'Customer'
				# 			doc_debit.party = cust_name
				# 			doc_debit.user_remark = rrbd_remark
				# 			# Journal Entry Account: Credit
				# 			doc_credit = frappe.new_doc('Journal Entry Account')
				# 			doc_credit.account = je_credit_account
				# 			doc_credit.credit = rrbd_rate_amount
				# 			doc_credit.party_type = 'Customer'
				# 			doc_credit.party = cust_name
				# 			doc_credit.credit_in_account_currency = rrbd_rate_amount
				# 			doc_credit.user_remark = rrbd_remark
				# 			# Append debit and credit to Journal Account
				# 			doc_journal_entry.append('accounts', doc_debit)
				# 			doc_journal_entry.append('accounts', doc_credit)
				# 			# Save and Submit Journal Entry
				# 			doc_journal_entry.save()
				# 			doc_journal_entry.submit()

				# Create Folio Transaction of Room Charge
				folio_name = frappe.db.get_value('Folio', {'reservation_id': reservation_id}, ['name'])
				doc_folio = frappe.get_doc('Folio', folio_name)

				doc_folio_transaction = frappe.new_doc('Folio Transaction')
				doc_folio_transaction.creation = datetime.datetime.today()
				doc_folio_transaction.folio_id = doc_folio.name
				doc_folio_transaction.amount = today_rate
				doc_folio_transaction.amount_after_tax = today_rate_after_tax
				doc_folio_transaction.room_stay_id = room_stay.name
				doc_folio_transaction.room_rate = room_stay.room_rate
				doc_folio_transaction.flag = 'Debit'
				doc_folio_transaction.account_id = je_debit_account
				doc_folio_transaction.against_account_id = je_credit_account
				doc_folio_transaction.remark = remark
				doc_folio_transaction.is_void = 0
				doc_folio_transaction.transaction_detail = rewrite_breakdown_summary(room_rate.name,
																					 room_stay.actual_weekday_rate,
																					 room_stay.actual_weekend_rate)

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
			je_debit_account = frappe.db.get_list('Account', filters={'account_number': '1132.001'})[0].name
			je_credit_account = frappe.db.get_list('Account', filters={'account_number': '4320.001'})[0].name
			remark = ac_item.name + " -  Additional Charge " + reservation_id + " " + ac_item.ac_description
			folio_name = frappe.db.get_value('Folio', {'reservation_id': reservation_id}, ['name'])
			doc_folio = frappe.get_doc('Folio', folio_name)

			exist_folio_trx_ac = frappe.db.exists('Folio Transaction',
												  {'parent': doc_folio.name,
												   'remark': remark})
			if not exist_folio_trx_ac:
				# JOURNAL ENTRY CREATION: ADDITIONAL CHARGE
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
				doc_folio_transaction.amount_after_tax = ac_item.ac_amount
				doc_folio_transaction.flag = 'Debit'
				doc_folio_transaction.account_id = je_debit_account
				doc_folio_transaction.against_account_id = je_credit_account
				doc_folio_transaction.room_stay_id = ac_item.room_stay_id
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
			# Exist Move Room
			if frappe.db.get_value('Move Room', {'replacement_room_stay': rs_item.name}, ['name']):
				move_room = frappe.get_doc('Move Room',
										   frappe.db.get_value('Move Room', {'replacement_room_stay': rs_item.name},
															   ['name']))
				initial_rs = frappe.get_doc('Room Stay', move_room.initial_room_stay)
				replacement_rs = frappe.get_doc('Room Stay', move_room.replacement_room_stay)
				if replacement_rs.room_bill_paid_id is None:
					room_bill_amount = room_bill_amount + (
								initial_rs.total_bill_amount + replacement_rs.total_bill_amount - initial_rs.old_total_bill_amount)
			# Default condition, no move room yet
			elif not rs_item.room_bill_paid_id:
				room_bill_amount = room_bill_amount + rs_item.total_bill_amount

	doc.room_bill_amount = room_bill_amount

def fill_actual_room_rate(doc, method):
	room_stay = doc.get('room_stay')
	if len(room_stay) > 0:
		for rs_item in room_stay:
			if rs_item.override_rate == 0:
				rs_item.actual_weekday_rate = rs_item.weekday_rate
				rs_item.actual_weekend_rate = rs_item.weekend_rate
			else:
				if rs_item.actual_weekday_rate == 0 and rs_item.actual_weekend_rate == 0:
					rs_item.override_rate = 0
				if rs_item.actual_weekday_rate == 0:
					rs_item.actual_weekday_rate = rs_item.weekday_rate
				if rs_item.actual_weekend_rate == 0:
					rs_item.actual_weekend_rate = rs_item.weekend_rate

def create_after_cleaning(doc, method):
	room_stay = doc.get('room_stay')
	if len(room_stay) > 0:
		for rs_item in room_stay:
			exist_after_cleaning = frappe.db.exists('After Cleaning', {'room_stay_id': rs_item.name})
			if not exist_after_cleaning:
				after_cleaning = frappe.new_doc('After Cleaning')
				after_cleaning.room_stay_id = rs_item.name
				after_cleaning.hotel_room_id = rs_item.room_id
				after_cleaning.room_status = frappe.get_doc('Hotel Room', rs_item.room_id).status
				after_cleaning.reservation_id = rs_item.reservation_id
				after_cleaning.save()

@frappe.whitelist()
def recalculate_room_bill_amount_after_guest_requested_move_room(reservation_id):
	reservation = frappe.get_doc('Reservation', reservation_id)
	room_bill_amount = 0.0
	room_stay = reservation.get('room_stay')
	if len(room_stay) > 0:
		for rs_item in room_stay:
			# Exist Move Room
			if frappe.db.get_value('Move Room', {'replacement_room_stay': rs_item.name}, ['name']):
				move_room = frappe.get_doc('Move Room',
										   frappe.db.get_value('Move Room', {'replacement_room_stay': rs_item.name},
															   ['name']))
				initial_rs = frappe.get_doc('Room Stay', move_room.initial_room_stay)
				replacement_rs = frappe.get_doc('Room Stay', move_room.replacement_room_stay)
				if replacement_rs.room_bill_paid_id is None:
					room_bill_amount = room_bill_amount + (
								initial_rs.total_bill_amount + replacement_rs.total_bill_amount - initial_rs.old_total_bill_amount)

	reservation.room_bill_amount = room_bill_amount
	reservation.save()


@frappe.whitelist()
def create_room_bill_payment_entry(reservation_id, room_bill_amount, paid_bill_amount, is_round_down_checked,
								   change_rounding_amount, change_amount, rounded_change_amount):
	updated_room_bill_amount = 0
	reservation = frappe.get_doc('Reservation', reservation_id)
	folio_name = frappe.db.get_value('Folio', {'reservation_id': reservation_id}, ['name'])
	doc_folio = frappe.get_doc('Folio', folio_name)
	rbpd_remark = "Payment for: \n"
	rbp_list = frappe.get_all('Room Bill Payments', filters={'parent': reservation_id, 'is_paid': 0}, fields=["*"])
	room_stay_list = frappe.get_all('Room Stay', filters={'reservation_id': reservation_id}, fields=["*"])
	kas_dp_kamar = frappe.db.get_list('Account', filters={'account_number': '2121.002'})[0].name
	kas_pendapatan_kamar = frappe.db.get_list('Account', filters={'account_number': '4320.001'})[0].name

	# Create Room Bill Paid Entry for this "MAKE PAYMENT" action
	doc_rbpd = frappe.new_doc('Room Bill Paid')
	doc_rbpd.rbpd_bill_amount = room_bill_amount
	doc_rbpd.rbpd_paid_bill_amount = paid_bill_amount
	doc_rbpd.rbpd_is_rounded_down_change = is_round_down_checked
	doc_rbpd.rbpd_change_rounding_amount = change_rounding_amount
	doc_rbpd.rbpd_change_amount = change_amount
	doc_rbpd.rbpd_rounded_change_amount = rounded_change_amount

	# Save the Room Bill Paid and Clear the Current Bill Amount that needed to be paid
	reservation.append('room_bill_paid', doc_rbpd)
	reservation.room_bill_amount = 0
	reservation.paid_bill_amount = 0
	reservation.is_round_change_amount = 0
	reservation.rbp_change_rounding_amount = 0
	reservation.room_bill_change_amount = 0
	reservation.rbp_rounded_change_amount = 0
	reservation.save()

	# Update the Room Stay that already paid by Room Bill Paid Above, by filling the room_bill_paid_id
	for room_stay_item in room_stay_list:
		if room_stay_item.room_bill_paid_id is None:
			frappe.db.set_value('Room Stay', room_stay_item.name, 'room_bill_paid_id', doc_rbpd.name)
			room_remark = " - Room Stay: " + room_stay_item.name + " - Room No. " + room_stay_item.room_id + "\n"
			rbpd_remark = rbpd_remark + room_remark

	# Update the room bill paid remark
	frappe.db.set_value('Room Bill Paid', doc_rbpd.name, 'rbpd_remark', rbpd_remark)

	# Create Folio Transaction and Journal Entry for all the Room Bill Payment related to current Room Bill Paid Entry
	for rbp_item in rbp_list:
		credit_account_name = kas_dp_kamar
		debit_account_name = get_mode_of_payment_account(rbp_item.mode_of_payment,
														 frappe.get_doc("Global Defaults").default_company)
		amount = rbp_item.rbp_amount
		remark = 'Room Bill Payment: ' + doc_rbpd.name + ' (' + rbp_item.mode_of_payment + ') - Reservation: ' + reservation_id
		exist_folio_trx_rbp_item = frappe.db.exists('Folio Transaction',
													{'parent': doc_folio.name,
													 'remark': remark})
		if not exist_folio_trx_rbp_item:
			if rbp_item.mode_of_payment != 'City Ledger':
				# JOURNAL ENTRY CREATION: ROOM BILL PAYMENT
				doc_journal_entry = frappe.new_doc('Journal Entry')
				doc_journal_entry.voucher_type = 'Journal Entry'
				doc_journal_entry.naming_series = 'ACC-JV-.YYYY.-'
				doc_journal_entry.posting_date = datetime.date.today()
				doc_journal_entry.company = frappe.get_doc("Global Defaults").default_company
				doc_journal_entry.remark = remark
				doc_journal_entry.user_remark = remark
				doc_debit = frappe.new_doc('Journal Entry Account')
				doc_debit.account = debit_account_name
				doc_debit.debit = amount
				doc_debit.debit_in_account_currency = amount
				doc_debit.user_remark = remark

				doc_credit = frappe.new_doc('Journal Entry Account')
				doc_credit.account = credit_account_name
				doc_credit.credit = amount
				doc_credit.credit_in_account_currency = amount
				doc_credit.user_remark = remark
				doc_journal_entry.append('accounts', doc_debit)
				doc_journal_entry.append('accounts', doc_credit)

				doc_journal_entry.save()
				doc_journal_entry.submit()

			doc_folio_transaction = frappe.new_doc('Folio Transaction')
			doc_folio_transaction.folio_id = doc_folio.name
			doc_folio_transaction.amount = amount
			doc_folio_transaction.amount_after_tax = amount
			doc_folio_transaction.flag = 'Credit'
			doc_folio_transaction.account_id = credit_account_name
			doc_folio_transaction.against_account_id = debit_account_name
			doc_folio_transaction.remark = remark
			doc_folio_transaction.is_void = 0

			doc_folio.append('transaction_detail', doc_folio_transaction)
			doc_folio.save()

			# Set the indicator that these Room Bill Payments already been paid by connecting the room_bill_paid_id and
			# set the is_paid flag to 1
			frappe.db.set_value('Room Bill Payments', rbp_item.name, 'room_bill_paid_id', doc_rbpd.name)
			frappe.db.set_value('Room Bill Payments', rbp_item.name, 'is_paid', 1)

		# Create Journal Entry for Room Bill Paid Change if there is any Change
		if float(doc_rbpd.rbpd_rounded_change_amount) > 0:
			rbpd_change_remark = "Change from " + doc_rbpd.name
			kas_kecil = frappe.db.get_list('Account', filters={'account_number': '1111.001'})[0].name
			kas_dp_kamar = frappe.db.get_list('Account', filters={'account_number': '2121.002'})[0].name

			# JOURNAL ENTRY CREATION ROOM BILL PAID CHANGE
			change_doc_journal_entry = frappe.new_doc('Journal Entry')
			change_doc_journal_entry.voucher_type = 'Journal Entry'
			change_doc_journal_entry.naming_series = 'ACC-JV-.YYYY.-'
			change_doc_journal_entry.posting_date = datetime.date.today()
			change_doc_journal_entry.company = frappe.get_doc("Global Defaults").default_company
			change_doc_journal_entry.remark = rbpd_change_remark
			change_doc_journal_entry.user_remark = rbpd_change_remark

			change_doc_debit = frappe.new_doc('Journal Entry Account')
			change_doc_debit.account = kas_dp_kamar
			change_doc_debit.debit = doc_rbpd.rbpd_rounded_change_amount
			change_doc_debit.party_type = 'Customer'
			change_doc_debit.party = reservation.customer_id
			change_doc_debit.debit_in_account_currency = doc_rbpd.rbpd_rounded_change_amount
			change_doc_debit.user_remark = rbpd_change_remark

			change_doc_credit = frappe.new_doc('Journal Entry Account')
			change_doc_credit.account = kas_kecil
			change_doc_credit.credit = doc_rbpd.rbpd_rounded_change_amount
			change_doc_credit.credit_in_account_currency = doc_rbpd.rbpd_rounded_change_amount
			change_doc_credit.user_remark = rbpd_change_remark
			change_doc_credit.party_type = 'Customer'
			change_doc_credit.party = reservation.customer_id
			change_doc_journal_entry.append('accounts', change_doc_debit)
			change_doc_journal_entry.append('accounts', change_doc_credit)

			change_doc_journal_entry.save()
			change_doc_journal_entry.submit()

			change_doc_folio_transaction = frappe.new_doc('Folio Transaction')
			change_doc_folio_transaction.folio_id = doc_folio.name
			change_doc_folio_transaction.amount = doc_rbpd.rbpd_rounded_change_amount
			change_doc_folio_transaction.amount_after_tax = doc_rbpd.rbpd_rounded_change_amount
			change_doc_folio_transaction.flag = 'Debit'
			change_doc_folio_transaction.account_id = kas_dp_kamar
			change_doc_folio_transaction.against_account_id = kas_kecil
			change_doc_folio_transaction.remark = rbpd_change_remark
			change_doc_folio_transaction.is_void = 0

			doc_folio.append('transaction_detail', change_doc_folio_transaction)

			if int(doc_rbpd.rbpd_is_rounded_down_change) == 1:
				rounded_down_doc_ft = frappe.new_doc('Folio Transaction')
				rounded_down_doc_ft.folio_id = doc_folio.name
				rounded_down_doc_ft.amount = doc_rbpd.rbpd_change_rounding_amount
				rounded_down_doc_ft.amount_after_tax = doc_rbpd.rbpd_change_rounding_amount
				rounded_down_doc_ft.flag = 'Debit'
				rounded_down_doc_ft.account_id = kas_pendapatan_kamar
				rounded_down_doc_ft.against_account_id = kas_dp_kamar
				rounded_down_doc_ft.remark = "Rounded Down Change Amount from " + doc_rbpd.name
				rounded_down_doc_ft.is_void = 0
				doc_folio.append('transaction_detail', rounded_down_doc_ft)

			doc_folio.save()

	# Calculate the room bill amount that still not paid yet ~ I feel this unnecessary tho
	for room_stay_item in room_stay_list:
		if not room_stay_item.room_bill_paid_id:
			updated_room_bill_amount = updated_room_bill_amount + room_stay_item.total_bill_amount

	# AR City Ledger
	if is_using_city_ledger(reservation_id):
		total_amount = 0.0
		for rbp_item in rbp_list:
			if rbp_item.mode_of_payment == 'City Ledger':
				total_amount = total_amount + float(rbp_item.rbp_amount)

		doc_ar_city_ledger = frappe.new_doc('AR City Ledger')
		doc_ar_city_ledger.naming_series = 'FO-AR-CL-.YYYY.-'
		doc_ar_city_ledger.is_paid = 0
		doc_ar_city_ledger.reservation_id = reservation_id
		doc_ar_city_ledger.customer_name = reservation.customer_id
		doc_ar_city_ledger.hotel_order_channel = reservation.hotel_order_channel
		doc_ar_city_ledger.folio_id = frappe.db.get_value('Folio', {'reservation_id': reservation_id}, ['name'])
		doc_ar_city_ledger.is_room_charge_only = 1
		doc_ar_city_ledger.total_amount = total_amount
		doc_ar_city_ledger.save()

	return updated_room_bill_amount


@frappe.whitelist()
def trigger_room_charge(reservation_id):
	room_stay_list = frappe.get_all('Room Stay', filters={"reservation_id": reservation_id}, fields=["*"])

	if len(room_stay_list) > 0:
		for room_stay in room_stay_list:
			# check if this room_stay is moved, if the moving took part in the same day, do not charge the room
			room_is_moved_at_the_same_day = False
			is_moved = frappe.db.exists('Move Room', {'initial_room_stay': room_stay.name})
			if is_moved and room_stay.departure.date() == room_stay.arrival.date():
				room_is_moved_at_the_same_day = True

			# add special charge if any
			add_early_checkin(room_stay.name)
			add_late_checkout(room_stay.name)

			# create room charge, if today is not departure day yet and the room_stay is not moved at the same day
			if room_stay.departure > datetime.datetime.today() and not room_is_moved_at_the_same_day:
				room_rate = frappe.get_doc('Room Rate', {'name': room_stay.room_rate})
				room_name = room_stay.room_id
				if not room_stay.discount_percentage:
					room_stay_discount = 0
				else:
					room_stay_discount = float(room_stay.discount_percentage) / 100.0
				amount_multiplier = 1 - room_stay_discount
				remark = 'Auto Room Charge:' + room_name + " - " + datetime.datetime.today().strftime("%d/%m/%Y")
				je_debit_account = frappe.db.get_list('Account', filters={'account_number': '2121.002'})[0].name
				je_credit_account = frappe.db.get_list('Account', filters={'account_number': '4320.001'})[0].name

				# define room rate for folio transaction. If room stay discount exist, apply the discount
				if is_weekday():
					today_rate = room_rate.rate_weekday * amount_multiplier
					today_rate_after_tax = get_rate_after_tax(room_rate.name, 'Weekday Rate',
															  room_stay.discount_percentage, room_stay.actual_weekday_rate)
				else:
					today_rate = room_rate.rate_weekend * amount_multiplier
					today_rate_after_tax = get_rate_after_tax(room_rate.name, 'Weekend Rate',
															  room_stay.discount_percentage, room_stay.actual_weekend_rate)

				# Create Folio Transaction of Room Charge
				folio_name = frappe.db.get_value('Folio', {'reservation_id': reservation_id}, ['name'])
				doc_folio = frappe.get_doc('Folio', folio_name)

				doc_folio_transaction = frappe.new_doc('Folio Transaction')
				doc_folio_transaction.creation = datetime.datetime.today()
				doc_folio_transaction.folio_id = doc_folio.name
				doc_folio_transaction.amount = today_rate
				doc_folio_transaction.amount_after_tax = today_rate_after_tax
				doc_folio_transaction.room_stay_id = room_stay.name
				doc_folio_transaction.room_rate = room_stay.room_rate
				doc_folio_transaction.flag = 'Debit'
				doc_folio_transaction.account_id = je_debit_account
				doc_folio_transaction.against_account_id = je_credit_account
				doc_folio_transaction.remark = remark
				doc_folio_transaction.is_void = 0
				doc_folio_transaction.transaction_detail = rewrite_breakdown_summary(room_rate.name,
																					 room_stay.actual_weekday_rate,
																					 room_stay.actual_weekend_rate)

				doc_folio.append('transaction_detail', doc_folio_transaction)
				doc_folio.save()


def is_using_city_ledger(reservation_id):
	city_ledger_flag = False
	rbp_list = frappe.get_all('Room Bill Payments', filters={'parent': reservation_id},
							  fields=["mode_of_payment"])

	for rbp_item in rbp_list:
		if rbp_item.mode_of_payment == 'City Ledger':
			city_ledger_flag = True

	return city_ledger_flag


def input_city_ledger_payment_to_journal_entry(reservation_id):
	rbp_list = frappe.get_all('Room Bill Payments',
							  filters={'parent': reservation_id, 'mode_of_payment': 'City Ledger'},
							  fields=["*"])
	for rbp_item in rbp_list:
		credit_account_name = frappe.db.get_list('Account', filters={'account_number': '2121.002'})[0].name
		debit_account_name = get_mode_of_payment_account(rbp_item.mode_of_payment,
														 frappe.get_doc("Global Defaults").default_company)
		remark = 'Room Bill Payment: ' + rbp_item.room_bill_paid_id + ' (' + rbp_item.mode_of_payment + ') - Reservation: ' + reservation_id
		folio_name = frappe.db.get_value('Folio', {'reservation_id': reservation_id}, ['name'])
		amount = frappe.db.get_value('Folio Transaction', {'parent': folio_name, 'remark': remark},
									 ['amount_after_tax'])
		cust_name = frappe.get_doc('Reservation', reservation_id).customer_id
		# JOURNAL ENTRY CREATION: CITY LEDGER PAYMENT. LIKELY WLL NOT BE USED
		doc_journal_entry = frappe.new_doc('Journal Entry')
		doc_journal_entry.voucher_type = 'Journal Entry'
		doc_journal_entry.naming_series = 'ACC-JV-.YYYY.-'
		doc_journal_entry.posting_date = datetime.date.today()
		doc_journal_entry.company = frappe.get_doc("Global Defaults").default_company
		doc_journal_entry.remark = remark
		doc_journal_entry.user_remark = remark

		doc_debit = frappe.new_doc('Journal Entry Account')
		doc_debit.account = debit_account_name
		doc_debit.debit = amount
		doc_debit.debit_in_account_currency = amount
		doc_debit.user_remark = remark
		doc_debit.party_type = 'Customer'
		doc_debit.party = cust_name

		doc_credit = frappe.new_doc('Journal Entry Account')
		doc_credit.account = credit_account_name
		doc_credit.credit = amount
		doc_credit.credit_in_account_currency = amount
		doc_credit.user_remark = remark
		doc_credit.party_type = 'Customer'
		doc_credit.party = cust_name

		doc_journal_entry.append('accounts', doc_debit)
		doc_journal_entry.append('accounts', doc_credit)

		doc_journal_entry.save()
		doc_journal_entry.submit()


@frappe.whitelist()
def cancel_individual_reservation(reservation_id):
	reservation = frappe.get_doc('Reservation', reservation_id)
	cust_name = frappe.get_doc('Customer', reservation.customer_id).name
	folio = frappe.get_doc('Folio', {'reservation_id': reservation_id})
	if not frappe.db.exists('Hotel Bill', {'reservation_id': reservation_id}):
		create_hotel_bill(reservation_id)
	hotel_bill = frappe.get_doc('Hotel Bill', {'reservation_id': reservation_id})
	remark = "Cancellation Fee - Reservation: " + reservation_id
	kas_pendapatan_kamar = frappe.db.get_list('Account', filters={'account_number': '4320.001'})[0].name
	piutang_lain2 = frappe.db.get_list('Account', filters={'account_number': '1132.001'})[0].name

	total_rbpd = 0.0
	rbpd_list = reservation.get('room_bill_paid')
	for rbpd_item in rbpd_list:
		total_rbpd += rbpd_item.rbpd_bill_amount

	total_room_charge = 0.0
	folio_trx_list = folio.get('transaction_detail')
	for folio_trx_item in folio_trx_list:
		if 'Auto Room Charge:' in folio_trx_item.remark:
			total_room_charge += folio_trx_item.amount_after_tax

	room_stay_list = frappe.get_all('Room Stay', filters={'reservation_id': reservation_id}, order_by="arrival asc",
									fields=['*'])
	arrival_date = room_stay_list[0].arrival.date()
	cancel_date = datetime.datetime.now().date()

	# Cancellation date must be greater or equals than arrival date
	if cancel_date < arrival_date:
		frappe.msgprint("Cannot Cancel Room Stay that not yet happened.")
	else:
		# Cancellation with room charge exist
		if arrival_date < cancel_date:
			# cancellation fee = 50% of One Day Room Charge
			cancellation_fee = calculate_room_stay_bill(
				datetime.datetime.strftime(room_stay_list[0].arrival, "%Y-%m-%d %H:%M:%S"),
				datetime.datetime.strftime(room_stay_list[0].arrival + datetime.timedelta(days=1), "%Y-%m-%d %H:%M:%S"),
				room_stay_list[0].room_rate,
				room_stay_list[0].discount_percentage) * 0.5
			# room refund
			refund_amount = total_rbpd - cancellation_fee
		# Cancellation without room charge exist
		else:
			# cancellation fee = 50% of Total Room Bill
			cancellation_fee = total_rbpd * 0.5
			# room refund
			refund_amount = total_rbpd - total_room_charge - cancellation_fee

		# Cancellation Fee Folio Transaction
		fee_folio_trx = frappe.new_doc('Folio Transaction')
		fee_folio_trx.folio_id = folio.name
		fee_folio_trx.amount = cancellation_fee
		fee_folio_trx.flag = 'Debit'
		fee_folio_trx.amount_after_tax = cancellation_fee
		fee_folio_trx.account_id = piutang_lain2
		fee_folio_trx.against_account_id = kas_pendapatan_kamar
		fee_folio_trx.room_stay_id = room_stay_list[0].name
		fee_folio_trx.remark = remark
		fee_folio_trx.is_additional_charge = 1
		fee_folio_trx.is_void = 0
		folio.append('transaction_detail', fee_folio_trx)
		folio.save()

		# Cancellation Fee Journal Entry
		# JOURNAL ENTRY CREATION: CANCELLATION FEE
		doc_journal_entry = frappe.new_doc('Journal Entry')
		doc_journal_entry.title = fee_folio_trx.name + remark
		doc_journal_entry.voucher_type = 'Journal Entry'
		doc_journal_entry.naming_series = 'ACC-JV-.YYYY.-'
		doc_journal_entry.posting_date = datetime.date.today()
		doc_journal_entry.company = frappe.get_doc("Global Defaults").default_company
		doc_journal_entry.total_amount_currency = frappe.get_doc("Global Defaults").default_currency
		doc_journal_entry.remark = remark
		doc_journal_entry.user_remark = remark

		doc_debit = frappe.new_doc('Journal Entry Account')
		doc_debit.account = piutang_lain2
		doc_debit.debit = cancellation_fee
		doc_debit.debit_in_account_currency = cancellation_fee
		doc_debit.party_type = 'Customer'
		doc_debit.party = cust_name
		doc_debit.user_remark = remark

		doc_credit = frappe.new_doc('Journal Entry Account')
		doc_credit.account = kas_pendapatan_kamar
		doc_credit.credit = cancellation_fee
		doc_credit.credit_in_account_currency = cancellation_fee
		doc_credit.party_type = 'Customer'
		doc_credit.party = cust_name
		doc_credit.user_remark = remark

		doc_journal_entry.append('accounts', doc_debit)
		doc_journal_entry.append('accounts', doc_credit)

		doc_journal_entry.save()
		doc_journal_entry.submit()

		# Cancellation Fee Hotel Bill Breakdown - Apakah Sebaiknya dipindah di Hotel Bill aja biar jadi satu?
		fee_bill_breakdown = frappe.new_doc('Hotel Bill Breakdown')
		fee_bill_breakdown.is_tax_item = 0
		fee_bill_breakdown.is_folio_trx_pairing = 1
		fee_bill_breakdown.is_excluded = 1
		fee_bill_breakdown.billing_folio_trx_id = fee_folio_trx.name
		fee_bill_breakdown.breakdown_description = remark
		fee_bill_breakdown.breakdown_net_total = cancellation_fee
		fee_bill_breakdown.breakdown_grand_total = cancellation_fee
		fee_bill_breakdown.breakdown_tax_amount = 0
		fee_bill_breakdown.breakdown_account = kas_pendapatan_kamar
		fee_bill_breakdown.breakdown_account_against = piutang_lain2
		hotel_bill.append('bill_breakdown', fee_bill_breakdown)
		hotel_bill.save()

		# Cancellation Hotel Bill Refund
		refund_description = 'Refund Room Payment of Reservation: ' + reservation_id
		kas_dp_kamar = frappe.db.get_list('Account', filters={'account_number': '2121.002'})[0].name
		kas_fo = frappe.db.get_list('Account', filters={'account_number': '1111.003'})[0].name

		exist_this_refund_item = frappe.db.exists('Hotel Bill Refund',
												  {'parent': hotel_bill.name,
												   'refund_description': refund_description})
		if not exist_this_refund_item:
			refund_item = frappe.new_doc('Hotel Bill Refund')
			refund_item.naming_series = 'FO-BILL-RFND-.YYYY.-'
			refund_item.refund_amount = refund_amount
			refund_item.refund_description = refund_description
			refund_item.is_refunded = 0
			refund_item.account = kas_fo
			refund_item.account_against = kas_dp_kamar

			hotel_bill.append('bill_refund', refund_item)
			hotel_bill.save()

		return 1


# Kalo butuh populate rba
@frappe.whitelist()
def populate_ba_of_all_folio():
	folio_list = frappe.get_all('Folio')
	if len(folio_list) > 0:
		for item in folio_list:
			polio = frappe.get_doc('Folio', item.name)
			ft_list = polio.get('transaction_detail')
			rba = 0
			hba = 0
			if ft_list:
				for ft_item in ft_list:
					if "Auto Room Charge:" in ft_item.remark:
						rba += ft_item.amount_after_tax
			polio.room_bill_amount = 0.0 + rba

			hotel_bill = frappe.get_doc('Hotel Bill', {'reservation_id': polio.reservation_id})
			bill_breakdown = hotel_bill.get('bill_breakdown')
			for bb_item in bill_breakdown:
				if bb_item.is_folio_trx_pairing == 1 and bb_item.is_tax_item == 0 and bb_item.is_excluded == 0:
					hba += bb_item.breakdown_grand_total

			frappe.db.set_value('Folio', polio.name, 'room_bill_amount', rba)
			frappe.db.set_value('Folio', polio.name, 'hotel_bill_amount', hba)

	frappe.msgprint("Folio's Room Biil Amount & Hotel Bill Amount populated")

@frappe.whitelist()
def get_all_room_id_in_reservation(reservation_id):
	return_list = []

	room_stay_list = frappe.get_doc('Reservation', reservation_id).get('room_stay')
	for item in room_stay_list:
		return_list.append(item.room_id)

	return return_list
