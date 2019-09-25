# -*- coding: utf-8 -*-
# Copyright (c) 2019, PMM and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import front_desk.front_desk.doctype.room_stay.room_stay as room_stay

class MoveRoom(Document):
	pass

@frappe.whitelist()
def get_move_room_name_by_initial_room_stay(initial_room_stay):
	return frappe.db.get_value('Move Room', {'initial_room_stay':initial_room_stay}, ['name'])

@frappe.whitelist()
def set_replacement_room_stay_by_name(name):
	replacement_room_stay = room_stay.get_room_stay_name_by_parent(name, 'room_stay', 'Move Room')
	frappe.db.set_value('Move Room', name, 'replacement_room_stay', replacement_room_stay)