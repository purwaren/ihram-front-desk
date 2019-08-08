# -*- coding: utf-8 -*-
# Copyright (c) 2019, PMM and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import json
import frappe
from frappe.website.website_generator import WebsiteGenerator

class HotelRoom(WebsiteGenerator):
	pass

@frappe.whitelist()
def get_images(room_type):
	return frappe.db.get_list('File', filters={'attached_to_doctype':'Room Type', 'attached_to_name':room_type}, fields=['file_url'])

@frappe.whitelist()
def set_availability(room_name_list, availability):
	room_name_list = json.loads(room_name_list)
	for room_name in room_name_list:
		frappe.db.set_value('Hotel Room', room_name, 'status', availability)