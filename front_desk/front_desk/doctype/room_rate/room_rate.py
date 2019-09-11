# -*- coding: utf-8 -*-
# Copyright (c) 2019, PMM and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class RoomRate(Document):
	pass

def calculate_total_amount(doc, method):
	total_rate_weekday = 0.0
	total_rate_weekend = 0.0

	# calculate weekday rate
	for item in doc.get('room_rate_breakdown'):
		sub_total = float(item.breakdown_qty) * float(item.breakdown_amount)
		if (item.breakdown_name != 'Weekend Rate'):
			total_rate_weekday += sub_total

	# calculate weekend rate
	for item in doc.get('room_rate_breakdown'):
		sub_total = float(item.breakdown_qty) * float(item.breakdown_amount)
		if (item.breakdown_name != 'Weekday Rate'):
			total_rate_weekend += sub_total

	doc.rate_weekday = total_rate_weekday
	doc.rate_weekend = total_rate_weekend
