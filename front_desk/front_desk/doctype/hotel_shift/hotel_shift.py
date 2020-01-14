# -*- coding: utf-8 -*-
# Copyright (c) 2020, PMM and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class HotelShift(Document):
	pass

@frappe.whitelist()
def populate_cash_count():
	return [100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000]
