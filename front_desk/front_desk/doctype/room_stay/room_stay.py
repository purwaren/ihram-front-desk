# -*- coding: utf-8 -*-
# Copyright (c) 2019, PMM and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import datetime
import frappe
from frappe.model.document import Document
from front_desk.front_desk.doctype.folio.folio import get_folio_name
from front_desk.front_desk.doctype.room_rate.room_rate import get_rate_after_tax
from front_desk.front_desk.doctype.room_booking.room_booking import update_by_room_stay

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

    exist_folio_trx_ec = frappe.db.exists('Folio Transaction', {'parent': get_folio_name(room_stay.reservation_id),
                                                              'remark': ("like",
                                                                         'Early Check In Room ' + room_stay.room_id + '%')})
    if room_stay.is_early_checkin == 1:
        ec_percentage = frappe.db.get_value('Early Check In Percentage',
                                            {'early_checkin_name': room_stay.early_checkin_rate},
                                            ['early_checkin_percentage'])
        ec_remark = 'Early Check In Room ' + room_stay.room_id + ": " + room_stay.early_checkin_rate + " ( " + str(
            ec_percentage) + "% of Room Rate)"
        if not exist_folio_trx_ec:
            je_debit_account = frappe.db.get_list('Account', filters={'account_number': '1132.001'})[0].name
            je_credit_account = frappe.db.get_list('Account', filters={'account_number': '4320.001'})[0].name
            cust_name = frappe.get_doc('Customer', frappe.get_doc('Reservation', room_stay.reservation_id).customer_id).name
            room_rate_doc = frappe.get_doc('Room Rate', room_stay.room_rate)
            if is_this_weekday(room_stay.arrival):
                special_charge_amount = room_rate_doc.rate_weekday * ec_percentage/100.0
            else:
                special_charge_amount = room_rate_doc.rate_weekend * ec_percentage/100.

            folio_name = get_folio_name(room_stay.reservation_id)
            doc_folio = frappe.get_doc('Folio', folio_name)

            doc_folio_transaction = frappe.new_doc('Folio Transaction')
            doc_folio_transaction.folio_id = doc_folio.name
            doc_folio_transaction.amount = special_charge_amount
            doc_folio_transaction.amount_after_tax = special_charge_amount
            doc_folio_transaction.flag = 'Debit'
            doc_folio_transaction.account_id = je_debit_account
            doc_folio_transaction.against_account_id = je_credit_account
            doc_folio_transaction.room_stay_id = room_stay.name
            doc_folio_transaction.remark = ec_remark
            doc_folio_transaction.is_special_charge = 1
            doc_folio_transaction.is_void = 0

            doc_folio.append('transaction_detail', doc_folio_transaction)
            doc_folio.save()

            # JOURNAL ENTRY CREATION: EARLY CHECKIN
            # doc_journal_entry = frappe.new_doc('Journal Entry')
            # doc_journal_entry.title = "JE " + doc_folio_transaction.name
            # doc_journal_entry.voucher_type = 'Journal Entry'
            # doc_journal_entry.naming_series = 'ACC-JV-.YYYY.-'
            # doc_journal_entry.posting_date = datetime.date.today()
            # doc_journal_entry.company = frappe.get_doc("Global Defaults").default_company
            # doc_journal_entry.total_amount_currency = frappe.get_doc("Global Defaults").default_currency
            # doc_journal_entry.remark = doc_folio_transaction.name + "-" + ec_remark
            # doc_journal_entry.user_remark = doc_folio_transaction.name + "-" + ec_remark
            #
            # doc_debit = frappe.new_doc('Journal Entry Account')
            # doc_debit.account = je_debit_account
            # doc_debit.debit = special_charge_amount
            # doc_debit.party_type = 'Customer'
            # doc_debit.party = cust_name
            # doc_debit.debit_in_account_currency = special_charge_amount
            # doc_debit.user_remark = doc_folio_transaction.name + "-" + ec_remark
            #
            # doc_credit = frappe.new_doc('Journal Entry Account')
            # doc_credit.account = je_credit_account
            # doc_credit.credit = special_charge_amount
            # doc_credit.party_type = 'Customer'
            # doc_credit.party = cust_name
            # doc_credit.credit_in_account_currency = special_charge_amount
            # doc_credit.user_remark = doc_folio_transaction.name + "-" + ec_remark
            #
            # doc_journal_entry.append('accounts', doc_debit)
            # doc_journal_entry.append('accounts', doc_credit)
            #
            # doc_journal_entry.save()
            # doc_journal_entry.submit()

    else:
        if exist_folio_trx_ec:
            folio_trx_ec = frappe.get_doc('Folio Transaction',
                                          {'parent': get_folio_name(room_stay.reservation_id),
                                           'remark': ("like",
                                                      'Early Check In Room ' + room_stay.room_id + '%')})
            if frappe.db.exists('Journal Entry', {'title': 'JE ' + folio_trx_ec.name}):
                doc_je = frappe.get_doc('Journal Entry', {'title': 'JE ' + folio_trx_ec.name})
                doc_debit_je = frappe.get_doc('Journal Entry Account', {'parent': doc_je.name, 'credit': 0.0})
                doc_credit_je = frappe.get_doc('Journal Entry Account', {'parent': doc_je.name, 'debit': 0.0})
                doc_hotel_bill_breakdown = frappe.get_doc('Hotel Bill Breakdown',
                                                          {'billing_folio_trx_id': folio_trx_ec.name})

                # JOURNAL ENTRY CREATION: FLIP EARLY CHECKIN JOURNAL ENTRY: LIKELY WILL NOT BE USED
                # doc_journal_entry = frappe.new_doc('Journal Entry')
                # doc_journal_entry.title = "Flip " + doc_je.title
                # doc_journal_entry.voucher_type = 'Journal Entry'
                # doc_journal_entry.naming_series = 'ACC-JV-.YYYY.-'
                # doc_journal_entry.posting_date = datetime.date.today()
                # doc_journal_entry.company = frappe.get_doc("Global Defaults").default_company
                # doc_journal_entry.total_amount_currency = frappe.get_doc("Global Defaults").default_currency
                # doc_journal_entry.remark = "Flip " + doc_je.remark
                # doc_journal_entry.user_remark = "Flip " + doc_je.user_remark
                #
                # doc_debit = frappe.new_doc('Journal Entry Account')
                # doc_debit.account = doc_credit_je.account
                # doc_debit.debit = doc_debit_je.debit
                # doc_debit.party_type = 'Customer'
                # doc_debit.party = doc_debit_je.party
                # doc_debit.debit_in_account_currency = doc_debit_je.debit_in_account_currency
                # doc_debit.user_remark = "Flip " + doc_debit_je.user_remark
                #
                # doc_credit = frappe.new_doc('Journal Entry Account')
                # doc_credit.account = doc_debit_je.account
                # doc_credit.credit = doc_credit_je.credit
                # doc_credit.party_type = 'Customer'
                # doc_credit.party = doc_credit_je.party
                # doc_credit.credit_in_account_currency = doc_credit_je.credit_in_account_currency
                # doc_credit.user_remark = "Flip " + doc_credit_je.user_remark
                #
                # doc_journal_entry.append('accounts', doc_debit)
                # doc_journal_entry.append('accounts', doc_credit)
                #
                # doc_journal_entry.save()
                # doc_journal_entry.submit()

                frappe.delete_doc("Folio Transaction", folio_trx_ec.name)
                frappe.delete_doc("Hotel Bill Breakdown", doc_hotel_bill_breakdown.name)

