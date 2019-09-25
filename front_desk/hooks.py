# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "front_desk"
app_title = "Front Desk"
app_publisher = "PMM"
app_description = "IHRAM - Front Desk Module"
app_icon = "octicon octicon-file-directory"
app_color = "blue"
app_email = "support@ihram.io"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/front_desk/css/front_desk.css"
# app_include_js = "/assets/front_desk/js/front_desk.js"

# include js, css files in header of web template
# web_include_css = "/assets/front_desk/css/front_desk.css"
# web_include_js = "/assets/front_desk/js/front_desk.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "front_desk.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "front_desk.install.before_install"
after_install = "front_desk.config.setup.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "front_desk.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	# "*": {
	# 	"on_update": "method",
	# 	"on_cancel": "method",
	# 	"on_trash": "method"
	# }
	"Room Rate": {
		"validate": ["front_desk.front_desk.doctype.room_rate.room_rate.calculate_total_amount",
					 "front_desk.front_desk.doctype.room_rate.room_rate.populate_breakdown_summary"],
	},
	"Reservation": {
		"validate": "front_desk.front_desk.doctype.reservation.reservation.add_special_charge"
	},
	"Hotel Tax": {
		"validate": "front_desk.front_desk.doctype.hotel_tax.hotel_tax.autofill_hotel_tax_value"
	},
	"Hotel Bill": {
		"validate": "front_desk.front_desk.doctype.hotel_bill.hotel_bill.calculate_bill_total"
	},
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	# "all": [
	# 	"front_desk.tasks.all"
	# ],
	"daily": [
		"front_desk.front_desk.doctype.hotel_room.hotel_room.set_hotel_room_vacant_dirty",
		"front_desk.front_desk.doctype.folio.folio.copy_all_trx_from_sales_invoice_to_folio",
	],
	# "hourly": [
	# 	"front_desk.tasks.hourly"
	# ],
	# "weekly": [
	# 	"front_desk.tasks.weekly"
	# ]
	# "monthly": [
	# 	"front_desk.tasks.monthly"
	# ]
	"cron": {
		"59 23 * * *": [
			"front_desk.front_desk.doctype.reservation.reservation.auto_room_charge",
		],
		"0 18 * * *":[
			"front_desk.front_desk.doctype.reservation.reservation.auto_release_reservation_at_six_pm",
		]
	}
}

# Testing
# -------

# before_tests = "front_desk.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "front_desk.event.get_events"
# }

