# -*- coding: utf-8 -*-
# Copyright (c) 2020, PMM and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import datetime
from frappe.model.document import Document

class HotelShift(Document):
	pass

@frappe.whitelist()
def populate_cash_count():
	return [100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000]

@frappe.whitelist()
def populate_cr_payment(hotel_shift_id, selector):
	cr_payment_detail_list = []
	return_list = []
	transaction_list = []
	mode_of_payment = frappe.get_all('Mode of Payment')
	reservation_list = frappe.get_all('Reservation', filters={'status': ['in', ['In House', 'Finish']]}, fields=['*'])
	hotel_shift_list = frappe.get_all('Hotel Shift')

	if hotel_shift_id:
		last_shift = get_last_closed_shift()	
		if last_shift is None:
			for reservation_item in reservation_list:
				# 1. Room Bill Payment
				rbp_list = frappe.get_all('Room Bill Payments',
										  filters={'parent': reservation_item.name,
												   'is_paid': 1}, fields=['name','mode_of_payment', 'rbp_amount'])
				for rbp_item in rbp_list:
					cr_payment_detail_doc_from_rbp = frappe.new_doc('CR Payment Detail')
					cr_payment_detail_doc_from_rbp.amount = rbp_item.rbp_amount
					cr_payment_detail_doc_from_rbp.mode_of_payment = rbp_item.mode_of_payment

					cr_payment_detail_list.append(cr_payment_detail_doc_from_rbp)
					if selector == 'detail' and rbp_item.rbp_amount != 0:
						crpt_doc = frappe.new_doc('CR Payment Transaction')
						crpt_doc.type = 'Room Bill Payment'
						crpt_doc.trx_id = rbp_item.name
						crpt_doc.reservation_id = reservation_item.name
						crpt_doc.folio_id = frappe.db.get_value('Folio', {'reservation_id': reservation_item.name}, ['name'])
						crpt_doc.customer_id = reservation_item.customer_id
						crpt_doc.account = frappe.db.get_value('Mode of Payment Account',
															   {'parent': rbp_item.mode_of_payment,
																'company': frappe.get_doc(
																	"Global Defaults").default_company},
															   "default_account")
						crpt_doc.amount = rbp_item.rbp_amount
						crpt_doc.user = rbp_item.owner
						transaction_list.append(crpt_doc)


				# 2. Reservation Deposit
				doc_reservation = frappe.get_doc('Reservation', reservation_item.name)
				cr_payment_detail_doc_from_deposit = frappe.new_doc('CR Payment Detail')
				cr_payment_detail_doc_from_deposit.amount = doc_reservation.deposit
				cr_payment_detail_doc_from_deposit.mode_of_payment = doc_reservation.payment_method

				cr_payment_detail_list.append(cr_payment_detail_doc_from_deposit)
				if selector == 'detail' and doc_reservation.deposit != 0:
					crpt_doc = frappe.new_doc('CR Payment Transaction')
					crpt_doc.type = 'Reservation'
					crpt_doc.trx_id = doc_reservation.name
					crpt_doc.reservation_id = doc_reservation.name
					crpt_doc.folio_id = frappe.db.get_value('Folio', {'reservation_id': doc_reservation.name}, ['name'])
					crpt_doc.customer_id = doc_reservation.customer_id
					crpt_doc.account = frappe.db.get_value('Mode of Payment Account',
															   {'parent': doc_reservation.payment_method,
																'company': frappe.get_doc(
																	"Global Defaults").default_company},
															   "default_account")
					crpt_doc.amount = doc_reservation.deposit
					crpt_doc.user = crpt_doc.owner
					transaction_list.append(crpt_doc)

				# 3. Hotel Bill Payment
				hotel_bill = frappe.get_doc('Hotel Bill', {'reservation_id': reservation_item.name})
				bill_payment_list = hotel_bill.get('bill_payments')
				for bill_payment_item in bill_payment_list:
					cr_payment_detail_doc_from_hbp = frappe.new_doc('CR Payment Detail')
					cr_payment_detail_doc_from_hbp.amount = bill_payment_item.payment_amount
					cr_payment_detail_doc_from_hbp.mode_of_payment = bill_payment_item.mode_of_payment

					cr_payment_detail_list.append(cr_payment_detail_doc_from_hbp)
					if selector == 'detail' and bill_payment_item.payment_amount != 0:
						crpt_doc = frappe.new_doc('CR Payment Transaction')
						crpt_doc.type = 'Hotel Bill Payments'
						crpt_doc.trx_id = bill_payment_item.name
						crpt_doc.reservation_id = reservation_item.name
						crpt_doc.folio_id = frappe.db.get_value('Folio', {'reservation_id': reservation_item.name}, ['name'])
						crpt_doc.customer_id = reservation_item.customer_id
						crpt_doc.account = frappe.db.get_value('Mode of Payment Account',
															   {'parent': bill_payment_item.mode_of_payment,
																'company': frappe.get_doc(
																	"Global Defaults").default_company},
															   "default_account")
						crpt_doc.amount = bill_payment_item.payment_amount
						crpt_doc.user = bill_payment_item.owner
						transaction_list.append(crpt_doc)
		else:
			for reservation_item in reservation_list:
				# 1. Room Bill Payment
				rbp_list = frappe.get_all('Room Bill Payments', filters={'creation': ['>=', last_shift.time_out],
																		 'parent': reservation_item.name, 'is_paid': 1},
										  fields=['name', 'mode_of_payment', 'rbp_amount'])
				for rbp_item in rbp_list:
					cr_payment_detail_doc_from_rbp = frappe.new_doc('CR Payment Detail')
					cr_payment_detail_doc_from_rbp.amount = rbp_item.rbp_amount
					cr_payment_detail_doc_from_rbp.mode_of_payment = rbp_item.mode_of_payment

					cr_payment_detail_list.append(cr_payment_detail_doc_from_rbp)
					if selector == 'detail' and rbp_item.rbp_amount != 0:
						crpt_doc = frappe.new_doc('CR Payment Transaction')
						crpt_doc.type = 'Room Bill Payment'
						crpt_doc.trx_id = rbp_item.name
						crpt_doc.reservation_id = reservation_item.name
						crpt_doc.folio_id = frappe.db.get_value('Folio', {'reservation_id': reservation_item.name}, ['name'])
						crpt_doc.customer_id = reservation_item.customer_id
						crpt_doc.account = frappe.db.get_value('Mode of Payment Account',
															   {'parent': rbp_item.mode_of_payment,
																'company': frappe.get_doc(
																	"Global Defaults").default_company},
															   "default_account")
						crpt_doc.amount = rbp_item.rbp_amount
						crpt_doc.user = rbp_item.owner
						transaction_list.append(crpt_doc)

				# 2. Reservation Deposit
				remark = 'Deposit ' + reservation_item.name
				folio_id = frappe.db.get_value('Folio', {'reservation_id': reservation_item.name}, ['name'])
				deposit_folio_trx = frappe.get_doc('Folio Transaction', {'folio_id': folio_id, 'remark': remark})
				if deposit_folio_trx.creation >= last_shift.time_out:
					doc_reservation = frappe.get_doc('Reservation', reservation_item.name)
					cr_payment_detail_doc_from_deposit = frappe.new_doc('CR Payment Detail')
					cr_payment_detail_doc_from_deposit.amount = doc_reservation.deposit
					cr_payment_detail_doc_from_deposit.mode_of_payment = doc_reservation.payment_method

					cr_payment_detail_list.append(cr_payment_detail_doc_from_deposit)
					if selector == 'detail' and doc_reservation.deposit != 0:
						crpt_doc = frappe.new_doc('CR Payment Transaction')
						crpt_doc.type = 'Reservation'
						crpt_doc.trx_id = doc_reservation.name
						crpt_doc.reservation_id = doc_reservation.name
						crpt_doc.folio_id = frappe.db.get_value('Folio', {'reservation_id': doc_reservation.name}, ['name'])
						crpt_doc.customer_id = doc_reservation.customer_id
						crpt_doc.account = frappe.db.get_value('Mode of Payment Account',
																   {'parent': doc_reservation.payment_method,
																	'company': frappe.get_doc(
																		"Global Defaults").default_company},
																   "default_account")
						crpt_doc.amount = doc_reservation.deposit
						crpt_doc.user = crpt_doc.owner
						transaction_list.append(crpt_doc)

				# 3. Hotel Bill Payment
				hotel_bill = frappe.get_doc('Hotel Bill', {'reservation_id': reservation_item.name})
				bill_payment_list = hotel_bill.get('bill_payments')
				for bill_payment_item in bill_payment_list:
					if bill_payment_item.creation >= last_shift.time_out:
						cr_payment_detail_doc_from_hbp = frappe.new_doc('CR Payment Detail')
						cr_payment_detail_doc_from_hbp.amount = bill_payment_item.payment_amount
						cr_payment_detail_doc_from_hbp.mode_of_payment = bill_payment_item.mode_of_payment

						cr_payment_detail_list.append(cr_payment_detail_doc_from_hbp)
						if selector == 'detail' and bill_payment_item.payment_amount != 0:
							crpt_doc = frappe.new_doc('CR Payment Transaction')
							crpt_doc.type = 'Hotel Bill Payments'
							crpt_doc.trx_id = bill_payment_item.name
							crpt_doc.reservation_id = reservation_item.name
							crpt_doc.folio_id = frappe.db.get_value('Folio', {'reservation_id': reservation_item.name}, ['name'])
							crpt_doc.customer_id = reservation_item.customer_id
							crpt_doc.account = frappe.db.get_value('Mode of Payment Account',
																   {'parent': bill_payment_item.mode_of_payment,
																	'company': frappe.get_doc(
																		"Global Defaults").default_company},
																   "default_account")
							crpt_doc.amount = bill_payment_item.payment_amount
							crpt_doc.user = bill_payment_item.owner
							transaction_list.append(crpt_doc)
	else:
		if len(frappe.get_all('Hotel Shift')) > 0:
			last_shift = get_last_closed_shift()
			for reservation_item in reservation_list:
				# 1. Room Bill Payment
				rbp_list = frappe.get_all('Room Bill Payments', filters={'creation': ['>=', last_shift.time_out],
																		 'parent': reservation_item.name, 'is_paid': 1},
										  fields=['mode_of_payment', 'rbp_amount'])
				for rbp_item in rbp_list:
					cr_payment_detail_doc_from_rbp = frappe.new_doc('CR Payment Detail')
					cr_payment_detail_doc_from_rbp.amount = rbp_item.rbp_amount
					cr_payment_detail_doc_from_rbp.mode_of_payment = rbp_item.mode_of_payment

					cr_payment_detail_list.append(cr_payment_detail_doc_from_rbp)
					if selector == 'detail' and rbp_item.rbp_amount != 0:
						crpt_doc = frappe.new_doc('CR Payment Transaction')
						crpt_doc.type = 'Room Bill Payment'
						crpt_doc.trx_id = rbp_item.name
						crpt_doc.reservation_id = reservation_item.name
						crpt_doc.folio_id = frappe.db.get_value('Folio', {'reservation_id': reservation_item.name}, ['name'])
						crpt_doc.customer_id = reservation_item.customer_id
						crpt_doc.account = frappe.db.get_value('Mode of Payment Account',
															   {'parent': rbp_item.mode_of_payment,
																'company': frappe.get_doc(
																	"Global Defaults").default_company},
															   "default_account")
						crpt_doc.amount = rbp_item.rbp_amount
						crpt_doc.user = rbp_item.owner
						transaction_list.append(crpt_doc)

				# 2. Reservation Deposit
				remark = 'Deposit ' + reservation_item.name
				folio_id = frappe.db.get_value('Folio', {'reservation_id': reservation_item.name}, ['name'])
				deposit_folio_trx = frappe.get_doc('Folio Transaction', {'folio_id': folio_id, 'remark': remark})
				if deposit_folio_trx.creation >= last_shift.time_out:
					doc_reservation = frappe.get_doc('Reservation', reservation_item.name)
					cr_payment_detail_doc_from_deposit = frappe.new_doc('CR Payment Detail')
					cr_payment_detail_doc_from_deposit.amount = doc_reservation.deposit
					cr_payment_detail_doc_from_deposit.mode_of_payment = doc_reservation.payment_method

					cr_payment_detail_list.append(cr_payment_detail_doc_from_deposit)
					if selector == 'detail' and doc_reservation.deposit != 0:
						crpt_doc = frappe.new_doc('CR Payment Transaction')
						crpt_doc.type = 'Reservation'
						crpt_doc.trx_id = doc_reservation.name
						crpt_doc.reservation_id = doc_reservation.name
						crpt_doc.folio_id = frappe.db.get_value('Folio', {'reservation_id': doc_reservation.name}, ['name'])
						crpt_doc.customer_id = doc_reservation.customer_id
						crpt_doc.account = frappe.db.get_value('Mode of Payment Account',
																   {'parent': doc_reservation.payment_method,
																	'company': frappe.get_doc(
																		"Global Defaults").default_company},
																   "default_account")
						crpt_doc.amount = doc_reservation.deposit
						crpt_doc.user = crpt_doc.owner
						transaction_list.append(crpt_doc)

				# 3. Hotel Bill Payment
				hotel_bill = frappe.get_doc('Hotel Bill', {'reservation_id': reservation_item.name})
				bill_payment_list = hotel_bill.get('bill_payments')
				for bill_payment_item in bill_payment_list:
					if bill_payment_item.creation >= last_shift.time_out:
						cr_payment_detail_doc_from_hbp = frappe.new_doc('CR Payment Detail')
						cr_payment_detail_doc_from_hbp.amount = bill_payment_item.payment_amount
						cr_payment_detail_doc_from_hbp.mode_of_payment = bill_payment_item.mode_of_payment

						cr_payment_detail_list.append(cr_payment_detail_doc_from_hbp)
						if selector == 'detail' and bill_payment_item.payment_amount != 0:
							crpt_doc = frappe.new_doc('CR Payment Transaction')
							crpt_doc.type = 'Hotel Bill Payments'
							crpt_doc.trx_id = bill_payment_item.name
							crpt_doc.reservation_id = reservation_item.name
							crpt_doc.folio_id = frappe.db.get_value('Folio', {'reservation_id': reservation_item.name}, ['name'])
							crpt_doc.customer_id = reservation_item.customer_id
							crpt_doc.account = frappe.db.get_value('Mode of Payment Account',
																   {'parent': bill_payment_item.mode_of_payment,
																	'company': frappe.get_doc(
																		"Global Defaults").default_company},
																   "default_account")
							crpt_doc.amount = bill_payment_item.payment_amount
							crpt_doc.user = bill_payment_item.owner
							transaction_list.append(crpt_doc)
		else:
			for reservation_item in reservation_list:
				# 1. Room Bill Payment
				rbp_list = frappe.get_all('Room Bill Payments',
										  filters={'parent': reservation_item.name,
												   'is_paid': 1}, fields=['mode_of_payment', 'rbp_amount'])
				for rbp_item in rbp_list:
					cr_payment_detail_doc_from_rbp = frappe.new_doc('CR Payment Detail')
					cr_payment_detail_doc_from_rbp.amount = rbp_item.rbp_amount
					cr_payment_detail_doc_from_rbp.mode_of_payment = rbp_item.mode_of_payment

					cr_payment_detail_list.append(cr_payment_detail_doc_from_rbp)
					if selector == 'detail' and rbp_item.rbp_amount != 0:
						crpt_doc = frappe.new_doc('CR Payment Transaction')
						crpt_doc.type = 'Room Bill Payment'
						crpt_doc.trx_id = rbp_item.name
						crpt_doc.reservation_id = reservation_item.name
						crpt_doc.folio_id = frappe.db.get_value('Folio', {'reservation_id': reservation_item.name}, ['name'])
						crpt_doc.customer_id = reservation_item.customer_id
						crpt_doc.account = frappe.db.get_value('Mode of Payment Account',
															   {'parent': rbp_item.mode_of_payment,
																'company': frappe.get_doc(
																	"Global Defaults").default_company},
															   "default_account")
						crpt_doc.amount = rbp_item.rbp_amount
						crpt_doc.user = rbp_item.owner
						transaction_list.append(crpt_doc)

				# 2. Reservation Deposit
				doc_reservation = frappe.get_doc('Reservation', reservation_item.name)
				cr_payment_detail_doc_from_deposit = frappe.new_doc('CR Payment Detail')
				cr_payment_detail_doc_from_deposit.amount = doc_reservation.deposit
				cr_payment_detail_doc_from_deposit.mode_of_payment = doc_reservation.payment_method

				cr_payment_detail_list.append(cr_payment_detail_doc_from_deposit)
				if selector == 'detail' and doc_reservation.deposit != 0:
					crpt_doc = frappe.new_doc('CR Payment Transaction')
					crpt_doc.type = 'Reservation'
					crpt_doc.trx_id = doc_reservation.name
					crpt_doc.reservation_id = doc_reservation.name
					crpt_doc.folio_id = frappe.db.get_value('Folio', {'reservation_id': doc_reservation.name}, ['name'])
					crpt_doc.customer_id = doc_reservation.customer_id
					crpt_doc.account = frappe.db.get_value('Mode of Payment Account',
															   {'parent': doc_reservation.payment_method,
																'company': frappe.get_doc(
																	"Global Defaults").default_company},
															   "default_account")
					crpt_doc.amount = doc_reservation.deposit
					crpt_doc.user = crpt_doc.owner
					transaction_list.append(crpt_doc)

				# 3. Hotel Bill Payment
				hotel_bill = frappe.get_doc('Hotel Bill', {'reservation_id': reservation_item.name})
				bill_payment_list = hotel_bill.get('bill_payments')
				for bill_payment_item in bill_payment_list:
					cr_payment_detail_doc_from_hbp = frappe.new_doc('CR Payment Detail')
					cr_payment_detail_doc_from_hbp.amount = bill_payment_item.payment_amount
					cr_payment_detail_doc_from_hbp.mode_of_payment = bill_payment_item.mode_of_payment

					cr_payment_detail_list.append(cr_payment_detail_doc_from_hbp)
					if selector == 'detail' and bill_payment_item.payment_amount != 0:
						crpt_doc = frappe.new_doc('CR Payment Transaction')
						crpt_doc.type = 'Hotel Bill Payments'
						crpt_doc.trx_id = bill_payment_item.name
						crpt_doc.reservation_id = reservation_item.name
						crpt_doc.folio_id = frappe.db.get_value('Folio', {'reservation_id': reservation_item.name}, ['name'])
						crpt_doc.customer_id = reservation_item.customer_id
						crpt_doc.account = frappe.db.get_value('Mode of Payment Account',
															   {'parent': bill_payment_item.mode_of_payment,
																'company': frappe.get_doc(
																	"Global Defaults").default_company},
															   "default_account")
						crpt_doc.amount = bill_payment_item.payment_amount
						crpt_doc.user = bill_payment_item.owner
						transaction_list.append(crpt_doc)

	for item in mode_of_payment:
		new_payment_detail = frappe.new_doc('CR Payment Detail')
		new_payment_detail.mode_of_payment = item.name
		new_payment_detail.amount = 0
		for cr_payment_detail_item in cr_payment_detail_list:
			if cr_payment_detail_item.mode_of_payment == new_payment_detail.mode_of_payment:
				new_payment_detail.amount += cr_payment_detail_item.amount
		if new_payment_detail.amount > 0:
			return_list.append(new_payment_detail)
	if selector == 'recap':
		return return_list
	else:
		return transaction_list

