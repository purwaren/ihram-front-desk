from __future__ import print_function, unicode_literals

import frappe

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