@frappe.whitelist()
def add_late_checkout(room_stay_id):
    room_stay = frappe.get_doc('Room Stay', room_stay_id)
    exist_folio_trx_lc = frappe.db.exists('Folio Transaction', {'parent': get_folio_name(room_stay.reservation_id),
                                                              'remark': ("like",
                                                                         'Late Check Out Room ' + room_stay.room_id + '%')})
    if room_stay.is_late_checkout == 1:
        lc_percentage = frappe.db.get_value('Late Check Out Percentage',
                                            {'late_checkout_name': room_stay.late_checkout_rate},
                                            ['late_checkout_percentage'])
        lc_remark = 'Late Check Out Room ' + room_stay.room_id + ": " + room_stay.late_checkout_rate + " ( " + str(
            lc_percentage) + "% of Room Rate)"
        if not exist_folio_trx_lc:
            je_debit_account = frappe.db.get_list('Account', filters={'account_number': '1132.001'})[0].name
            je_credit_account = frappe.db.get_list('Account', filters={'account_number': '4320.001'})[0].name
            cust_name = frappe.get_doc('Customer', frappe.get_doc('Reservation', room_stay.reservation_id).customer_id).name
            room_rate_doc = frappe.get_doc('Room Rate', room_stay.room_rate)

            if is_this_weekday(room_stay.departure):
                special_charge_amount = room_rate_doc.rate_weekday * lc_percentage / 100.0
            else:
                special_charge_amount = room_rate_doc.rate_weekend * lc_percentage / 100.0

            folio_name = get_folio_name(room_stay.reservation_id)
            doc_folio = frappe.get_doc('Folio', folio_name)

            doc_folio_transaction = frappe.new_doc('Folio Transaction')
            doc_folio_transaction.folio_id = doc_folio.name
            doc_folio_transaction.amount = special_charge_amount
            doc_folio_transaction.amount_after_tax = special_charge_amount
            doc_folio_transaction.flag = 'Debit'
            doc_folio_transaction.account_id = je_debit_account
            doc_folio_transaction.against_account_id = je_credit_account
            doc_folio_transaction.room_stay_id = room_stay.name
            doc_folio_transaction.remark = lc_remark
            doc_folio_transaction.is_special_charge = 1
            doc_folio_transaction.is_void = 0

            doc_folio.append('transaction_detail', doc_folio_transaction)
            doc_folio.save()
            # JOURNAL ENTRY CREATION: LATE CHECKOUT
            # doc_journal_entry = frappe.new_doc('Journal Entry')
            # doc_journal_entry.title = "JE " + doc_folio_transaction.name
            # doc_journal_entry.voucher_type = 'Journal Entry'
            # doc_journal_entry.naming_series = 'ACC-JV-.YYYY.-'
            # doc_journal_entry.posting_date = datetime.date.today()
            # doc_journal_entry.company = frappe.get_doc("Global Defaults").default_company
            # doc_journal_entry.total_amount_currency = frappe.get_doc("Global Defaults").default_currency
            # doc_journal_entry.remark = doc_folio_transaction.name + "-" + lc_remark
            # doc_journal_entry.user_remark = doc_folio_transaction.name + "-" + lc_remark
            #
            # doc_debit = frappe.new_doc('Journal Entry Account')
            # doc_debit.account = je_debit_account
            # doc_debit.debit = special_charge_amount
            # doc_debit.party_type = 'Customer'
            # doc_debit.party = cust_name
            # doc_debit.debit_in_account_currency = special_charge_amount
            # doc_debit.user_remark = doc_folio_transaction.name + "-" + lc_remark
            #
            # doc_credit = frappe.new_doc('Journal Entry Account')
            # doc_credit.account = je_credit_account
            # doc_credit.credit = special_charge_amount
            # doc_credit.party_type = 'Customer'
            # doc_credit.party = cust_name
            # doc_credit.credit_in_account_currency = special_charge_amount
            # doc_credit.user_remark = doc_folio_transaction.name + "-" + lc_remark
            #
            # doc_journal_entry.append('accounts', doc_debit)
            # doc_journal_entry.append('accounts', doc_credit)
            #
            # doc_journal_entry.save()
            # doc_journal_entry.submit()
    else:
        if exist_folio_trx_lc:
            folio_trx_lc = frappe.get_doc('Folio Transaction',
                                                  {'parent': get_folio_name(room_stay.reservation_id),
                                                   'remark': ("like",
                                                              'Late Check Out Room ' + room_stay.room_id + '%')})
            if frappe.db.exists('Journal Entry', {'title': 'JE ' + folio_trx_lc.name}):
                doc_je = frappe.get_doc('Journal Entry', {'title': 'JE ' + folio_trx_lc.name})
                doc_debit_je = frappe.get_doc('Journal Entry Account', {'parent': doc_je.name, 'credit': 0.0})
                doc_credit_je = frappe.get_doc('Journal Entry Account', {'parent': doc_je.name, 'debit': 0.0})
                doc_hotel_bill_breakdown = frappe.get_doc('Hotel Bill Breakdown', {'billing_folio_trx_id': folio_trx_lc.name})

                # JOURNAL ENTRY CREATION: FLIP LATE CHECKOUT. LIKELY WILL NOT BE USED
                # doc_journal_entry = frappe.new_doc('Journal Entry')
                # doc_journal_entry.title = "Flip " + doc_je.title
                # doc_journal_entry.voucher_type = 'Journal Entry'
                # doc_journal_entry.naming_series = 'ACC-JV-.YYYY.-'
                # doc_journal_entry.posting_date = datetime.date.today()
                # doc_journal_entry.company = frappe.get_doc("Global Defaults").default_company
                # doc_journal_entry.total_amount_currency = frappe.get_doc("Global Defaults").default_currency
                # doc_journal_entry.remark = "Flip " + doc_je.remark
                # doc_journal_entry.user_remark = "Flip " + doc_je.user_remark
                #
                # doc_debit = frappe.new_doc('Journal Entry Account')
                # doc_debit.account = doc_credit_je.account
                # doc_debit.debit = doc_debit_je.debit
                # doc_debit.party_type = 'Customer'
                # doc_debit.party = doc_debit_je.party
                # doc_debit.debit_in_account_currency = doc_debit_je.debit_in_account_currency
                # doc_debit.user_remark = "Flip " + doc_debit_je.user_remark
                #
                # doc_credit = frappe.new_doc('Journal Entry Account')
                # doc_credit.account = doc_debit_je.account
                # doc_credit.credit = doc_credit_je.credit
                # doc_credit.party_type = 'Customer'
                # doc_credit.party = doc_credit_je.party
                # doc_credit.credit_in_account_currency = doc_credit_je.credit_in_account_currency
                # doc_credit.user_remark = "Flip " + doc_credit_je.user_remark
                #
                # doc_journal_entry.append('accounts', doc_debit)
                # doc_journal_entry.append('accounts', doc_credit)
                #
                # doc_journal_entry.save()
                # doc_journal_entry.submit()

                frappe.delete_doc("Folio Transaction", folio_trx_lc.name)
                frappe.delete_doc("Hotel Bill Breakdown", doc_hotel_bill_breakdown.name)

