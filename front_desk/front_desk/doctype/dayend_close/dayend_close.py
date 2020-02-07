# -*- coding: utf-8 -*-
# Copyright (c) 2020, PMM and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class DayendClose(Document):
	pass

@frappe.whitelist()
def is_there_open_dayend_close():
	if frappe.get_all('Dayend Close', {'is_closed': 0}):
		return 1
	else:
		return 2
