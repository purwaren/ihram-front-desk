# -*- coding: utf-8 -*-
# Copyright (c) 2019, PMM and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from datetime import datetime
import frappe
from frappe.model.document import Document
from front_desk.front_desk.doctype.night_audit_transaction.night_audit_transaction import make_journal_entry


class NightAudit(Document):
	pass


def get_mode_of_payment_account(mode_of_payment_id, company_name):
	return frappe.db.get_value('Mode of Payment Account', {'parent': mode_of_payment_id, 'company': company_name},
							   "default_account")


@frappe.whitelist()
def fetch_transactions(fetch_all_check):
	list_of_transactions = []
	nat_list_transaction_id = []
	today = datetime.today()
	midnight = datetime.combine(today, datetime.min.time())
	# # 1. get all AR City Ledger Invoice - Change
	# acli_list = frappe.get_all('AR City Ledger Invoice',
	# 						   filters={'creation': ['>=', midnight], 'change_amount': ['>', 0],
	# 									'change_journal_entry_id': ['=', '']},
	# 						   fields=['name', 'creation', 'rounded_change_amount', 'customer_id'])
	# # 2. get all AR City Ledger Invoice Payment
	# aclip_list = frappe.get_all('AR City Ledger Invoice Payments',
	# 							filters={'creation': ['>=', midnight], 'journal_entry_id': ['=', '']},
	# 							fields=['name', 'parent', 'creation', 'mode_of_payment', 'payment_amount'])
	# # 3. get all Hotel Bill Breakdown - Item and Tax
	# hbb_list = frappe.get_all('Hotel Bill Breakdown',
	# 							filters={'creation': ['>=', midnight], 'journal_entry_id': ['=', '']},
	# 							fields=['name', 'creation', 'parent', 'breakdown_net_total', 'breakdown_grand_total',
	# 									'breakdown_description', 'breakdown_account', 'breakdown_account_against'])
	# # 4. get all Hotel Bill Refund
	# hbr_list = frappe.get_all('Hotel Bill Refund',
	# 						  filters={'creation': ['>=', midnight], 'journal_entry_id': ['=', '']},
	# 						  fields=['name', 'creation', 'parent', 'refund_amount', 'refund_description', 'account',
	# 								  'account_against'])
	# # 5. get all Hotel Bill Payments
	# hbp_list = frappe.get_all('Hotel Bill Payments',
	# 						  filters={'creation': ['>=', midnight], 'journal_entry_id': ['=', '']},
	# 						  fields=['name', 'creation', 'parent', 'payment_amount', 'mode_of_payment'])
	# # 6. get all Hotel Bill - Use Deposit
	# hb_depo_list = frappe.get_all('Hotel Bill',
	# 							  filters={'creation': ['>=', midnight], 'is_paid': ['=', 1], 'use_deposit': ['=', 1],
	# 									   'use_deposit_journal_entry_id': ['=', '']},
	# 							  fields=['name', 'creation', 'reservation_id', 'bill_deposit_amount', 'customer_id'])
	# # 7. get all Hotel BIll - Cash Change
	# hb_change_list = frappe.get_all('Hotel Bill',
	# 								filters={'creation': ['>=', midnight], 'is_paid': ['=', 1],
	# 										 'bill_change_amount': ['>', 0], 'change_journal_entry_id': ['=', '']},
	# 								fields=['name', 'creation', 'reservation_id', 'bill_rounded_change_amount', 'customer_id'])
	# 8. get all Folio Transaction
	if fetch_all_check == 0:
		ft_list = frappe.get_all('Folio Transaction', filters={'journal_entry_id': ['=', '']})
	else:
		ft_list = frappe.get_all('Folio Transaction',
								 filters={'creation': ['>=', midnight], 'journal_entry_id': ['=', '']})
	# 9. get all Night Audit Transaction
	if fetch_all_check == 0:
		nat_list = frappe.get_all('Night Audit Transaction', fields=['transaction_id'])
	else:
		nat_list = frappe.get_all('Night Audit Transaction', filters={'creation': ['>=', midnight]},
								  fields=['transaction_id'])
	for nat_item in nat_list:
		nat_list_transaction_id.append(nat_item.transaction_id)

	# FOLIO TRANSACTIONS - START
	if len(ft_list) > 0:
		for ft_item in ft_list:
			if ft_item.name not in nat_list_transaction_id:
				doc_ft = frappe.get_doc('Folio Transaction', ft_item.name)
				customer_name = frappe.get_doc('Customer', frappe.get_doc('Reservation', frappe.db.get_value('Folio', {
								'name': doc_ft.parent}, "reservation_id")).customer_id).name
				if ' -  Additional Charge ' in doc_ft.remark:
					doc_nat = frappe.new_doc('Night Audit Transaction')
					doc_nat.transaction_type = 'Folio - Additional Charge'
					doc_nat.transaction_id = ft_item.name
					doc_nat.reservation_id = frappe.db.get_value('Folio', {'name': doc_ft.parent}, "reservation_id")
					doc_nat.folio_id = doc_ft.parent
					doc_nat.amount = doc_ft.amount
					doc_nat.title = doc_ft.remark
					doc_nat.remark = doc_ft.remark
					doc_nat.debit_account = doc_ft.account_id
					doc_nat.credit_account = doc_ft.against_account_id
					doc_nat.customer_id = customer_name
					list_of_transactions.append(doc_nat)
				elif 'Early Check In Room ' in doc_ft.remark:
					doc_nat = frappe.new_doc('Night Audit Transaction')
					doc_nat.transaction_type = 'Folio - Room Stay Early Checkin'
					doc_nat.transaction_id = ft_item.name
					doc_nat.reservation_id = frappe.db.get_value('Folio', {'name': doc_ft.parent}, "reservation_id")
					doc_nat.folio_id = doc_ft.parent
					doc_nat.amount = doc_ft.amount
					doc_nat.title = "JE " + doc_ft.name
					doc_nat.remark = doc_ft.name + "-" + doc_ft.remark
					doc_nat.debit_account = doc_ft.account_id
					doc_nat.credit_account = doc_ft.against_account_id
					doc_nat.customer_id = customer_name
					list_of_transactions.append(doc_nat)
				elif 'Late Check Out Room ' in doc_ft.remark:
					doc_nat = frappe.new_doc('Night Audit Transaction')
					doc_nat.transaction_type = 'Folio - Room Stay Late Checkout'
					doc_nat.transaction_id = ft_item.name
					doc_nat.reservation_id = frappe.db.get_value('Folio', {'name': doc_ft.parent}, "reservation_id")
					doc_nat.folio_id = doc_ft.parent
					doc_nat.amount = doc_ft.amount
					doc_nat.title = "JE " + doc_ft.name
					doc_nat.remark = doc_ft.name + "-" + doc_ft.remark
					doc_nat.debit_account = doc_ft.account_id
					doc_nat.credit_account = doc_ft.against_account_id
					doc_nat.customer_id = customer_name
					list_of_transactions.append(doc_nat)
				elif 'Deposit ' in doc_ft.remark:
					doc_nat = frappe.new_doc('Night Audit Transaction')
					doc_nat.transaction_type = 'Folio - Reservation Deposit'
					doc_nat.transaction_id = ft_item.name
					doc_nat.reservation_id = frappe.db.get_value('Folio', {'name': doc_ft.parent}, "reservation_id")
					doc_nat.folio_id = doc_ft.parent
					doc_nat.amount = doc_ft.amount
					doc_nat.title = "JE " + doc_ft.name
					doc_nat.remark = doc_ft.remark
					doc_nat.debit_account = doc_ft.account_id
					doc_nat.credit_account = doc_ft.against_account_id
					doc_nat.customer_id = customer_name
					list_of_transactions.append(doc_nat)
				elif 'Room Bill Payment: ' in doc_ft.remark:
					doc_nat = frappe.new_doc('Night Audit Transaction')
					doc_nat.transaction_type = 'Folio - Room Bill Payment'
					doc_nat.transaction_id = ft_item.name
					doc_nat.reservation_id = frappe.db.get_value('Folio', {'name': doc_ft.parent}, "reservation_id")
					doc_nat.folio_id = doc_ft.parent
					doc_nat.amount = doc_ft.amount
					doc_nat.title = "JE " + doc_ft.name
					doc_nat.remark = doc_ft.remark
					doc_nat.debit_account = doc_ft.account_id
					doc_nat.credit_account = doc_ft.against_account_id
					doc_nat.customer_id = customer_name
					list_of_transactions.append(doc_nat)
				elif 'Change from ' in doc_ft.remark:
					doc_nat = frappe.new_doc('Night Audit Transaction')
					doc_nat.transaction_type = 'Folio - Room Bill Payment Change'
					doc_nat.transaction_id = ft_item.name
					doc_nat.reservation_id = frappe.db.get_value('Folio', {'name': doc_ft.parent}, "reservation_id")
					doc_nat.folio_id = doc_ft.parent
					doc_nat.amount = doc_ft.amount
					doc_nat.title = "JE " + doc_ft.name
					doc_nat.remark = doc_ft.remark
					doc_nat.debit_account = doc_ft.account_id
					doc_nat.credit_account = doc_ft.against_account_id
					doc_nat.customer_id = customer_name
					list_of_transactions.append(doc_nat)
				elif 'Cancellation Fee - Reservation: ' in doc_ft.remark:
					doc_nat = frappe.new_doc('Night Audit Transaction')
					doc_nat.transaction_type = 'Folio - Reservation Cancellation Fee'
					doc_nat.transaction_id = ft_item.name
					doc_nat.reservation_id = frappe.db.get_value('Folio', {'name': doc_ft.parent}, "reservation_id")
					doc_nat.folio_id = doc_ft.parent
					doc_nat.amount = doc_ft.amount
					doc_nat.title = doc_ft.name + ' ' + doc_ft.remark
					doc_nat.remark = doc_ft.remark
					doc_nat.debit_account = doc_ft.account_id
					doc_nat.credit_account = doc_ft.against_account_id
					doc_nat.customer_id = customer_name
					list_of_transactions.append(doc_nat)
	# FOLIO TRANSACTIONS - END

	# # HOTEL BILL - START
	# if len(hbb_list) > 0:
	# 	for hbb_item in hbb_list:
	# 		doc_hbb = frappe.get_doc('Hotel Bill Breakdown', hbb_item.name)
	# 		if doc_hbb.is_excluded == 0 and doc_hbb.is_tax_item == 0 and doc_hbb.is_folio_trx_pairing == 0 and doc_hbb.breakdown_tax_id is not None:
	# 			doc_nat = frappe.new_doc('Night Audit Transaction')
	# 			doc_nat.transaction_type = 'Hotel Bill Breakdown - Item'
	# 			doc_nat.transaction_id = hbb_item.name
	# 			doc_nat.reservation_id = frappe.db.get_value('Hotel Bill', {'name': hbb_item.parent}, "reservation_id")
	# 			doc_nat.amount = hbb_item.breakdown_net_total
	# 			doc_nat.title = 'Hotel Bill Breakdown: ' + hbb_item.breakdown_description + ' - ' + hbb_item.name
	# 			doc_nat.remark = doc_nat.title + '. @ ' + str(hbb_item.creation)
	# 			doc_nat.debit_account = hbb_item.breakdown_account_against
	# 			doc_nat.credit_account = hbb_item.breakdown_account
	# 			doc_nat.customer_id = frappe.db.get_value('Hotel Bill', {'name': hbb_item.parent}, "customer_id")
	# 			list_of_transactions.append(doc_nat)
	# 		elif doc_hbb.is_excluded == 0 and doc_hbb.is_tax_item == 1:
	# 			doc_nat = frappe.new_doc('Night Audit Transaction')
	# 			doc_nat.transaction_type = 'Hotel Bill Breakdown - Tax'
	# 			doc_nat.transaction_id = hbb_item.name
	# 			doc_nat.reservation_id = frappe.db.get_value('Hotel Bill', {'name': hbb_item.parent}, "reservation_id")
	# 			doc_nat.amount = hbb_item.breakdown_grand_total
	# 			doc_nat.title = 'Hotel Bill Breakdown Tax: ' + hbb_item.breakdown_description + ' - ' + hbb_item.name
	# 			doc_nat.remark = doc_nat.title + '. @ ' + str(hbb_item.creation)
	# 			doc_nat.debit_account = hbb_item.breakdown_account_against
	# 			doc_nat.credit_account = hbb_item.breakdown_account
	# 			doc_nat.customer_id = frappe.db.get_value('Hotel Bill', {'name': hbb_item.parent}, "customer_id")
	# 			list_of_transactions.append(doc_nat)
	#
	# if len(hbr_list) > 0:
	# 	for hbr_item in hbr_list:
	# 		doc_nat = frappe.new_doc('Night Audit Transaction')
	# 		doc_nat.transaction_type = 'Hotel Bill Refund'
	# 		doc_nat.transaction_id = hbr_item.name
	# 		doc_nat.reservation_id = frappe.db.get_value('Hotel Bill', {'name': hbr_item.parent}, "reservation_id")
	# 		doc_nat.amount = hbr_item.refund_amount
	# 		doc_nat.title = 'Hotel Bill Refund: ' + hbr_item.refund_description + ' - ' + hbr_item.name
	# 		doc_nat.remark = doc_nat.title + '. @ ' + str(hbr_item.creation)
	# 		doc_nat.debit_account = hbr_item.account_against
	# 		doc_nat.credit_account = hbr_item.account
	# 		doc_nat.customer_id = frappe.db.get_value('Hotel Bill', {'name': hbb_item.parent}, "customer_id")
	# 		list_of_transactions.append(doc_nat)
	#
	# if len(hbp_list) > 0:
	# 	for hbp_item in hbp_list:
	# 		doc_nat = frappe.new_doc('Night Audit Transaction')
	# 		doc_nat.transaction_type = 'Hotel Bill Payments'
	# 		doc_nat.transaction_id = hbp_item.name
	# 		doc_nat.reservation_id = frappe.db.get_value('Hotel Bill', {'name': hbp_item.parent}, "reservation_id")
	# 		doc_nat.amount = hbp_item.payment_amount
	# 		doc_nat.title = 'Hotel Bill Payment (' + str(hbp_item.mode_of_payment) + '): ' + str(
	# 			hbp_item.parent) + ' - ' + hbp_item.name
	# 		doc_nat.remark = doc_nat.title + ' - @' + str(hbp_item.creation)
	# 		doc_nat.debit_account = get_mode_of_payment_account(hbp_item.mode_of_payment,
	# 														 frappe.get_doc("Global Defaults").default_company)
	# 		doc_nat.credit_account = frappe.db.get_list('Account', filters={'account_number': '4320.001'})[0].name
	# 		doc_nat.customer_id = frappe.db.get_value('Hotel Bill', {'name': hbp_item.parent}, "customer_id")
	# 		list_of_transactions.append(doc_nat)
	#
	# if len(hb_depo_list) > 0:
	# 	for hb_depo_item in hb_depo_list:
	# 		doc_nat = frappe.new_doc('Night Audit Transaction')
	# 		doc_nat.transaction_type = 'Hotel Bill - Use Deposit'
	# 		doc_nat.transaction_id = hb_depo_item.name
	# 		doc_nat.reservation_id = hb_depo_item.reservation_id
	# 		doc_nat.amount = hb_depo_item.bill_deposit_amount
	# 		doc_nat.title = 'Hotel Bill Payment (Deposit): ' + hb_depo_item.name
	# 		doc_nat.remark = doc_nat.title + ' - @' + str(hb_depo_item.creation)
	# 		doc_nat.debit_account = frappe.db.get_list('Account', filters={'account_number': '1172.000'})[0].name
	# 		doc_nat.credit_account = frappe.db.get_list('Account', filters={'account_number': '1132.001'})[0].name
	# 		doc_nat.customer_id = hb_depo_item.customer_id
	# 		list_of_transactions.append(doc_nat)
	#
	# if len(hb_change_list) > 0:
	# 	for hb_change_item in hb_change_list:
	# 		doc_nat = frappe.new_doc('Night Audit Transaction')
	# 		doc_nat.transaction_type = 'Hotel Bill - Change'
	# 		doc_nat.transaction_id = hb_change_item.name
	# 		doc_nat.reservation_id = hb_change_item.reservation_id
	# 		doc_nat.amount = hb_change_item.bill_rounded_change_amount
	# 		doc_nat.title = 'Hotel Bill Change: ' + hb_change_item.name
	# 		doc_nat.remark = doc_nat.title + ' - @' + str(hb_change_item.creation)
	# 		doc_nat.debit_account = frappe.db.get_list('Account', filters={'account_number': '1132.001'})[0].name
	# 		doc_nat.credit_account = frappe.db.get_list('Account', filters={'account_number': '1111.003'})[0].name
	# 		doc_nat.customer_id = hb_change_item.customer_id
	# 		list_of_transactions.append(doc_nat)
	# # HOTEL BILL - END
	#
	# # AR CITY LEDGER - START
	# if len(acli_list) > 0:
	# 	for acli_item in acli_list:
	# 		doc_nat = frappe.new_doc('Night Audit Transaction')
	# 		doc_nat.transaction_type = 'AR City Ledger Invoice - Change'
	# 		doc_nat.transaction_id = acli_item.name
	# 		doc_nat.amount = acli_item.rounded_change_amount
	# 		doc_nat.title = 'AR City Ledger Change: ' + acli_item.name
	# 		doc_nat.remark = doc_nat.title + ' -@' + str(acli_item.creation)
	# 		doc_nat.debit_account = frappe.db.get_list('Account', filters={'account_number': '1132.002'})[0].name
	# 		doc_nat.credit_account = frappe.db.get_list('Account', filters={'account_number': '1111.003'})[0].name
	# 		doc_nat.customer_id = acli_item.customer_id
	# 		list_of_transactions.append(doc_nat)
	#
	# if len(aclip_list) > 0:
	# 	for aclip_item in aclip_list:
	# 		doc_nat = frappe.new_doc('Night Audit Transaction')
	# 		doc_nat.transaction_type = 'AR City Ledger Invoice Payments'
	# 		doc_nat.transaction_id = aclip_item.name
	# 		doc_nat.amount = aclip_item.payment_amount
	# 		doc_nat.title = 'AR City Ledger Payment (' + str(aclip_item.mode_of_payment) + '): ' + aclip_item.name
	# 		doc_nat.remark = doc_nat.title + ' -@' + str(aclip_item.creation)
	# 		doc_nat.debit_account = get_mode_of_payment_account(aclip_item.mode_of_payment,
	# 															frappe.get_doc("Global Defaults").default_company)
	# 		doc_nat.credit_account = frappe.db.get_list('Account', filters={'account_number': '1132.002'})[0].name
	# 		doc_nat.customer_id = frappe.get_doc('AR City Ledger Invoice', aclip_item.parent).customer_id
	# 		list_of_transactions.append(doc_nat)
	# # AR CITY LEDGER - END

	return list_of_transactions

@frappe.whitelist()
def get_total(na_id):
	total_amount = [0, 0, 0]
	doc = frappe.get_doc('Night Audit', na_id)
	nat_list = doc.get('night_audit_transaction')
	for nat_item in nat_list:
		total_amount[0] += nat_item.amount
		if nat_item.journal_entry_id is None:
			total_amount[1] += nat_item.amount
		elif nat_item.journal_entry_id is not None:
			total_amount[2] += nat_item.amount

	return total_amount

@frappe.whitelist()
def post_all_to_journal(na_id):
	doc = frappe.get_doc('Night Audit', na_id)
	nat_list = doc.get('night_audit_transaction')
	tobe_posted = []
	for nat_item in nat_list:
		if nat_item.journal_entry_id is None:
			tobe_posted.append(nat_item.name)

	if len(tobe_posted) > 0:
		for item in tobe_posted:
			make_journal_entry(item)
		frappe.msgprint(str(len(tobe_posted)) + " transaction(s) posted to Journal")
	else:
		frappe.msgprint("All Transactions already Posted to Journal")

def populate_night_audit_id(doc, method):
	nat_list = doc.get('night_audit_transaction')
	for nat_item in nat_list:
		nat_item.night_audit_id = doc.name