@frappe.whitelist()
def populate_cr_refund(hotel_shift_id, selector):
	return_list = []
	transaction_list = []
	cr_refund = frappe.new_doc('CR Refund Detail')
	cr_refund.type = 'Refund'
	cr_refund.amount = 0

	cr_change = frappe.new_doc('CR Refund Detail')
	cr_change.type = 'Change'
	cr_change.amount = 0

	reservation_list = frappe.get_all('Reservation', filters={'status': ['in', ['In House', 'Finish']]}, fields=['*'])

	if hotel_shift_id:
		last_shift = get_last_closed_shift()
		if last_shift is None:
			for reservation_item in reservation_list:
				hotel_bill = frappe.get_doc('Hotel Bill', {'reservation_id': reservation_item.name})
				# Hotel Bill Change
				cr_change.amount += hotel_bill.bill_rounded_change_amount
				if selector == 'detail' and hotel_bill.bill_rounded_change_amount != 0:
					crrt_doc = frappe.new_doc('CR Refund Transaction')
					crrt_doc.type = 'Hotel Bill'
					crrt_doc.trx_id = hotel_bill.name
					crrt_doc.reservation_id = reservation_item.name
					crrt_doc.folio_id = frappe.db.get_value('Folio', {'reservation_id': reservation_item.name}, ['name'])
					crrt_doc.customer_id = reservation_item.customer_id
					crrt_doc.account = frappe.db.get_list('Account', filters={'account_number': '1111.001'})[0].name  # nanti update coa diganti
					crrt_doc.amount = hotel_bill.bill_rounded_change_amount
					crrt_doc.user = crrt_doc.owner
					transaction_list.append(crrt_doc)
				# Room Bill Paid Change
				room_bill_paid_list = hotel_bill.get('room_bill_paid')
				if room_bill_paid_list:
					for rbpd_item in room_bill_paid_list:
						cr_change.amount += rbpd_item.rbpd_rounded_change_amount
						if selector == 'detail' and rbpd_item.rbpd_rounded_change_amount != 0:
							crrt_doc = frappe.new_doc('CR Refund Transaction')
							crrt_doc.type = 'Room Bill Paid'
							crrt_doc.trx_id = rbpd_item.name
							crrt_doc.reservation_id = reservation_item.name
							crrt_doc.folio_id = frappe.db.get_value('Folio', {'reservation_id': reservation_item.name}, ['name'])
							crrt_doc.customer_id = reservation_item.customer_id
							crrt_doc.account = frappe.db.get_list('Account', filters={'account_number': '1111.001'})[0].name #nanti update coa diganti
							crrt_doc.amount = rbpd_item.rbpd_rounded_change_amount
							crrt_doc.user = crrt_doc.owner
							transaction_list.append(crrt_doc)
				# Hotel Bill Refund
				hotel_bill_refund_list = hotel_bill.get('bill_refund')
				if hotel_bill_refund_list:
					for hbr_item in hotel_bill_refund_list:
						cr_refund.amount += hbr_item.refund_amount
						if selector == 'detail':
							if selector == 'detail':
								crrt_doc = frappe.new_doc('CR Refund Transaction')
								crrt_doc.type = 'Hotel Bill Refund'
								crrt_doc.trx_id = hbr_item.name
								crrt_doc.reservation_id = reservation_item.name
								crrt_doc.folio_id = frappe.db.get_value('Folio', {'reservation_id': reservation_item.name}, ['name'])
								crrt_doc.customer_id = reservation_item.customer_id
								crrt_doc.account = hbr_item.account
								crrt_doc.amount = hbr_item.refund_amount
								crrt_doc.user = crrt_doc.owner
								transaction_list.append(crrt_doc)
		else:
			for reservation_item in reservation_list:
				hotel_bill = frappe.get_doc('Hotel Bill', {'reservation_id': reservation_item.name})
				if hotel_bill.creation >= last_shift.time_out:
					# Hotel Bill Change
					cr_change.amount += hotel_bill.bill_rounded_change_amount
					if selector == 'detail' and hotel_bill.bill_rounded_change_amount != 0:
						crrt_doc = frappe.new_doc('CR Refund Transaction')
						crrt_doc.type = 'Hotel Bill'
						crrt_doc.trx_id = hotel_bill.name
						crrt_doc.reservation_id = reservation_item.name
						crrt_doc.folio_id = frappe.db.get_value('Folio', {'reservation_id': reservation_item.name}, ['name'])
						crrt_doc.customer_id = reservation_item.customer_id
						crrt_doc.account = frappe.db.get_list('Account', filters={'account_number': '1111.001'})[0].name  # nanti update coa diganti
						crrt_doc.amount = hotel_bill.bill_rounded_change_amount
						crrt_doc.user = crrt_doc.owner
					transaction_list.append(crrt_doc)
					# Room Bill Paid Change
					room_bill_paid_list = hotel_bill.get('room_bill_paid')
					if room_bill_paid_list:
						for rbpd_item in room_bill_paid_list:
							cr_change.amount += rbpd_item.rbpd_rounded_change_amount
							if selector == 'detail' and rbpd_item.rbpd_rounded_change_amount != 0:
								crrt_doc = frappe.new_doc('CR Refund Transaction')
								crrt_doc.type = 'Room Bill Paid'
								crrt_doc.trx_id = rbpd_item.name
								crrt_doc.reservation_id = reservation_item.name
								crrt_doc.folio_id = frappe.db.get_value('Folio', {'reservation_id': reservation_item.name}, ['name'])
								crrt_doc.customer_id = reservation_item.customer_id
								crrt_doc.account = frappe.db.get_list('Account', filters={'account_number': '1111.001'})[0].name  # nanti update coa diganti
								crrt_doc.amount = rbpd_item.rbpd_rounded_change_amount
								crrt_doc.user = crrt_doc.owner
								transaction_list.append(crrt_doc)
				# Hotel Bill Refund
				hotel_bill_refund_list = hotel_bill.get('bill_refund')
				if hotel_bill_refund_list:
					for hbr_item in hotel_bill_refund_list:
						if hbr_item.creation >= last_shift.time_out:
							cr_refund.amount += hbr_item.refund_amount
							if selector == 'detail':
								crrt_doc = frappe.new_doc('CR Refund Transaction')
								crrt_doc.type = 'Hotel Bill Refund'
								crrt_doc.trx_id = hbr_item.name
								crrt_doc.reservation_id = reservation_item.name
								crrt_doc.folio_id = frappe.db.get_value('Folio', {'reservation_id': reservation_item.name}, ['name'])
								crrt_doc.customer_id = reservation_item.customer_id
								crrt_doc.account = hbr_item.account
								crrt_doc.amount = hbr_item.refund_amount
								crrt_doc.user = crrt_doc.owner
								transaction_list.append(crrt_doc)
	else:
		if len(frappe.get_all('Hotel Shift')) > 0:
			last_shift = get_last_closed_shift()
			for reservation_item in reservation_list:
				hotel_bill = frappe.get_doc('Hotel Bill', {'reservation_id': reservation_item.name})
				if hotel_bill.creation >= last_shift.time_out:
					# Hotel Bill Change
					cr_change.amount += hotel_bill.bill_rounded_change_amount
					if selector == 'detail' and hotel_bill.bill_rounded_change_amount != 0:
						crrt_doc = frappe.new_doc('CR Refund Transaction')
						crrt_doc.type = 'Hotel Bill'
						crrt_doc.trx_id = hotel_bill.name
						crrt_doc.reservation_id = reservation_item.name
						crrt_doc.folio_id = frappe.db.get_value('Folio', {'reservation_id': reservation_item.name}, ['name'])
						crrt_doc.customer_id = reservation_item.customer_id
						crrt_doc.account = frappe.db.get_list('Account', filters={'account_number': '1111.001'})[0].name  # nanti update coa diganti
						crrt_doc.amount = hotel_bill.bill_rounded_change_amount
						crrt_doc.user = crrt_doc.owner
						transaction_list.append(crrt_doc)
					# Room Bill Paid Change
					room_bill_paid_list = hotel_bill.get('room_bill_paid')
					if room_bill_paid_list:
						for rbpd_item in room_bill_paid_list:
							cr_change.amount += rbpd_item.rbpd_rounded_change_amount
							if selector == 'detail' and rbpd_item.rbpd_rounded_change_amount != 0:
								crrt_doc = frappe.new_doc('CR Refund Transaction')
								crrt_doc.type = 'Room Bill Paid'
								crrt_doc.trx_id = rbpd_item.name
								crrt_doc.reservation_id = reservation_item.name
								crrt_doc.folio_id = frappe.db.get_value('Folio', {'reservation_id': reservation_item.name}, ['name'])
								crrt_doc.customer_id = reservation_item.customer_id
								crrt_doc.account = frappe.db.get_list('Account', filters={'account_number': '1111.001'})[0].name #nanti update coa diganti
								crrt_doc.amount = rbpd_item.rbpd_rounded_change_amount
								crrt_doc.user = crrt_doc.owner
								transaction_list.append(crrt_doc)
				# Hotel Bill Refund
				hotel_bill_refund_list = hotel_bill.get('bill_refund')
				if hotel_bill_refund_list:
					for hbr_item in hotel_bill_refund_list:
						if hbr_item.creation >= last_shift.time_out:
							cr_refund.amount += hbr_item.refund_amount
							if selector == 'detail':
								crrt_doc = frappe.new_doc('CR Refund Transaction')
								crrt_doc.type = 'Hotel Bill Refund'
								crrt_doc.trx_id = hbr_item.name
								crrt_doc.reservation_id = reservation_item.name
								crrt_doc.folio_id = frappe.db.get_value('Folio', {'reservation_id': reservation_item.name}, ['name'])
								crrt_doc.customer_id = reservation_item.customer_id
								crrt_doc.account = hbr_item.account
								crrt_doc.amount = hbr_item.refund_amount
								crrt_doc.user = crrt_doc.owner
								transaction_list.append(crrt_doc)
		else:
			for reservation_item in reservation_list:
				hotel_bill = frappe.get_doc('Hotel Bill', {'reservation_id': reservation_item.name})
				# Hotel Bill Change
				cr_change.amount += hotel_bill.bill_rounded_change_amount
				if selector == 'detail':
					crrt_doc = frappe.new_doc('CR Refund Transaction')
					crrt_doc.type = 'Hotel Bill'
					crrt_doc.trx_id = hotel_bill.name
					crrt_doc.reservation_id = reservation_item.name
					crrt_doc.folio_id = frappe.db.get_value('Folio', {'reservation_id': reservation_item.name}, ['name'])
					crrt_doc.customer_id = reservation_item.customer_id
					crrt_doc.account = frappe.db.get_list('Account', filters={'account_number': '1111.001'})[0].name  # nanti update coa diganti
					crrt_doc.amount = hotel_bill.bill_rounded_change_amount
					crrt_doc.user = crrt_doc.owner
					transaction_list.append(crrt_doc)
				# Room Bill Paid Change
				room_bill_paid_list = hotel_bill.get('room_bill_paid')
				if room_bill_paid_list:
					for rbpd_item in room_bill_paid_list:
						cr_change.amount += rbpd_item.rbpd_rounded_change_amount
						if selector == 'detail':
							crrt_doc = frappe.new_doc('CR Refund Transaction')
							crrt_doc.type = 'Room Bill Paid'
							crrt_doc.trx_id = rbpd_item.name
							crrt_doc.reservation_id = reservation_item.name
							crrt_doc.folio_id = frappe.db.get_value('Folio', {'reservation_id': reservation_item.name}, ['name'])
							crrt_doc.customer_id = reservation_item.customer_id
							crrt_doc.account = frappe.db.get_list('Account', filters={'account_number': '1111.001'})[0].name #nanti update coa diganti
							crrt_doc.amount = rbpd_item.rbpd_rounded_change_amount
							crrt_doc.user = crrt_doc.owner
							transaction_list.append(crrt_doc)
				# Hotel Bill Refund
				hotel_bill_refund_list = hotel_bill.get('bill_refund')
				if hotel_bill_refund_list:
					for hbr_item in hotel_bill_refund_list:
						cr_refund.amount += hbr_item.refund_amount
						if selector == 'detail':
							crrt_doc = frappe.new_doc('CR Refund Transaction')
							crrt_doc.type = 'Hotel Bill Refund'
							crrt_doc.trx_id = hbr_item.name
							crrt_doc.reservation_id = reservation_item.name
							crrt_doc.folio_id = frappe.db.get_value('Folio', {'reservation_id': reservation_item.name}, ['name'])
							crrt_doc.customer_id = reservation_item.customer_id
							crrt_doc.account = hbr_item.account
							crrt_doc.amount = hbr_item.refund_amount
							crrt_doc.user = crrt_doc.owner
							transaction_list.append(crrt_doc)

	if cr_refund.amount > 0:
		return_list.append(cr_refund)
	if cr_change.amount > 0:
		return_list.append(cr_change)

	if selector == 'recap':
		return return_list
	else:
		return transaction_list

