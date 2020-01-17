# -*- coding: utf-8 -*-
# Copyright (c) 2019, PMM and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import datetime
from frappe.model.document import Document
from front_desk.front_desk.doctype.hotel_tax.hotel_tax import calculate_hotel_tax_and_charges
from front_desk.front_desk.doctype.folio.folio import get_deposit_amount
from front_desk.front_desk.doctype.folio.folio import copy_trx_from_sales_invoice_to_folio_transaction
from front_desk.front_desk.doctype.room_stay.room_stay import add_early_checkin
from front_desk.front_desk.doctype.room_stay.room_stay import add_late_checkout
from front_desk.front_desk.doctype.room_stay.room_stay import checkout_early_refund

class HotelBill(Document):
	pass


def is_this_weekday(the_date):
	weekno = the_date.weekday()
	if weekno < 5:
		return True
	else:
		return False

def calculate_bill_total(doc, method):
	hotel_bill_net_total = 0
	hotel_bill_tax_amount = 0
	hotel_bill_grand_total = 0

	bill_breakdown_list = doc.get('bill_breakdown')
	for bb_item in bill_breakdown_list:
		if bb_item.is_folio_trx_pairing == 1 and bb_item.is_excluded == 0:
			hotel_bill_net_total = hotel_bill_net_total + bb_item.breakdown_net_total
			hotel_bill_tax_amount = hotel_bill_tax_amount + bb_item.breakdown_tax_amount
			hotel_bill_grand_total = hotel_bill_grand_total + bb_item.breakdown_grand_total

	doc.bill_net_total = hotel_bill_net_total
	doc.bill_tax_amount = hotel_bill_tax_amount
	doc.bill_grand_total = hotel_bill_grand_total

def check_special_charge(reservation_id):
	room_stay_list = frappe.get_all('Room Stay',
									filters={"reservation_id": reservation_id},
									fields=["name", "room_rate", "room_id", "departure"]
									)
	if len(room_stay_list) > 0:
		for room_stay in room_stay_list:
			add_early_checkin(room_stay.name)
			add_late_checkout(room_stay.name)

def create_additional_charge(reservation_id):
	ac_list = frappe.get_all('Additional Charge',
							 filters={'parent': reservation_id},
							 fields=['*']
							 )
	if len(ac_list) > 0:
		for ac_item in ac_list:
			cust_name = frappe.get_doc('Customer', frappe.get_doc('Reservation', reservation_id).customer_id).name
			je_debit_account = frappe.db.get_list('Account', filters={'account_number': '1133.002'})[0].name
			je_credit_account = frappe.db.get_list('Account', filters={'account_number': '4210.001'})[0].name
			remark = ac_item.name + " -  Additional Charge " + reservation_id + " " + ac_item.ac_description
			folio_name = frappe.db.get_value('Folio', {'reservation_id': reservation_id}, ['name'])
			doc_folio = frappe.get_doc('Folio', folio_name)

			exist_folio_trx_ac = frappe.db.exists('Folio Transaction',
												  {'parent': doc_folio.name,
												   'remark': remark})
			if not exist_folio_trx_ac:
				# JOURNAL ENTRY CREATION: ADDITIONAL CHARGE
				# doc_journal_entry = frappe.new_doc('Journal Entry')
				# doc_journal_entry.title = ac_item.name + " Additional Charge of Reservation: " + reservation_id
				# doc_journal_entry.voucher_type = 'Journal Entry'
				# doc_journal_entry.naming_series = 'ACC-JV-.YYYY.-'
				# doc_journal_entry.posting_date = datetime.date.today()
				# doc_journal_entry.company = frappe.get_doc("Global Defaults").default_company
				# doc_journal_entry.total_amount_currency = frappe.get_doc("Global Defaults").default_currency
				# doc_journal_entry.remark = remark
				# doc_journal_entry.user_remark = remark
				#
				# doc_debit = frappe.new_doc('Journal Entry Account')
				# doc_debit.account = je_debit_account
				# doc_debit.debit = ac_item.ac_amount
				# doc_debit.debit_in_account_currency = ac_item.ac_amount
				# doc_debit.party_type = 'Customer'
				# doc_debit.party = cust_name
				# doc_debit.user_remark = remark
				#
				# doc_credit = frappe.new_doc('Journal Entry Account')
				# doc_credit.account = je_credit_account
				# doc_credit.credit = ac_item.ac_amount
				# doc_credit.party_type = 'Customer'
				# doc_credit.party = cust_name
				# doc_credit.credit_in_account_currency = ac_item.ac_amount
				# doc_credit.user_remark = remark
				#
				# doc_journal_entry.append('accounts', doc_debit)
				# doc_journal_entry.append('accounts', doc_credit)
				#
				# doc_journal_entry.save()
				# doc_journal_entry.submit()

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

