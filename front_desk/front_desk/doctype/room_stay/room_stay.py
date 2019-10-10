# -*- coding: utf-8 -*-
# Copyright (c) 2019, PMM and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import datetime
import frappe
from frappe.model.document import Document
from front_desk.front_desk.doctype.folio.folio import get_folio_name
from front_desk.front_desk.doctype.room_rate.room_rate import get_rate_after_tax

class RoomStay(Document):
    pass

@frappe.whitelist()
def get_room_stay_by_name(name):
    return frappe.get_doc('Room Stay', name)

def get_room_stay_name_by_parent(parent, parentfield, parenttype):
    return frappe.db.get_value('Room Stay', {'parent':parent, 'parentfield':parentfield, 'parenttype':parenttype}, ['name'])

@frappe.whitelist()
def change_parent(parent_now, parentfield_now, parenttype_now, parent_new, parentfield_new, parenttype_new):
    frappe.db.sql('UPDATE `tabRoom Stay` SET parent=%s, parentfield=%s, parenttype=%s WHERE parent=%s AND parentfield=%s AND parenttype=%s', (parent_new, parentfield_new, parenttype_new, parent_now, parentfield_now, parenttype_now))

def is_this_weekday(the_date):
    weekno = the_date.weekday()
    if weekno < 5:
        return True
    else:
        return False

@frappe.whitelist()
def add_early_checkin(room_stay_id):
    room_stay = frappe.get_doc('Room Stay', room_stay_id)

    if room_stay.is_early_checkin == 1:
        ec_percentage = frappe.db.get_value('Early Check In Percentage',
                                            {'early_checkin_name': room_stay.early_checkin_rate},
                                            ['early_checkin_percentage'])
        ec_remark = 'Early Check In Room ' + room_stay.room_id + ": " + room_stay.early_checkin_rate + " ( " + str(
            ec_percentage) + "% of Room Rate)"
        exist_folio_trx_ec = frappe.db.exists('Folio Transaction', {'parent':get_folio_name(room_stay.reservation_id), 'remark': ec_remark})
        if not exist_folio_trx_ec:
            je_debit_account = frappe.db.get_list('Account', filters={'account_number': '1132.001'})[0].name
            je_credit_account = frappe.db.get_list('Account', filters={'account_number': '4320.001'})[0].name
            cust_name = frappe.get_doc('Customer', frappe.get_doc('Reservation', room_stay.reservation_id).customer_id).name
            room_rate_doc = frappe.get_doc('Room Rate', room_stay.room_rate)
            if is_this_weekday(room_stay.arrival):
                special_charge_amount = room_rate_doc.rate_weekday * ec_percentage/100.0
            else:
                special_charge_amount = room_rate_doc.rate_weekend * ec_percentage/100.0
            doc_journal_entry = frappe.new_doc('Journal Entry')
            doc_journal_entry.title = ec_remark
            doc_journal_entry.voucher_type = 'Journal Entry'
            doc_journal_entry.naming_series = 'ACC-JV-.YYYY.-'
            doc_journal_entry.posting_date = datetime.date.today()
            doc_journal_entry.company = frappe.get_doc("Global Defaults").default_company
            doc_journal_entry.total_amount_currency = frappe.get_doc("Global Defaults").default_currency
            doc_journal_entry.remark = ec_remark
            doc_journal_entry.user_remark = ec_remark

            doc_debit = frappe.new_doc('Journal Entry Account')
            doc_debit.account = je_debit_account
            doc_debit.debit = special_charge_amount
            doc_debit.party_type = 'Customer'
            doc_debit.party = cust_name
            doc_debit.debit_in_account_currency = special_charge_amount
            doc_debit.user_remark = ec_remark

            doc_credit = frappe.new_doc('Journal Entry Account')
            doc_credit.account = je_credit_account
            doc_credit.credit = special_charge_amount
            doc_credit.party_type = 'Customer'
            doc_credit.party = cust_name
            doc_credit.credit_in_account_currency = special_charge_amount
            doc_credit.user_remark = ec_remark

            doc_journal_entry.append('accounts', doc_debit)
            doc_journal_entry.append('accounts', doc_credit)

            doc_journal_entry.save()
            doc_journal_entry.submit()

            folio_name = get_folio_name(room_stay.reservation_id)
            doc_folio = frappe.get_doc('Folio', folio_name)

            doc_folio_transaction = frappe.new_doc('Folio Transaction')
            doc_folio_transaction.folio_id = doc_folio.name
            doc_folio_transaction.amount = special_charge_amount
            doc_folio_transaction.flag = 'Debit'
            doc_folio_transaction.account_id = je_debit_account
            doc_folio_transaction.against_account_id = je_credit_account
            doc_folio_transaction.remark = ec_remark
            doc_folio_transaction.is_special_charge = 1
            doc_folio_transaction.is_void = 0

            doc_folio.append('transaction_detail', doc_folio_transaction)
            doc_folio.save()

