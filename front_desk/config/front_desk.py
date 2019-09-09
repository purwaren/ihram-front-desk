from __future__ import unicode_literals
from frappe import _


def get_data():
	config = [
		{
			"label": _("Report"),
			"items": [
				{
					"label": _("Reservation"),
					"type": "doctype",
					"name": "Reservation",
					"description": _("List of reservation.")
				},
				{
					"label": _("Folio Transaction"),
					"type": "doctype",
					"name": "Hotel Room",
					"description": _("List guest transaction.")
				},
			]
		},
		{
			"label": _("Setup"),
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
		},
		{
			"label": _("Help"),
			"items": [
				{
					"label": _("How to create reservation ?"),
					"type": "doctype",
					"name": "Hotel Room",
					"description": _("Manual for creating reservation.")
				},
				{
					"label": _("How to issue card ?"),
					"type": "doctype",
					"name": "Hotel Room",
					"description": _("Manual for card issuing.")
				},
				{
					"label": _("I need support assistance"),
					"type": "doctype",
					"name": "Hotel Room",
					"description": _("Directly contact support assistance / IT Department.")
				},
			]
		}
	]
	return config
