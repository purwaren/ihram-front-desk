# -*- coding: utf-8 -*-
# Copyright (c) 2019, PMM and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class ARCityLedger(Document):
	pass

@frappe.whitelist()
def get_folio_list_by_order_channel(hotel_order_channel):
	return_list = []

	ar_city_ledger_list = frappe.get_all('AR City Ledger',
										 filters = [['hotel_order_channel', '=', hotel_order_channel]],
										 fields = ['folio_id'])

	for item in ar_city_ledger_list:
		return_list.append(item.folio_id)

	return return_list
