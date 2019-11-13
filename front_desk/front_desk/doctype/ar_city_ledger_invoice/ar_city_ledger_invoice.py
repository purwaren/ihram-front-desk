# -*- coding: utf-8 -*-
# Copyright (c) 2019, PMM and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import datetime
from frappe.model.document import Document

class ARCityLedgerInvoice(Document):
	pass

def calculate_outstanding_amount(doc, method):
	amount = 0.0
	folio_list = doc.get('folio')
	if len(folio_list) > 0:
		for item in folio_list:
			amount += item.amount
	doc.total_amount = amount

def add_ar_invoice_id_to_folio(doc, method):
	folio_list = doc.get('folio')
	if len(folio_list) > 0:
		for item in folio_list:
			frappe.db.set_value('Folio', item.folio_id, 'ar_city_ledger_invoice_id', doc.name)

def remove_ar_invoice_id_from_folio(doc, method):
	folio_list = doc.get('folio')
	folio_list_from_db = frappe.get_all('Folio', filters={'ar_city_ledger_invoice_id': doc.name}, fields=['name'])
	list_from_invoice = []
	list_from_db = []
	diff = []

	for item in folio_list:
		list_from_invoice.append(item.folio_id)
	for item2 in folio_list_from_db:
		list_from_db.append(item2.name)

	if len(list_from_db) > len(list_from_invoice):
		diff = list(set(list_from_db).difference(list_from_invoice))

	if len(diff) > 0:
		for folio_item in diff:
			frappe.db.set_value('Folio', item.folio_id, 'ar_city_ledger_invoice_id', None)

def get_mode_of_payment_account(mode_of_payment_id, company_name):
	return frappe.db.get_value('Mode of Payment Account', {'parent': mode_of_payment_id, 'company': company_name}, "default_account")

@frappe.whitelist()
def make_payment_ar_city_ledger_invoice(ar_city_ledger_invoice_id, latest_outstanding_amount):
	acli = frappe.get_doc('AR City Ledger Invoice', ar_city_ledger_invoice_id)
	acli_payment_details = acli.get('payment_details')
	acli_folio = acli.get('folio')

	if float(latest_outstanding_amount) > 0:
		frappe.msgprint("There are still outstanding amount needed to be paid")
	else:
		for payment_item in acli_payment_details:
			piutang_city_ledger = frappe.db.get_list('Account', filters={'account_number': '1132.002'})[0].name
			debit_account_name = get_mode_of_payment_account(payment_item.mode_of_payment,
															 frappe.get_doc("Global Defaults").default_company)
			frappe.msgprint(piutang_city_ledger)
			frappe.msgprint(debit_account_name)
			title = 'AR City Ledger Payment (' + str(payment_item.mode_of_payment) + '): ' + payment_item.name
			remark = title + ' -@' + str(payment_item.creation)

			payment_journal_entry = frappe.new_doc('Journal Entry')
			payment_journal_entry.title = title
			payment_journal_entry.voucher_type = 'Journal Entry'
			payment_journal_entry.naming_series = 'ACC-JV-.YYYY.-'
			payment_journal_entry.posting_date = datetime.date.today()
			payment_journal_entry.company = frappe.get_doc('Global Defaults').default_company
			payment_journal_entry.total_amount_currency = frappe.get_doc('Global Defaults').default_currency
			payment_journal_entry.remark = remark
			payment_journal_entry.user_remark = remark

			payment_debit = frappe.new_doc('Journal Entry Account')
			payment_debit.account = debit_account_name
			payment_debit.debit = payment_item.payment_amount
			payment_debit.debit_in_account_currency = payment_item.payment_amount
			payment_debit.party_type = 'Customer'
			payment_debit.party = acli.customer_id
			payment_debit.user_remark = remark

			payment_credit = frappe.new_doc('Journal Entry Account')
			payment_credit.account = piutang_city_ledger
			payment_credit.credit = payment_item.payment_amount
			payment_credit.credit_in_account_currency = payment_item.payment_amount
			payment_credit.party_type = 'Customer'
			payment_credit.party = acli.customer_id
			payment_credit.user_remark = remark

			payment_journal_entry.append('accounts', payment_debit)
			payment_journal_entry.append('accounts', payment_credit)

			payment_journal_entry.save()
			payment_journal_entry.submit()

		if float(acli.change_amount) > 0:
			kas_kecil = frappe.db.get_list('Account', filters={'account_number': '1111.001'})[0].name
			piutang_city_ledger = frappe.db.get_list('Account', filters={'account_number': '1132.002'})[0].name
			change_title = 'AR City Ledger Change: ' + acli.name
			change_remark = change_title + ' -@' + str(acli.creation)

			change_journal_entry = frappe.new_doc('Journal Entry')
			change_journal_entry.title = change_title
			change_journal_entry.voucher_type = 'Journal Entry'
			change_journal_entry.naming_series = 'ACC-JV-.YYYY.-'
			change_journal_entry.posting_date = datetime.date.today()
			change_journal_entry.company = frappe.get_doc('Global Defaults').default_company
			change_journal_entry.total_amount_currency = frappe.get_doc('Global Defaults').default_currency
			change_journal_entry.remark = change_remark
			change_journal_entry.user_remark = change_remark

			change_je_debit = frappe.new_doc('Journal Entry Account')
			change_je_debit.account = piutang_city_ledger
			change_je_debit.debit = acli.rounded_change_amount
			change_je_debit.debit_in_account_currency = acli.rounded_change_amount
			change_je_debit.party_type = 'Customer'
			change_je_debit.party = acli.customer_id
			change_je_debit.user_remark = change_remark

			change_je_credit = frappe.new_doc('Journal Entry Account')
			change_je_credit.account = kas_kecil
			change_je_credit.credit = acli.rounded_change_amount
			change_je_credit.credit_in_account_currency = acli.rounded_change_amount
			change_je_credit.party_type = 'Customer'
			change_je_credit.party = acli.customer_id
			change_je_credit.user_remark = change_remark

			change_journal_entry.append('accounts', change_je_debit)
			change_journal_entry.append('accounts', change_je_credit)

			change_journal_entry.save()
			change_journal_entry.submit()

		frappe.db.set_value('AR City Ledger Invoice', ar_city_ledger_invoice_id, 'is_paid', 1)

		for acli_item in acli_folio:
			frappe.db.set_value('Folio', acli_item.folio_id, 'city_ledger_payment_final', 1)

		return 1
