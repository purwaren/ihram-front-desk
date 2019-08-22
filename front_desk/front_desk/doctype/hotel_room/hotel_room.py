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
def set_availability_and_room_status(room_name_list, availability, room_status):
	room_name_list = json.loads(room_name_list)
	for room_name in room_name_list:
		frappe.db.set_value('Hotel Room', room_name, 'status', availability)
		frappe.db.set_value('Hotel Room', room_name, 'room_status', room_status)

@frappe.whitelist()
def set_hotel_room_vacant_dirty():
	hotel_room_list = frappe.get_all('Hotel Room', filters={'room_status': 'Occupied Clean'}, fields=['room_status'])
	for room in hotel_room_list:
		room.room_status = "Occupied Dirty"
		room.save()

@frappe.whitelist()
def upgrade_status(room_name_list):
	is_housekeeping = False
	is_housekeeping_supervisor = False

	roles = frappe.get_roles(frappe.session.user)
	for role in roles:
		if role == 'Housekeeping':
			is_housekeeping = True
		elif role == 'Housekeeping Supervisor':
			is_housekeeping_supervisor = True

	room_name_list = json.loads(room_name_list)
	for room_name in room_name_list:
		status = frappe.db.get_value('Hotel Room', room_name, 'room_status')
		if status == 'Occupied Dirty' and is_housekeeping:
			frappe.db.set_value('Hotel Room', room_name, 'room_status', 'Occupied Clean')
		elif status == 'Vacant Dirty' and is_housekeeping:
			frappe.db.set_value('Hotel Room', room_name, 'room_status', 'Vacant Clean')
		elif status == 'Vacant Clean' and is_housekeeping_supervisor:
			frappe.db.set_value('Hotel Room', room_name, 'room_status', 'Vacant Ready')
			frappe.db.set_value('Hotel Room', room_name, 'status', 'AV')