@frappe.whitelist()
def get_cash_balance(hotel_shift_id):
	cr_payment = populate_cr_payment(hotel_shift_id, 'recap')
	cr_refund = populate_cr_refund(hotel_shift_id, 'recap')
	total_cash_payment = 0
	total_refund = 0
	for item in cr_refund:
		total_refund += item.amount
	for item in cr_payment:
		if frappe.get_doc('Mode of Payment', item.mode_of_payment).type == 'Cash':
			total_cash_payment += item.amount
	return total_cash_payment - total_refund

@frappe.whitelist()
def is_there_open_hotel_shift():
	if frappe.get_all('Hotel Shift', {'status': 'Open'}):
		return 1
	else:
		return 2

@frappe.whitelist()
def close_shift(hotel_shift_id):
	doc = frappe.get_doc('Hotel Shift', hotel_shift_id)
	doc.time_out = datetime.datetime.now()
	if frappe.get_doc('Employee', {'user_id': frappe.session.user}):
		doc.employee = frappe.db.get_value('Employee', {'user_id': frappe.session.user}, ['name'])
		doc.employee_name = frappe.db.get_value('Employee', {'user_id': frappe.session.user}, ['employee_name'])

	doc.status = 'Closed'
	doc.save()

	if frappe.db.get_value('Hotel Shift', {'name': hotel_shift_id}, ['status']) == 'Closed':
		return True
	else:
		return False


def get_last_closed_shift():
	d = frappe.get_all('Hotel Shift', filters={'status': 'Closed'}, order_by='creation desc', limit_page_length=1)
	if d:
		return frappe.get_doc('Hotel Shift', d[0].name)
	else:
		return None