def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + datetime.timedelta(n)

@frappe.whitelist()
def calculate_room_stay_bill(arrival, departure, room_rate_id, discount, actual_weekday, actual_weekend):
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
    rate_weekday_taxed = get_rate_after_tax(room_rate_id, 'Weekday Rate', discount, actual_weekday)
    rate_weekend_taxed = get_rate_after_tax(room_rate_id, 'Weekend Rate', discount, actual_weekend)

    total_rate = (float(weekday) * rate_weekday_taxed) + (float(weekend) * rate_weekend_taxed)

    return total_rate

@frappe.whitelist()
def get_value(room_stay_id, field):
    return frappe.db.get_value('Room Stay', room_stay_id, [field])


def checkout_early_refund(room_stay_id):
    using_city_ledger = False
    room_stay = frappe.get_doc('Room Stay', room_stay_id)

    rbp_list = frappe.get_all('Room Bill Payments', filters={'parent': room_stay.reservation_id}, fields=["name", "mode_of_payment"])

    for rbp_item in rbp_list:
        if rbp_item.mode_of_payment == 'City Ledger':
            using_city_ledger = True

    if not using_city_ledger:
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
                if refund_amount > 0:
                    refund_item = frappe.new_doc('Hotel Bill Refund')
                    refund_item.naming_series = 'FO-BILL-RFND-.YYYY.-'
                    refund_item.refund_amount = refund_amount
                    refund_item.refund_description = refund_description
                    refund_item.is_refunded = 0
                    refund_item.account = kas_fo
                    refund_item.account_against = kas_dp_kamar

                    hotel_bill.append('bill_refund', refund_item)
                    hotel_bill.save()
    else:
        if room_stay.is_need_refund == 1:
            refund_amount = float(room_stay.old_total_bill_amount) - float(room_stay.total_bill_amount)
            folio_name = frappe.db.get_value('Folio', {'reservation_id': room_stay.reservation_id}, ['name'])
            remark = 'Room Bill Payment: ' + room_stay.room_bill_paid_id + ' (City Ledger) - Reservation: ' + room_stay.reservation_id
            exist_folio_trx_of_city_ledger_payment = frappe.db.exists('Folio Transaction', {'parent': folio_name, 'remark': remark})
            room_bill_payment = frappe.db.get_value('Room Bill Payments',
                                                    {'parent': room_stay.reservation_id, 'mode_of_payment': 'City Ledger'},
                                                    ['name'])
            bill_adjustment_remark = 'City Ledger Bill Adjustment for Room Bill Payment: ' + room_bill_payment
            exist_room_bill_adjustment = frappe.db.exists('Room Bill Adjustment', {'parent': room_stay.reservation_id,
                                                                                   'adjustment_remark': bill_adjustment_remark,
                                                                                   'room_bill_paid_id': room_stay.room_bill_paid_id,
                                                                                   'room_bill_payments_id': room_bill_payment})
            if not exist_room_bill_adjustment:
                bill_adjustment = frappe.new_doc('Room Bill Adjustment')
                bill_adjustment.naming_series = 'FO-BILL-ADJ-.YYYY.-'
                bill_adjustment.adjustment_amount = refund_amount
                bill_adjustment.parent = room_stay.reservation_id
                bill_adjustment.parentfield = 'room_bill_adjustment'
                bill_adjustment.parenttype = 'Reservation'
                bill_adjustment.adjustment_remark = bill_adjustment_remark
                bill_adjustment.room_bill_paid_id = room_stay.room_bill_paid_id
                bill_adjustment.room_bill_payments_id = room_bill_payment
                bill_adjustment.save()

                if exist_folio_trx_of_city_ledger_payment:
                    diff = float(room_stay.old_total_bill_amount) - float(room_stay.total_bill_amount)
                    if diff > 0:
                        # Update Folio Transaction
                        folio_need_updated = frappe.db.get_value('Folio Transaction', {'parent': folio_name, 'remark': remark}, ['name'])
                        folio_need_updated_amount = frappe.db.get_value('Folio Transaction', {'parent': folio_name, 'remark': remark}, ['amount'])
                        new_folio_amount = float(folio_need_updated_amount) - diff
                        frappe.db.set_value("Folio Transaction", folio_need_updated, "amount", new_folio_amount)
                        frappe.db.set_value("Folio Transaction", folio_need_updated, "amount_after_tax", new_folio_amount)

@frappe.whitelist()
def get_room_stay_id_by_room_id(reservation_id, room_id_blah):
    return frappe.get_doc('Room Stay', {'reservation_id': reservation_id, 'room_id': room_id_blah})

@frappe.whitelist()
def checkout_room_stay(room_stay_id):
    room_stay = frappe.get_doc('Room Stay', room_stay_id)
    reservation = frappe.get_doc('Reservation', room_stay.parent)
    if reservation.status == 'In House':
        if room_stay.status == 'Checked In':
            room_stay.departure = frappe.utils.now()
            room_stay.status = 'Checked Out'
            room_stay.save()
            hotel_room = frappe.get_doc('Hotel Room', room_stay.room_id)
            # Update room_status dari hotel_room menjadi "Vacant Dirty"
            hotel_room.room_status = "Vacant Dirty"
            hotel_room.save()
            # Update room booking status
            update_by_room_stay(room_stay_id)

            return "Room " + str(room_stay.room_id) + " successfully checked out."
        else:
            return "Room " + str(room_stay.room_id) + " already checked out."
    else:
        return "Reservation " + str(reservation.name) + " status not In House, can't check out."