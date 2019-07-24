# -*- coding: utf-8 -*-
# Copyright (c) 2019, PMM and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.website.website_generator import WebsiteGenerator

class HotelRoom(WebsiteGenerator):
	pass

@frappe.whitelist()
def get_images(room_type):
		return frappe.db.get_list('File', filters={'attached_to_doctype':'Room Type', 'attached_to_name':room_type}, fields=['file_url'])
