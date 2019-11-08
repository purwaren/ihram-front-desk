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
	hotel_room_list = frappe.get_all('Hotel Room', filters={'room_status': 'Occupied Clean'}, fields=['room_status', 'name'])
	for room in hotel_room_list:
		frappe.db.set_value('Hotel Room', room.name, 'room_status', 'Occupied Dirty')

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

@frappe.whitelist()
def get_all_hotel_room():
	return frappe.db.get_all('Hotel Room',
				fields=['name', 'room_type', 'bed_type', 'allow_smoke', 'view', 'room_status'],
				order_by='name asc'
			)

@frappe.whitelist()
def copy_amenities_template(amenities_type_id):
	amenities_list = frappe.get_all('Amenities', filters={'parent': amenities_type_id}, fields=['*'])
	return amenities_list

def calculate_total_amenities_cost(doc, method):
	amenities_list = doc.get('amenities')
	total_cost = 0.0
	for item in amenities_list:
		item_price = frappe.db.get_value('Item Price', {'item_code':item.item, 'item_name': item.item_name, 'buying': 1}, ['price_list_rate'])
		total_cost += float(item_price) * float(item.qty)

	doc.total_amenities_cost = total_cost