@frappe.whitelist()
def update_hotel_bill(reservation_id):
	create_hotel_bill(reservation_id)
	bill_name = frappe.db.get_value('Hotel Bill', {'reservation_id': reservation_id}, ['name'])
	return "Hotel Bill " + bill_name + " Updated."

def create_hotel_bill(reservation_id):
	deposit_refund_amount = 0
	exist_bill = frappe.db.get_value('Hotel Bill', {'reservation_id': reservation_id}, ['name'])

	doc_folio = frappe.get_doc('Folio', frappe.db.get_value('Folio', {'reservation_id': reservation_id}, ['name']))

	# create all transaction that may occur after scheduler copy to folio trx
	# create_special_charge(reservation_id)
	# copy_trx_from_sales_invoice_to_folio_transaction(reservation_id)
	copy_trx_from_sales_invoice_to_folio_transaction(reservation_id)
	check_special_charge(reservation_id)
	create_additional_charge(reservation_id)

	folio_trx_list = frappe.get_all('Folio Transaction', filters={'folio_id': doc_folio.name, 'flag': 'Debit'},
									fields=["*"])

	customer_deposit = get_deposit_amount(reservation_id)

	if not exist_bill:
		new_doc_hotel_bill = frappe.new_doc('Hotel Bill')
		new_doc_hotel_bill.naming_series = 'FO-BILL-.YYYY.-'
		new_doc_hotel_bill.reservation_id = reservation_id
		new_doc_hotel_bill.customer_id = frappe.get_doc('Reservation', reservation_id).customer_id
		new_doc_hotel_bill.bill_deposit_amount = customer_deposit
		new_doc_hotel_bill.save()
		exist_bill = new_doc_hotel_bill.name

	if exist_bill:
		for item in folio_trx_list:
			doc_hotel_bill = frappe.get_doc("Hotel Bill", {'name': exist_bill})
			kas_dp_kamar = frappe.db.get_list('Account', filters={'account_number': '2121.002'})[0].name

			# Input if only there is no record of this folio_trx in the hotell billing yet
			if not frappe.db.exists('Hotel Bill Breakdown', {'parent': exist_bill, 'billing_folio_trx_id': item.name}):
				# Input the folio trx with type of sales invoice
				if item.sales_invoice_id:
					sales_invoice = frappe.get_doc('Sales Invoice', item.sales_invoice_id)
					# Input the sales invoice item first
					si_doc_item = frappe.new_doc("Hotel Bill Breakdown")
					si_doc_item.is_tax_item = 0
					si_doc_item.is_folio_trx_pairing = 1
					si_doc_item.billing_folio_trx_id = item.name
					si_doc_item.breakdown_description = item.remark
					si_doc_item.breakdown_net_total = item.amount
					si_doc_item.breakdown_tax_id = sales_invoice.taxes_and_charges  # masih null
					si_doc_item.breakdown_tax_amount = sales_invoice.total_taxes_and_charges
					si_doc_item.breakdown_grand_total = sales_invoice.grand_total
					# folio accounts are from the Customer's side, needed to flip it in Hotel Bill Breakdown
					si_doc_item.breakdown_account = item.against_account_id
					si_doc_item.breakdown_account_against = item.account_id
					doc_hotel_bill.append('bill_breakdown', si_doc_item)

					# Input the tax item
					if frappe.db.exists('Sales Taxes and Charges', {'parent': item.sales_invoice_id}):
						sales_tax_charges = frappe.get_doc('Sales Taxes and Charges', {'parent': item.sales_invoice_id})
						si_doc_tax_item = frappe.new_doc("Hotel Bill Breakdown")
						si_doc_tax_item.is_tax_item = 1
						si_doc_tax_item.billing_folio_trx_id = item.name
						si_doc_tax_item.breakdown_grand_total = sales_invoice.total_taxes_and_charges
						si_doc_tax_item.breakdown_account = sales_tax_charges.account_head
						# si_doc_tax_item.breakdown_account_against = doc_hotel_bill.customer_id
						si_doc_tax_item.breakdown_description = sales_tax_charges.description + ' of ' + item.sales_invoice_id
						doc_hotel_bill.append('bill_breakdown', si_doc_tax_item)

				# Input the folio trx with type of auto room charge
				elif item.room_rate:
					room_rate = frappe.get_doc('Room Rate', item.room_rate)
					room_stay = frappe.get_doc('Room Stay', item.room_stay_id)
					if not room_stay.discount_percentage:
						room_stay_discount = 0
					else:
						room_stay_discount = float(room_stay.discount_percentage)/100.0
					amount_multiplier = 1 - room_stay_discount
					room_rate_breakdown_list = room_rate.get('room_rate_breakdown')
					bundle_tax_amount = 0

					if is_this_weekday(item.creation):
						rate_breakdown = frappe.get_doc('Room Rate Breakdown',
														{'parent': item.room_rate, 'breakdown_name': 'Weekday Rate'})
						description = "Weekday Rate of " + item.room_rate + ' + ' + rate_breakdown.breakdown_tax
					else:
						rate_breakdown = frappe.get_doc('Room Rate Breakdown',
														{'parent': item.room_rate, 'breakdown_name': 'Weekend Rate'})
						description = "Weekend Rate of " + item.room_rate + ' + ' + rate_breakdown.breakdown_tax

					base_amount = rate_breakdown.breakdown_amount * amount_multiplier
					breakdown_tax = rate_breakdown.breakdown_tax
					room_rate_breakdown_account = rate_breakdown.breakdown_account
					room_tb_id, room_tb_amount, room_tb_total = calculate_hotel_tax_and_charges(base_amount, breakdown_tax)

					bundle_tax_amount = bundle_tax_amount + sum(room_tb_amount)
					for rrbd_item in room_rate_breakdown_list:
						if rrbd_item.breakdown_name != 'Weekend Rate' and rrbd_item.breakdown_name != 'Weekday Rate':
							_, rrbd_tb_amount, _ = calculate_hotel_tax_and_charges(
								amount_multiplier * rrbd_item.breakdown_amount * float(rrbd_item.breakdown_qty), rrbd_item.breakdown_tax)
							bundle_tax_amount = bundle_tax_amount + sum(rrbd_tb_amount)

					# input the Rate total corresponded to folio trx
					rr_bundle_item = frappe.new_doc("Hotel Bill Breakdown")
					rr_bundle_item.is_tax_item = 0
					rr_bundle_item.is_folio_trx_pairing = 1
					rr_bundle_item.is_excluded = 1 #excluded because of room bill payment in reservation.
					rr_bundle_item.breakdown_description = item.remark
					rr_bundle_item.breakdown_net_total = item.amount
					rr_bundle_item.breakdown_tax_amount = bundle_tax_amount
					rr_bundle_item.breakdown_grand_total = rr_bundle_item.breakdown_net_total + rr_bundle_item.breakdown_tax_amount
					rr_bundle_item.breakdown_account = item.against_account_id
					rr_bundle_item.breakdown_account_against = item.account_id
					doc_hotel_bill.append('bill_breakdown', rr_bundle_item)

					# Input the item room charge
					rr_doc_item = frappe.new_doc("Hotel Bill Breakdown")
					rr_doc_item.is_tax_item = 0
					rr_doc_item.billing_folio_trx_id = item.name
					rr_doc_item.breakdown_description = description
					rr_doc_item.breakdown_net_total = base_amount
					rr_doc_item.breakdown_tax_amount = sum(room_tb_amount)
					rr_doc_item.breakdown_grand_total = room_tb_total[-1]
					rr_doc_item.breakdown_tax_id = breakdown_tax
					rr_doc_item.breakdown_account = room_rate_breakdown_account # cek account dari room rate breakdown most likely pendapatan kamar
					rr_doc_item.breakdown_account_against = kas_dp_kamar
					doc_hotel_bill.append('bill_breakdown', rr_doc_item)

					# input the tax item of room charge
					for index, room_charge_tax_item_name in enumerate(room_tb_id):
						hotel_tax_breakdown = frappe.get_doc('Hotel Tax Breakdown', room_charge_tax_item_name)
						rr_doc_tax_item = frappe.new_doc("Hotel Bill Breakdown")
						rr_doc_tax_item.is_tax_item = 1
						rr_doc_tax_item.breakdown_description = hotel_tax_breakdown.breakdown_description
						rr_doc_tax_item.breakdown_grand_total = room_tb_amount[index]
						rr_doc_tax_item.breakdown_account = hotel_tax_breakdown.breakdown_account # account dari tax
						rr_doc_tax_item.breakdown_account_against = kas_dp_kamar
						doc_hotel_bill.append('bill_breakdown', rr_doc_tax_item)

					# input the other room rate charge besides room rate: e.g: breakfast, coffee break, etc
					for rrbd_item in room_rate_breakdown_list:
						if rrbd_item.breakdown_name != 'Weekend Rate' and rrbd_item.breakdown_name != 'Weekday Rate':
							rrbd_tb_id, rrbd_tb_amount, rrbd_tb_total = calculate_hotel_tax_and_charges(
								amount_multiplier * rrbd_item.breakdown_amount * float(rrbd_item.breakdown_qty), rrbd_item.breakdown_tax)

							# input the other charge
							orr_doc_item = frappe.new_doc("Hotel Bill Breakdown")
							orr_doc_item.is_tax_item = 0
							orr_doc_item.billing_folio_trx_id = item.name
							orr_doc_item.breakdown_description = str(
								rrbd_item.breakdown_qty) + " " + rrbd_item.breakdown_name + " of " + item.room_rate + ' + ' + rrbd_item.breakdown_tax
							orr_doc_item.breakdown_net_total = amount_multiplier * rrbd_item.breakdown_amount * float(rrbd_item.breakdown_qty)
							orr_doc_item.breakdown_tax_amount = sum(rrbd_tb_amount)
							orr_doc_item.breakdown_grand_total = rrbd_tb_total[-1]
							orr_doc_item.breakdown_tax_id = rrbd_item.breakdown_tax
							orr_doc_item.breakdown_account = rrbd_item.breakdown_account # cek account dari room rate breakdown
							orr_doc_item.breakdown_account_against = kas_dp_kamar
							doc_hotel_bill.append('bill_breakdown', orr_doc_item)

							# input the other charge tax item
							for index, orr_tax_item_name in enumerate(rrbd_tb_id):
								orr_hotel_tax_breakdown = frappe.get_doc('Hotel Tax Breakdown', orr_tax_item_name)
								orr_doc_tax_item = frappe.new_doc("Hotel Bill Breakdown")
								orr_doc_tax_item.is_tax_item = 1
								orr_doc_tax_item.breakdown_description = orr_hotel_tax_breakdown.breakdown_description
								orr_doc_tax_item.breakdown_grand_total = rrbd_tb_amount[index]
								orr_doc_tax_item.breakdown_account = orr_hotel_tax_breakdown.breakdown_account # cek account dari hotel tax
								orr_doc_tax_item.breakdown_account_against = kas_dp_kamar
								doc_hotel_bill.append('bill_breakdown', orr_doc_tax_item)

				# Special charge are early check-in and late check-out fee
				elif item.is_special_charge:
					sp_doc_item = frappe.new_doc("Hotel Bill Breakdown")
					sp_doc_item.is_folio_trx_pairing = 1
					sp_doc_item.billing_folio_trx_id = item.name
					sp_doc_item.breakdown_description = item.remark
					sp_doc_item.breakdown_net_total = item.amount
					sp_doc_item.breakdown_tax_amount = 0
					sp_doc_item.breakdown_grand_total = item.amount
					sp_doc_item.breakdown_account = item.against_account_id
					sp_doc_item.breakdown_account_against = item.account_id
					doc_hotel_bill.append('bill_breakdown', sp_doc_item)

				# Additional charge are charges that added by Additional Charge form in Rerservation Page
				elif item.is_additional_charge:
					ac_doc_item = frappe.new_doc("Hotel Bill Breakdown")
					ac_doc_item.is_folio_trx_pairing = 1
					ac_doc_item.billing_folio_trx_id = item.name
					ac_doc_item.breakdown_description = item.remark
					ac_doc_item.breakdown_net_total = item.amount
					ac_doc_item.breakdown_tax_amount = 0
					ac_doc_item.breakdown_grand_total = item.amount
					ac_doc_item.breakdown_account = item.against_account_id
					ac_doc_item.breakdown_account_against = item.account_id
					doc_hotel_bill.append('bill_breakdown', ac_doc_item)

			# save all hotel bill breakdown to the hotel bill
			doc_hotel_bill.save()

		# Check if any checkout early type of refund
		room_stay_list = frappe.get_all('Room Stay', filters={"reservation_id": reservation_id}, fields=["*"])
		if len(room_stay_list) > 0:
			for rs_item in room_stay_list:
				checkout_early_refund(rs_item.name)

		# Check deposit refund
		this_hotel_bill = frappe.get_doc("Hotel Bill", exist_bill)
		if this_hotel_bill.use_deposit == 1:
			if this_hotel_bill.bill_deposit_amount > this_hotel_bill.bill_grand_total:
				deposit_refund_amount = this_hotel_bill.bill_deposit_amount - this_hotel_bill.bill_grand_total
			else:
				deposit_refund_amount = 0
		else:
			deposit_refund_amount = this_hotel_bill.bill_deposit_amount

		if deposit_refund_amount > 0:
			refund_description = 'Deposit Refund of Reservation: ' + str(this_hotel_bill.reservation_id)
			kas_deposit_customer = frappe.db.get_list('Account', filters={'account_number': '1172.000'})[0].name
			kas_fo = frappe.db.get_list('Account', filters={'account_number': '1111.003'})[0].name

			exist_this_refund_item = frappe.db.exists('Hotel Bill Refund',
													  {'parent': this_hotel_bill.name,
													   'refund_description': refund_description})
			if not exist_this_refund_item:
				refund_item = frappe.new_doc('Hotel Bill Refund')
				refund_item.naming_series = 'FO-BILL-RFND-.YYYY.-'
				refund_item.refund_amount = deposit_refund_amount
				refund_item.refund_description = refund_description
				refund_item.is_refunded = 0
				refund_item.account = kas_fo
				refund_item.account_against = kas_deposit_customer

				this_hotel_bill.append('bill_refund', refund_item)
				this_hotel_bill.save()
		else:
			refund_description = 'Deposit Refund of Reservation: ' + str(this_hotel_bill.reservation_id)
			exist_this_refund_item = frappe.db.exists('Hotel Bill Refund',
													  {'parent': this_hotel_bill.name,
													   'refund_description': refund_description})
			if exist_this_refund_item:
				refund_list = this_hotel_bill.get('bill_refund')
				for item in refund_list:
					if item.name == exist_this_refund_item:
						refund_list.remove(item)
						this_hotel_bill.save()
	else:
		frappe.msgprint('Hotel Bill Cannot be found. Check if Customer Deposit already made or not.')

