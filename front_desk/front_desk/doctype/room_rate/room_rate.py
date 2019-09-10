# -*- coding: utf-8 -*-
# Copyright (c) 2019, PMM and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class RoomRate(Document):
	pass

def calculate_total_amount(doc, method):
	total_rate = 0.0
	for item in doc.get('room_rate_breakdown'):
		sub_total = float(item.breakdown_qty) * float(item.breakdown_amount)
		total_rate += sub_total

	doc.rate = total_rate
