# -*- coding: utf-8 -*-
# Copyright (c) 2019, PMM and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class HotelTax(Document):
	pass

def autoname(self):
	if self.hotel_tax_title:
		company = frappe.get_doc("Global Defaults").default_company
		abbr = frappe.get_cached_value('Company', company, 'abbr')
		self.name = '{0} - {1}'.format(self.hotel_tax_title, abbr)

def autofill_hotel_tax_value(doc, method):
	value = ""
	tax_breakdown = doc.get('hotel_tax_breakdown')
	for index, item in enumerate(tax_breakdown):
		if index == (len(tax_breakdown) - 1):
			value = value + '(' + item.breakdown_description + ').'
		else:
			value = value + '(' + item.breakdown_description + ') + '

	doc.hotel_tax_value = value