def get_mode_of_payment_account(mode_of_payment_id, company_name):
	return frappe.db.get_value('Mode of Payment Account', {'parent': mode_of_payment_id, 'company': company_name}, "default_account")

@frappe.whitelist()
def deposit_refund_account(type):
	if type == 'account':
		return frappe.db.get_list('Account', filters={'account_number': '1111.003'})[0].name
	elif type == 'against':
		return frappe.db.get_list('Account', filters={'account_number': '1172.000'})[0].name

@frappe.whitelist()
def make_payment_hotel_bill(hotel_bill_id, latest_outstanding_amount):
	hotel_bill = frappe.get_doc('Hotel Bill', hotel_bill_id)
	bill_breakdown_list = hotel_bill.get('bill_breakdown')
	bill_refund_list = hotel_bill.get('bill_refund')
	bill_payment_list = hotel_bill.get('bill_payments')

	if float(latest_outstanding_amount) > 0:
		frappe.msgprint("There are still outstanding amount needed to be paid")
	else:

		# 1. Room Rate Breakdown Journal Entry
		for bb_item in bill_breakdown_list:
			# 1.1 Room Rate Breakdown: is_excluded = 0, is_tax_item = 0, is_folio_trx_pairing = 0, breakdown_tax_id != null
			if bb_item.is_excluded == 0 and bb_item.is_tax_item == 0 and bb_item.is_folio_trx_pairing == 0 and bb_item.breakdown_tax_id is not None:
				bb_title = 'Hotel Bill Breakdown: ' + bb_item.breakdown_description + ' - ' + bb_item.name
				bb_remark = bb_title + '. @ ' + str(bb_item.creation)

				# JOURNAL ENTRY CREATION: BILL BREAKDOWN
				bb_doc_journal_entry = frappe.new_doc('Journal Entry')
				bb_doc_journal_entry.title = bb_title
				bb_doc_journal_entry.voucher_type = 'Journal Entry'
				bb_doc_journal_entry.naming_series = 'ACC-JV-.YYYY.-'
				bb_doc_journal_entry.posting_date = datetime.date.today()
				bb_doc_journal_entry.company = frappe.get_doc("Global Defaults").default_company
				bb_doc_journal_entry.total_amount_currency = frappe.get_doc("Global Defaults").default_currency
				bb_doc_journal_entry.remark = bb_remark
				bb_doc_journal_entry.user_remark = bb_remark

				# Journal Entry Account: Debit
				bb_doc_debit = frappe.new_doc('Journal Entry Account')
				bb_doc_debit.account = bb_item.breakdown_account_against
				bb_doc_debit.debit = bb_item.breakdown_net_total
				bb_doc_debit.debit_in_account_currency = bb_item.breakdown_net_total
				bb_doc_debit.party_type = 'Customer'
				bb_doc_debit.party = hotel_bill.customer_id
				bb_doc_debit.user_remark = bb_remark

				# Journal Entry Account: Credit
				bb_doc_credit = frappe.new_doc('Journal Entry Account')
				bb_doc_credit.account = bb_item.breakdown_account
				bb_doc_credit.credit = bb_item.breakdown_net_total
				bb_doc_credit.credit_in_account_currency = bb_item.breakdown_net_total
				bb_doc_credit.party_type = 'Customer'
				bb_doc_credit.party = hotel_bill.customer_id
				bb_doc_credit.user_remark = bb_remark

				# Append debit and credit to Journal Account
				bb_doc_journal_entry.append('accounts', bb_doc_debit)
				bb_doc_journal_entry.append('accounts', bb_doc_credit)

				# Save and Submit Journal Entry
				bb_doc_journal_entry.save()
				bb_doc_journal_entry.submit()

			# 1.2 Room Rate Breakdown Tax: is_excluded = 0, is_tax_item = 1
			elif bb_item.is_excluded == 0 and bb_item.is_tax_item == 1:
				bb_tax_title = 'Hotel Bill Breakdown Tax: ' + bb_item.breakdown_description + ' - ' + bb_item.name
				bb_tax_remark = bb_tax_title + '. @ ' + str(bb_item.creation)

				# JOURNAL ENTRY CREATION: BILL BREAKDOWN TAX
				bb_tax_doc_journal_entry = frappe.new_doc('Journal Entry')
				bb_tax_doc_journal_entry.title = bb_tax_title
				bb_tax_doc_journal_entry.voucher_type = 'Journal Entry'
				bb_tax_doc_journal_entry.naming_series = 'ACC-JV-.YYYY.-'
				bb_tax_doc_journal_entry.posting_date = datetime.date.today()
				bb_tax_doc_journal_entry.company = frappe.get_doc("Global Defaults").default_company
				bb_tax_doc_journal_entry.total_amount_currency = frappe.get_doc("Global Defaults").default_currency
				bb_tax_doc_journal_entry.remark = bb_tax_remark
				bb_tax_doc_journal_entry.user_remark = bb_tax_remark

				# Journal Entry Account: Debit
				bb_tax_doc_debit = frappe.new_doc('Journal Entry Account')
				bb_tax_doc_debit.account = bb_item.breakdown_account_against
				bb_tax_doc_debit.debit = bb_item.breakdown_grand_total
				bb_tax_doc_debit.debit_in_account_currency = bb_item.breakdown_grand_total
				bb_tax_doc_debit.party_type = 'Customer'
				bb_tax_doc_debit.party = hotel_bill.customer_id
				bb_tax_doc_debit.user_remark = bb_tax_remark

				# Journal Entry Account: Credit
				bb_tax_doc_credit = frappe.new_doc('Journal Entry Account')
				bb_tax_doc_credit.account = bb_item.breakdown_account
				bb_tax_doc_credit.credit = bb_item.breakdown_grand_total
				bb_tax_doc_credit.credit_in_account_currency = bb_item.breakdown_grand_total
				bb_tax_doc_credit.party_type = 'Customer'
				bb_tax_doc_credit.party = hotel_bill.customer_id
				bb_tax_doc_credit.user_remark = bb_tax_remark

				# Append debit and credit to Journal Account
				bb_tax_doc_journal_entry.append('accounts', bb_tax_doc_debit)
				bb_tax_doc_journal_entry.append('accounts', bb_tax_doc_credit)

				# Save and Submit Journal Entry
				bb_tax_doc_journal_entry.save()
				bb_tax_doc_journal_entry.submit()
		# 2. Hotel Bill Refund Journal Entry
		for br_item in bill_refund_list:
			br_title = 'Hotel Bill Refund: ' + br_item.refund_description + ' - ' + br_item.name
			br_remark = br_title + '. @ ' + str(br_item.creation)

			# JOURNAL ENTRY CREATION: HOTEL BILL REFUND
			br_doc_journal_entry = frappe.new_doc('Journal Entry')
			br_doc_journal_entry.title = br_title
			br_doc_journal_entry.voucher_type = 'Journal Entry'
			br_doc_journal_entry.naming_series = 'ACC-JV-.YYYY.-'
			br_doc_journal_entry.posting_date = datetime.date.today()
			br_doc_journal_entry.company = frappe.get_doc("Global Defaults").default_company
			br_doc_journal_entry.total_amount_currency = frappe.get_doc("Global Defaults").default_currency
			br_doc_journal_entry.remark = br_remark
			br_doc_journal_entry.user_remark = br_remark

			# Journal Entry Account: Debit
			br_doc_debit = frappe.new_doc('Journal Entry Account')
			br_doc_debit.account = br_item.account_against
			br_doc_debit.debit = br_item.refund_amount
			br_doc_debit.debit_in_account_currency = br_item.refund_amount
			br_doc_debit.party_type = 'Customer'
			br_doc_debit.party = hotel_bill.customer_id
			br_doc_debit.user_remark = br_remark

			# Journal Entry Account: Credit
			br_doc_credit = frappe.new_doc('Journal Entry Account')
			br_doc_credit.account = br_item.account
			br_doc_credit.credit = br_item.refund_amount
			br_doc_credit.credit_in_account_currency = br_item.refund_amount
			br_doc_credit.party_type = 'Customer'
			br_doc_credit.party = hotel_bill.customer_id
			br_doc_credit.user_remark = br_remark

			# Append debit and credit to Journal Account
			br_doc_journal_entry.append('accounts', br_doc_debit)
			br_doc_journal_entry.append('accounts', br_doc_credit)

			# Save and Submit Journal Entry
			br_doc_journal_entry.save()
			br_doc_journal_entry.submit()

			# Flag this br_item as refunded
			frappe.db.set_value('Hotel Bill Refund', br_item.name, 'is_refunded', 1)
		# 3. Hotel Bill Payment Journal Entry
		for bp_item in bill_payment_list:
			bp_credit_account_name = frappe.db.get_list('Account', filters={'account_number': '4210.001'})[0].name
			bp_debit_account_name = get_mode_of_payment_account(bp_item.mode_of_payment,
															 frappe.get_doc("Global Defaults").default_company)
			bp_title = 'Hotel Bill Payment (' + str(bp_item.mode_of_payment) + '): ' + str(bp_item.parent) + ' - ' + bp_item.name
			bp_remark = bp_title + ' - @' + str(bp_item.creation)

			# JOURNAL ENTRY CREATION: HOTEL BILL PAYMENT
			bp_doc_journal_entry = frappe.new_doc('Journal Entry')
			bp_doc_journal_entry.title = bp_title
			bp_doc_journal_entry.voucher_type = 'Journal Entry'
			bp_doc_journal_entry.naming_series = 'ACC-JV-.YYYY.-'
			bp_doc_journal_entry.posting_date = datetime.date.today()
			bp_doc_journal_entry.company = frappe.get_doc("Global Defaults").default_company
			bp_doc_journal_entry.total_amount_currency = frappe.get_doc("Global Defaults").default_currency
			bp_doc_journal_entry.remark = bp_remark
			bp_doc_journal_entry.user_remark = bp_remark

			# Journal Entry Account: Debit
			bp_doc_debit = frappe.new_doc('Journal Entry Account')
			bp_doc_debit.account = bp_debit_account_name
			bp_doc_debit.debit = bp_item.payment_amount
			bp_doc_debit.debit_in_account_currency = bp_item.payment_amount
			bp_doc_debit.party_type = 'Customer'
			bp_doc_debit.party = hotel_bill.customer_id
			bp_doc_debit.user_remark = bp_remark

			# Journal Entry Account: Credit
			bp_doc_credit = frappe.new_doc('Journal Entry Account')
			bp_doc_credit.account = bp_credit_account_name
			bp_doc_credit.credit = bp_item.payment_amount
			bp_doc_credit.credit_in_account_currency = bp_item.payment_amount
			bp_doc_credit.party_type = 'Customer'
			bp_doc_credit.party = hotel_bill.customer_id
			bp_doc_credit.user_remark = bp_remark

			# Append debit and credit to Journal Account
			bp_doc_journal_entry.append('accounts', bp_doc_debit)
			bp_doc_journal_entry.append('accounts', bp_doc_credit)

			# Save and Submit Journal Entry
			bp_doc_journal_entry.save()
			bp_doc_journal_entry.submit()

		# 4. Deposit as Payment Journal Entry, if Use Deposit is checked
		if hotel_bill.use_deposit == 1:
			depo_credit_account_name = frappe.db.get_list('Account', filters={'account_number': '1133.002'})[0].name
			depo_debit_account_name = frappe.db.get_list('Account', filters={'account_number': '1172.000'})[0].name
			depo_title = 'Hotel Bill Payment (Deposit): ' + hotel_bill.name
			depo_remark = depo_title + ' - @' + str(hotel_bill.creation)
			refund_description = 'Deposit Refund of Reservation: ' + str(hotel_bill.reservation_id)
			exist_this_refund_item = frappe.db.exists('Hotel Bill Refund',
													  {'parent': hotel_bill.name,
													   'refund_description': refund_description})
			if exist_this_refund_item:
				deposit_refund_amount = frappe.db.get_value('Hotel Bill Refund', {'name': exist_this_refund_item}, ['refund_amount'])
				deposit_used_amount = hotel_bill.bill_deposit_amount - deposit_refund_amount
			else:
				deposit_used_amount = hotel_bill.bill_deposit_amount

			# JOURNAL ENTRY CREATION: DEPOSIT AS PAYMENT
			depo_doc_journal_entry = frappe.new_doc('Journal Entry')
			depo_doc_journal_entry.title = depo_title
			depo_doc_journal_entry.voucher_type = 'Journal Entry'
			depo_doc_journal_entry.naming_series = 'ACC-JV-.YYYY.-'
			depo_doc_journal_entry.posting_date = datetime.date.today()
			depo_doc_journal_entry.company = frappe.get_doc("Global Defaults").default_company
			depo_doc_journal_entry.total_amount_currency = frappe.get_doc("Global Defaults").default_currency
			depo_doc_journal_entry.remark = depo_remark
			depo_doc_journal_entry.user_remark = depo_remark

			# Journal Entry Account: Debit
			depo_doc_debit = frappe.new_doc('Journal Entry Account')
			depo_doc_debit.account = depo_debit_account_name
			depo_doc_debit.debit = deposit_used_amount
			depo_doc_debit.debit_in_account_currency = deposit_used_amount
			depo_doc_debit.party_type = 'Customer'
			depo_doc_debit.party = hotel_bill.customer_id
			depo_doc_debit.user_remark = depo_remark

			# Journal Entry Account: Credit
			depo_doc_credit = frappe.new_doc('Journal Entry Account')
			depo_doc_credit.account = depo_credit_account_name
			depo_doc_credit.credit = deposit_used_amount
			depo_doc_credit.credit_in_account_currency = deposit_used_amount
			depo_doc_credit.party_type = 'Customer'
			depo_doc_credit.party = hotel_bill.customer_id
			depo_doc_credit.user_remark = depo_remark

			# Append debit and credit to Journal Account
			depo_doc_journal_entry.append('accounts', depo_doc_debit)
			depo_doc_journal_entry.append('accounts', depo_doc_credit)

			# Save and Submit Journal Entry
			depo_doc_journal_entry.save()
			depo_doc_journal_entry.submit()
		# 5. Hotel Bill Change Journal Entry, if Cash Used in Payments, and there is excess in payment needed to be returned
		if float(hotel_bill.bill_change_amount) > 0:
			kas_kecil = frappe.db.get_list('Account', filters={'account_number': '1111.003'})[0].name
			piutang_lain2 = frappe.db.get_list('Account', filters={'account_number': '1133.002'})[0].name
			change_title = 'Hotel Bill Change: ' + hotel_bill.name
			change_remark = change_title + ' - @' + str(hotel_bill.creation)

			# JOURNAL ENTRY CREATION: HOTEL BILL CHANGE
			change_doc_journal_entry = frappe.new_doc('Journal Entry')
			change_doc_journal_entry.title = change_title
			change_doc_journal_entry.voucher_type = 'Journal Entry'
			change_doc_journal_entry.naming_series = 'ACC-JV-.YYYY.-'
			change_doc_journal_entry.posting_date = datetime.date.today()
			change_doc_journal_entry.company = frappe.get_doc("Global Defaults").default_company
			change_doc_journal_entry.remark = change_remark
			change_doc_journal_entry.user_remark = change_remark

			change_doc_debit = frappe.new_doc('Journal Entry Account')
			change_doc_debit.account = piutang_lain2
			change_doc_debit.debit = hotel_bill.bill_rounded_change_amount
			change_doc_debit.debit_in_account_currency = hotel_bill.bill_rounded_change_amount
			change_doc_debit.party_type = 'Customer'
			change_doc_debit.party = hotel_bill.customer_id
			change_doc_debit.user_remark = change_remark

			change_doc_credit = frappe.new_doc('Journal Entry Account')
			change_doc_credit.account = kas_kecil
			change_doc_credit.credit = hotel_bill.bill_rounded_change_amount
			change_doc_credit.credit_in_account_currency = hotel_bill.bill_rounded_change_amount
			change_doc_credit.party_type = 'Customer'
			change_doc_credit.party = hotel_bill.customer_id
			change_doc_credit.user_remark = change_remark

			change_doc_journal_entry.append('accounts', change_doc_debit)
			change_doc_journal_entry.append('accounts', change_doc_credit)

			change_doc_journal_entry.save()
			change_doc_journal_entry.submit()
		# 6. Set Hotel Bill is_paid = 1
		frappe.db.set_value('Hotel Bill', hotel_bill_id, 'is_paid', 1)
		# 7. Set Reservation related is_frozen status to 1
		frappe.db.set_value('Reservation', hotel_bill.reservation_id, 'is_frozen', 1)

		return 1
