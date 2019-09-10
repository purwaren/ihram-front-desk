# -*- coding: utf-8 -*-
# Copyright (c) 2019, PMM and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import datetime
import frappe
from frappe.model.document import Document

class RoomStay(Document):
	pass

def validate_special_charge(doc, method):
	je_credit_account = frappe.db.get_list('Account', filters={'account_number': '1132.001'})[0].name
	je_debit_account = frappe.db.get_list('Account', filters={'account_number': '4320.001'})[0].name

	if (doc.is_early_checkin == 1):
		percentage = frappe.db.get_value('Early Check In Percentage', {'early_checkin_name': doc.early_checkin_rate}, ['early_checkin_percentage'])
		special_charge_amount = doc.rate * percentage
		remark = 'Early Check In Room: ' + doc.room_id

		doc_journal_entry = frappe.new_doc('Journal Entry')
		doc_journal_entry.voucher_type = 'Journal Entry'
		doc_journal_entry.naming_series = 'ACC-JV-.YYYY.-'
		doc_journal_entry.posting_date = datetime.date.today()
		doc_journal_entry.company = frappe.get_doc("Global Defaults").default_company
		doc_journal_entry.total_amount_currency = frappe.get_doc("Global Defaults").default_currency
		doc_journal_entry.remark = remark
		doc_journal_entry.user_remark = remark

		doc_debit = frappe.new_doc('Journal Entry Account')
		doc_debit.account = je_debit_account
		doc_debit.debit = special_charge_amount
		doc_debit.debit_in_account_currency = special_charge_amount
		doc_debit.user_remark = remark

		doc_credit = frappe.new_doc('Journal Entry Account')
		doc_credit.account = je_credit_account
		doc_credit.credit = special_charge_amount
		doc_credit.credit_in_account_currency = special_charge_amount
		doc_credit.user_remark = remark

		doc_journal_entry.append('accounts', doc_debit)
		doc_journal_entry.append('accounts', doc_credit)

		doc_journal_entry.save()
		doc_journal_entry.submit()

		folio_name = frappe.db.get_value('Folio', {'reservation_id': doc.reservation_id}, ['name'])
		doc_folio = frappe.get_doc('Folio', folio_name)

		doc_folio_transaction = frappe.new_doc('Folio Transaction')
		doc_folio_transaction.folio_id = doc_folio.name
		doc_folio_transaction.amount = special_charge_amount
		doc_folio_transaction.flag = 'Debit'
		doc_folio_transaction.account_id = je_credit_account
		doc_folio_transaction.against_account_id = je_debit_account
		doc_folio_transaction.remark = remark
		doc_folio_transaction.is_void = 0

		doc_folio.append('transaction_detail', doc_folio_transaction)
		doc_folio.save()

	if (doc.is_late_checkout == 1):
		percentage = frappe.db.get_value('Late Check Out Percentage', {'late_checkout_name': doc.late_checkout_rate}, ['late_checkout_percentage'])
		special_charge_amount = doc.rate * percentage
		remark = 'Late Check Out Room: ' + doc.room_id

		doc_journal_entry = frappe.new_doc('Journal Entry')
		doc_journal_entry.voucher_type = 'Journal Entry'
		doc_journal_entry.naming_series = 'ACC-JV-.YYYY.-'
		doc_journal_entry.posting_date = datetime.date.today()
		doc_journal_entry.company = frappe.get_doc("Global Defaults").default_company
		doc_journal_entry.total_amount_currency = frappe.get_doc("Global Defaults").default_currency
		doc_journal_entry.remark = remark
		doc_journal_entry.user_remark = remark

		doc_debit = frappe.new_doc('Journal Entry Account')
		doc_debit.account = je_debit_account
		doc_debit.debit = special_charge_amount
		doc_debit.debit_in_account_currency = special_charge_amount
		doc_debit.user_remark = remark

		doc_credit = frappe.new_doc('Journal Entry Account')
		doc_credit.account = je_credit_account
		doc_credit.credit = special_charge_amount
		doc_credit.credit_in_account_currency = special_charge_amount
		doc_credit.user_remark = remark

		doc_journal_entry.append('accounts', doc_debit)
		doc_journal_entry.append('accounts', doc_credit)

		doc_journal_entry.save()
		doc_journal_entry.submit()

		folio_name = frappe.db.get_value('Folio', {'reservation_id': doc.reservation_id}, ['name'])
		doc_folio = frappe.get_doc('Folio', folio_name)

		doc_folio_transaction = frappe.new_doc('Folio Transaction')
		doc_folio_transaction.folio_id = doc_folio.name
		doc_folio_transaction.amount = special_charge_amount
		doc_folio_transaction.flag = 'Debit'
		doc_folio_transaction.account_id = je_credit_account
		doc_folio_transaction.against_account_id = je_debit_account
		doc_folio_transaction.remark = remark
		doc_folio_transaction.is_void = 0

		doc_folio.append('transaction_detail', doc_folio_transaction)
		doc_folio.save()
