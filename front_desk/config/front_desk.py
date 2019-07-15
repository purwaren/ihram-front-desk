from __future__ import unicode_literals
from frappe import _


def get_data():
	config = [
		{
			"label": _("Transaction"),
			"items": []
		},
		{
			"label": _("Report"),
			"items": []
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
					"name": "Room Photos",
					"description": "Upload room photo"
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
			"items": []
		}
	]
	return config
