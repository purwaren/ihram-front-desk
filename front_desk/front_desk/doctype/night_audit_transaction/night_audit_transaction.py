# -*- coding: utf-8 -*-
# Copyright (c) 2019, PMM and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import datetime
from frappe.model.document import Document

class NightAuditTransaction(Document):
	pass

@frappe.whitelist()
def make_journal_entry(nat_id):
	doc_nat = frappe.get_doc('Night Audit Transaction', nat_id)
	doc_na = frappe.get_doc('Night Audit', doc_nat.parent)
	doc_je = frappe.new_doc('Journal Entry')
	doc_je.title = doc_nat.title
	doc_je.voucher_type = 'Journal Entry'
	doc_je.naming_series = 'ACC-JV-.YYYY.-'
	doc_je.posting_date = datetime.date.today()
	doc_je.company = frappe.get_doc('Global Defaults').default_company
	doc_je.total_amount_currency = frappe.get_doc('Global Defaults').default_currency
	doc_je.remark = doc_nat.remark
	doc_je.user_remark = doc_nat.remark

	doc_jea_debit = frappe.new_doc('Journal Entry Account')
	doc_jea_debit.account = doc_nat.debit_account
	doc_jea_debit.debit = doc_nat.amount
	doc_jea_debit.debit_in_account_currency = doc_nat.amount
	doc_jea_debit.party_type = 'Customer'
	doc_jea_debit.party = doc_nat.customer_id
	doc_jea_debit.user_remark = doc_nat.remark

	doc_jea_credit = frappe.new_doc('Journal Entry Account')
	doc_jea_credit.account = doc_nat.credit_account
	doc_jea_credit.credit = doc_nat.amount
	doc_jea_credit.credit_in_account_currency = doc_nat.amount
	doc_jea_credit.party_type = 'Customer'
	doc_jea_credit.party = doc_nat.customer_id
	doc_jea_credit.user_remark = doc_nat.remark

	doc_je.append('accounts', doc_jea_debit)
	doc_je.append('accounts', doc_jea_credit)

	doc_je.save()
	doc_je.submit()

	frappe.db.set_value('Night Audit Transaction', doc_nat.name, 'journal_entry_id', doc_je.name)
	frappe.db.set_value('Night Audit Transaction', doc_nat.name, 'posting_date', doc_je.posting_date)
	frappe.db.set_value('Night Audit', doc_na.name, 'posting_date', doc_je.posting_date)

	if 'Folio - ' in doc_nat.transaction_type:
		doc_ft = frappe.get_doc('Folio Transaction', doc_nat.transaction_id)
		doc_ft.journal_entry_id = doc_je.name
		doc_ft.save()
	elif 'Hotel Bill Breakdown ' in doc_nat.transaction_type:
		doc_hbb = frappe.get_doc('Hotel Bill Breakdown', doc_nat.transaction_id)
		doc_hbb.journal_entry_id = doc_je.name
		doc_hbb.save()
	elif doc_nat.transaction_type == 'Hotel Bill Refund':
		doc_hbr = frappe.get_doc('Hotel Bill Refund', doc_nat.transaction_id)
		doc_hbr.journal_entry_id = doc_je.name
		doc_hbr.save()
	elif doc_nat.transaction_type == 'Hotel Bill Payments':
		doc_hbp = frappe.get_doc('Hotel Bill Payments', doc_nat.transaction_id)
		doc_hbp.journal_entry_id = doc_je.name
		doc_hbp.save()
	elif doc_nat.transaction_type == 'Hotel Bill - Use Deposit':
		doc_hb = frappe.get_doc('Hotel Bill', doc_nat.transaction_id)
		doc_hb.use_deposit_journal_entry_id = doc_je.name
		doc_hb.save()
	elif doc_nat.transaction_type == 'Hotel Bill - Change':
		doc_hb = frappe.get_doc('Hotel Bill', doc_nat.transaction_id)
		doc_hb.change_journal_entry_id = doc_je.name
		doc_hb.save()
	elif doc_nat.transaction_type == 'AR City Ledger Invoice - Change':
		doc_acli = frappe.get_doc('AR City Ledger Invoice', doc_nat.transaction_id)
		doc_acli.change_journal_entry_id = doc_je.name
		doc_acli.save()
	elif doc_nat.transaction_type == 'AR City Ledger Invoice Payments':
		doc_aclip = frappe.get_doc('AR City Ledger Invoice Payments', doc_nat.transaction_id)
		doc_aclip.journal_entry_id = doc_je.name
		doc_aclip.save()

	return_message = doc_je.name
	return return_message
