# -*- coding: utf-8 -*-
# Copyright (c) 2020, PMM and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class HotelShift(Document):
	pass

@frappe.whitelist()
def populate_cash_count():
	return [100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000]

@frappe.whitelist()
def populate_cr_payment():
	cr_payment_detail_list = []
	return_list = []
	mode_of_payment = frappe.get_all('Mode of Payment')
	reservation_list = frappe.get_all('Reservation', filters={'status': ['in', ['In House', 'Finish']]})
	hotel_shift_list = frappe.get_all('Hotel Shift')

	if len(hotel_shift_list) > 0:
		last_shift = frappe.get_last_doc('Hotel Shift')
		if last_shift.status == 'Closed':
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

				# 3. Hotel Bill Payment
				hotel_bill = frappe.get_doc('Hotel Bill', {'reservation_id': reservation_item.name})
				bill_payment_list = hotel_bill.get('bill_payments')
				for bill_payment_item in bill_payment_list:
					if bill_payment_item.creation >= last_shift.time_out:
						cr_payment_detail_doc_from_hbp = frappe.new_doc('CR Payment Detail')
						cr_payment_detail_doc_from_hbp.amount = bill_payment_item.payment_amount
						cr_payment_detail_doc_from_hbp.mode_of_payment = bill_payment_item.mode_of_payment

						cr_payment_detail_list.append(cr_payment_detail_doc_from_hbp)
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

			# 2. Reservation Deposit
			doc_reservation = frappe.get_doc('Reservation', reservation_item.name)
			cr_payment_detail_doc_from_deposit = frappe.new_doc('CR Payment Detail')
			cr_payment_detail_doc_from_deposit.amount = doc_reservation.deposit
			cr_payment_detail_doc_from_deposit.mode_of_payment = doc_reservation.payment_method

			cr_payment_detail_list.append(cr_payment_detail_doc_from_deposit)

			# 3. Hotel Bill Payment
			hotel_bill = frappe.get_doc('Hotel Bill', {'reservation_id': reservation_item.name})
			bill_payment_list = hotel_bill.get('bill_payments')
			for bill_payment_item in bill_payment_list:
				cr_payment_detail_doc_from_hbp = frappe.new_doc('CR Payment Detail')
				cr_payment_detail_doc_from_hbp.amount = bill_payment_item.payment_amount
				cr_payment_detail_doc_from_hbp.mode_of_payment = bill_payment_item.mode_of_payment

				cr_payment_detail_list.append(cr_payment_detail_doc_from_hbp)

	for item in mode_of_payment:
		new_payment_detail = frappe.new_doc('CR Payment Detail')
		new_payment_detail.mode_of_payment = item.name
		new_payment_detail.amount = 0
		for cr_payment_detail_item in cr_payment_detail_list:
			if cr_payment_detail_item.mode_of_payment == new_payment_detail.mode_of_payment:
				new_payment_detail.amount += cr_payment_detail_item.amount
		if new_payment_detail.amount > 0:
			return_list.append(new_payment_detail)

	return return_list

@frappe.whitelist()
def populate_cr_refund():
	return_list = []
	cr_refund = frappe.new_doc('CR Refund Detail')
	cr_refund.type = 'Refund'
	cr_refund.amount = 0

	cr_change = frappe.new_doc('CR Refund Detail')
	cr_change.type = 'Change'
	cr_change.amount = 0

	reservation_list = frappe.get_all('Reservation', filters={'status': ['in', ['In House', 'Finish']]})
	hotel_shift_list = frappe.get_all('Hotel Shift')

	if len(hotel_shift_list) > 0:
		last_shift = frappe.get_last_doc('Hotel Shift')
		if last_shift.status == 'Closed':
			for reservation_item in reservation_list:
				hotel_bill = frappe.get_doc('Hotel Bill', {'reservation_id': reservation_item.name})
				if hotel_bill.creation >= last_shift.time_out:
					# Hotel Bill Change
					cr_change.amount += hotel_bill.bill_rounded_change_amount
					# Room Bill Paid Change
					room_bill_paid_list = hotel_bill.get('room_bill_paid')
					if room_bill_paid_list:
						for rbpd_item in room_bill_paid_list:
							cr_change.amount += rbpd_item.rbpd_rounded_change_amount
				# Hotel Bill Refund
				hotel_bill_refund_list = hotel_bill.get('bill_refund')
				if hotel_bill_refund_list:
					for hbr_item in hotel_bill_refund_list:
						if hbr_item.creation >= last_shift.time_out:
							cr_refund.amount += hbr_item.refund_amount
	else:
		for reservation_item in reservation_list:
			hotel_bill = frappe.get_doc('Hotel Bill', {'reservation_id': reservation_item.name})
			# Hotel Bill Change
			cr_change.amount += hotel_bill.bill_rounded_change_amount
			# Room Bill Paid Change
			room_bill_paid_list = hotel_bill.get('room_bill_paid')
			if room_bill_paid_list:
				for rbpd_item in room_bill_paid_list:
					cr_change.amount += rbpd_item.rbpd_rounded_change_amount
			# Hotel Bill Refund
			hotel_bill_refund_list = hotel_bill.get('bill_refund')
			if hotel_bill_refund_list:
				for hbr_item in hotel_bill_refund_list:
					cr_refund.amount += hbr_item.refund_amount

	if cr_refund.amount > 0:
		return_list.append(cr_refund)
	if cr_change.amount > 0:
		return_list.append(cr_change)
	return return_list


@frappe.whitelist()
def get_cash_balance():
	cr_payment = populate_cr_payment()
	cr_refund = populate_cr_refund()
	total_cash_payment = 0
	total_refund = 0
	for item in cr_refund:
		total_refund += item.amount
	for item in cr_payment:
		if frappe.get_doc('Mode of Payment', item.mode_of_payment).type == 'Cash':
			total_cash_payment += item.amount
	return total_cash_payment - total_refund