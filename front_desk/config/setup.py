from __future__ import print_function, unicode_literals
from frappe import _
import frappe
from frappe.desk.page.setup_wizard.setup_wizard import make_records


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
	records = [
		# Room Availability
		{'doctype': 'Room Availability', 'name':_('AV'), 'description': _('Available')},
		{'doctype': 'Room Availability', 'name':_('RS'), 'description': _('Room Sold')},
		{'doctype': 'Room Availability', 'name':_('RC'), 'description': _('Room Compliment')},
		{'doctype': 'Room Availability', 'name':_('HU'), 'description': _('House Use')},
		{'doctype': 'Room Availability', 'name':_('OO'), 'description': _('Out of Order')},
		{'doctype': 'Room Availability', 'name':_('OU'), 'description': _('Office Use')},
		{'doctype': 'Room Availability', 'name':_('UC'), 'description': _('Under Construction')},
	]
	make_records(records, True)