@frappe.whitelist()
def add_late_checkout(room_stay_id):
    room_stay = frappe.get_doc('Room Stay', room_stay_id)

    if room_stay.is_late_checkout == 1:
        lc_percentage = frappe.db.get_value('Late Check Out Percentage',
                                            {'late_checkout_name': room_stay.late_checkout_rate},
                                            ['late_checkout_percentage'])
        lc_remark = 'Late Check Out Room ' + room_stay.room_id + ": " + room_stay.late_checkout_rate + " ( " + str(
            lc_percentage) + "% of Room Rate)"
        exist_folio_trx_lc = frappe.db.exists('Folio Transaction', {'parent':get_folio_name(room_stay.reservation_id), 'remark': lc_remark})
        if not exist_folio_trx_lc:
            je_debit_account = frappe.db.get_list('Account', filters={'account_number': '1132.001'})[0].name
            je_credit_account = frappe.db.get_list('Account', filters={'account_number': '4320.001'})[0].name
            cust_name = frappe.get_doc('Customer', frappe.get_doc('Reservation', room_stay.reservation_id).customer_id).name
            room_rate_doc = frappe.get_doc('Room Rate', room_stay.room_rate)

            if is_this_weekday(room_stay.departure):
                special_charge_amount = room_rate_doc.rate_weekday * lc_percentage / 100.0
            else:
                special_charge_amount = room_rate_doc.rate_weekend * lc_percentage / 100.0

            doc_journal_entry = frappe.new_doc('Journal Entry')
            doc_journal_entry.title = lc_remark
            doc_journal_entry.voucher_type = 'Journal Entry'
            doc_journal_entry.naming_series = 'ACC-JV-.YYYY.-'
            doc_journal_entry.posting_date = datetime.date.today()
            doc_journal_entry.company = frappe.get_doc("Global Defaults").default_company
            doc_journal_entry.total_amount_currency = frappe.get_doc("Global Defaults").default_currency
            doc_journal_entry.remark = lc_remark
            doc_journal_entry.user_remark = lc_remark

            doc_debit = frappe.new_doc('Journal Entry Account')
            doc_debit.account = je_debit_account
            doc_debit.debit = special_charge_amount
            doc_debit.party_type = 'Customer'
            doc_debit.party = cust_name
            doc_debit.debit_in_account_currency = special_charge_amount
            doc_debit.user_remark = lc_remark

            doc_credit = frappe.new_doc('Journal Entry Account')
            doc_credit.account = je_credit_account
            doc_credit.credit = special_charge_amount
            doc_credit.party_type = 'Customer'
            doc_credit.party = cust_name
            doc_credit.credit_in_account_currency = special_charge_amount
            doc_credit.user_remark = lc_remark

            doc_journal_entry.append('accounts', doc_debit)
            doc_journal_entry.append('accounts', doc_credit)

            doc_journal_entry.save()
            doc_journal_entry.submit()

            folio_name = get_folio_name(room_stay.reservation_id)
            doc_folio = frappe.get_doc('Folio', folio_name)

            doc_folio_transaction = frappe.new_doc('Folio Transaction')
            doc_folio_transaction.folio_id = doc_folio.name
            doc_folio_transaction.amount = special_charge_amount
            doc_folio_transaction.flag = 'Debit'
            doc_folio_transaction.account_id = je_debit_account
            doc_folio_transaction.against_account_id = je_credit_account
            doc_folio_transaction.remark = lc_remark
            doc_folio_transaction.is_special_charge = 1
            doc_folio_transaction.is_void = 0

            doc_folio.append('transaction_detail', doc_folio_transaction)
            doc_folio.save()

def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + datetime.timedelta(n)

@frappe.whitelist()
def calculate_room_stay_bill(arrival, departure, room_rate_id, discount):
    start = datetime.datetime.strptime(arrival, "%Y-%m-%d %H:%M:%S")
    day_before_start = datetime.datetime.strptime((datetime.datetime.strftime(start - datetime.timedelta(1), "%Y-%m-%d %H:%M:%S")), "%Y-%m-%d %H:%M:%S")
    end = datetime.datetime.strptime(departure, "%Y-%m-%d %H:%M:%S")
    day_before_end = datetime.datetime.strptime(
        (datetime.datetime.strftime(end - datetime.timedelta(1), "%Y-%m-%d %H:%M:%S")), "%Y-%m-%d %H:%M:%S")
    total_day = (end - start).days
    weekday = 0
    day_generator = (day_before_start + datetime.timedelta(x + 1) for x in range((day_before_end - day_before_start).days))
    for day in day_generator:
        if day.weekday() < 5:
            weekday = weekday + 1
    weekend = total_day - weekday
    rate_weekday_taxed = get_rate_after_tax(room_rate_id, 'Weekday Rate', discount)
    rate_weekend_taxed = get_rate_after_tax(room_rate_id, 'Weekend Rate', discount)

    total_rate = (float(weekday) * rate_weekday_taxed) + (float(weekend) * rate_weekend_taxed)

    return total_rate

@frappe.whitelist()
def get_value(room_stay_id, field):
    return frappe.db.get_value('Room Stay', room_stay_id, [field])


def checkout_early_refund(room_stay_id):
    room_stay = frappe.get_doc('Room Stay', room_stay_id)
    if room_stay.is_need_refund == 1:
        refund_amount = float(room_stay.old_total_bill_amount) - float(room_stay.total_bill_amount)
    refund_description = 'Checkout Early Refund of Room Stay:' + str(room_stay.name) + ' Reservation: ' + str(room_stay.reservation_id)
    kas_dp_kamar = frappe.db.get_list('Account', filters={'account_number': '2121.002'})[0].name
    kas_fo = frappe.db.get_list('Account', filters={'account_number': '1111.003'})[0].name
    hotel_bill = frappe.get_doc('Hotel Bill', {'reservation_id': room_stay.parent})

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