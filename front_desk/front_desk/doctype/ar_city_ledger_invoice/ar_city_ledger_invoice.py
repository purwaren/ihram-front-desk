# -*- coding: utf-8 -*-
# Copyright (c) 2019, PMM and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
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