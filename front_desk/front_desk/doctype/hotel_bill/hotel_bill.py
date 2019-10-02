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
		if bb_item.is_folio_trx_pairing == 1:
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


def create_hotel_bill(reservation_id):
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

	if not exist_bill:
		new_doc_hotel_bill = frappe.new_doc('Hotel Bill')
		new_doc_hotel_bill.naming_series = 'FO-BILL-.YYYY.-'
		new_doc_hotel_bill.reservation_id = reservation_id
		new_doc_hotel_bill.customer_id = frappe.get_doc('Reservation', reservation_id).customer_id
		new_doc_hotel_bill.bill_deposit_amount = get_deposit_amount(reservation_id)
		new_doc_hotel_bill.save()
		exist_bill = new_doc_hotel_bill.name

	for item in folio_trx_list:
		doc_hotel_bill = frappe.get_doc("Hotel Bill", {'name': exist_bill})
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
				sales_tax_charges = frappe.get_doc('Sales Taxes and Charges', {'parent': item.sales_invoice_id})
				if sales_tax_charges:
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
				# TODO: account and against account
				rr_doc_item.breakdown_account = ''
				rr_doc_item.breakdown_account_against = ''
				doc_hotel_bill.append('bill_breakdown', rr_doc_item)

				# input the tax item of room charge
				for index, room_charge_tax_item_name in enumerate(room_tb_id):
					hotel_tax_breakdown = frappe.get_doc('Hotel Tax Breakdown', room_charge_tax_item_name)
					rr_doc_tax_item = frappe.new_doc("Hotel Bill Breakdown")
					rr_doc_tax_item.is_tax_item = 1
					rr_doc_tax_item.breakdown_description = hotel_tax_breakdown.breakdown_description
					rr_doc_tax_item.breakdown_grand_total = room_tb_amount[index]
					# TODO: account and against account
					rr_doc_item.breakdown_account = ''
					rr_doc_item.breakdown_account_against = ''
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
						# TODO: account and against account
						rr_doc_item.breakdown_account = ''
						rr_doc_item.breakdown_account_against = ''
						doc_hotel_bill.append('bill_breakdown', orr_doc_item)

						# input the other charge tax item
						for index, orr_tax_item_name in enumerate(rrbd_tb_id):
							orr_hotel_tax_breakdown = frappe.get_doc('Hotel Tax Breakdown', orr_tax_item_name)
							orr_doc_tax_item = frappe.new_doc("Hotel Bill Breakdown")
							orr_doc_tax_item.is_tax_item = 1
							orr_doc_tax_item.breakdown_description = orr_hotel_tax_breakdown.breakdown_description
							orr_doc_tax_item.breakdown_grand_total = rrbd_tb_amount[index]
							# TODO: account and against account
							rr_doc_item.breakdown_account = ''
							rr_doc_item.breakdown_account_against = ''
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
				sp_doc_item.breakdown_acocunt = item.against_account_id
				sp_doc_item.breakdown_acocunt_against = item.account_id
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
				ac_doc_item.breakdown_acocunt = item.against_account_id
				ac_doc_item.breakdown_acocunt_against = item.account_id
				doc_hotel_bill.append('bill_breakdown', ac_doc_item)

		# save all hotel bill breakdown to the hotel bill
		doc_hotel_bill.save()
