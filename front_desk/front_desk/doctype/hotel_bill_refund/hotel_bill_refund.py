# -*- coding: utf-8 -*-
# Copyright (c) 2019, PMM and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class HotelBillRefund(Document):
	pass

@frappe.whitelist()
def get_value_by_desc(desc, field):
    return frappe.db.get_value('Hotel Bill Refund', {'refund_description': desc}, [field])
