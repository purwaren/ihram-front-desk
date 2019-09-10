from __future__ import print_function, unicode_literals
from frappe import _
import frappe


def get_data():
	config = [
		{
			"label": _("Front Desk"),
			"items": [
				{
					"type": "doctype",
					"name": "Hotel Room",
					"description": _("Hotel Room Management.")
				},
				{
					"type": "doctype",
					"name": "Room Rate",
					"description": "Rate for room"
				},
				{
					"type": "doctype",
					"name": "Amenities Type",
					"description": _("Amenities list for hotel room")
				},
				{
					"type": "doctype",
					"name": "Bed Type",
					"description": _("Bed type configuration")
				},
				{
					"type": "doctype",
					"name": "Room Type",
					"description": _("Room type configuration")
				},
				{
					"type": "doctype",
					"name": "Room Availability",
					"description": _("Room availability configuration")
				},
			]
		}
	]
	return config


def after_install():
	# setup Room Availability
	room_availability_list = [
		['AV', 'Available'],
		['RS', 'Room Sold'],
		['RC', 'Room Compliment'],
		['HU', 'House Use'],
		['OO', 'Out of Order'],
		['OU', 'Office Use'],
		['UC', 'Under Construction'],
	]
	for ra in room_availability_list:
		ra_entry = frappe.new_doc('Room Availability')
		ra_entry.name = ra[0]
		ra_entry.description = ra[1]
		ra_entry.save()


	# setup Hotel Tax
	hotel_tax_list = [
		['None', '0.0'],
		['Tax & Service Include 21%', '21.0'],
		['Tax Only 10%', '10.0'],

	]

	for ht in hotel_tax_list:
		ha_entry = frappe.new_doc('Hotel Tax')
		ha_entry.hotel_tax_description = ht[0]
		# ha_entry.hotel_tax_value = ht[1]
		ha_entry.hotel_tax_value = 0
		ha_entry.save()

	# # setup Chart of Accounts
	# parent_account = frappe.db.get_list('Account', filters={'account_number': '1111.000'})[0].name
	# account_list = [
	# 	['Kas Front Office', '1111.003'],
	# 	['Kas Kitchen', '1111.004'],
	# 	['Kas F&B', '1111.005'],
	# 	['Kas Housekeeping', '1111.006'],
	# ]
	#
	# for ac in account_list:
	# 	ac_entry = frappe.new_doc('Account')
	# 	ac_entry.account_name = ac[0]
	# 	ac_entry.account_number = ac[1]
	# 	ac_entry.parent = parent_account
	# 	ac_entry.parent_account = parent_account
	# 	ac_entry.account_currency = 'IDR'
	# 	ac_entry.account_type = 'Cash'
	# 	ac_entry.save()