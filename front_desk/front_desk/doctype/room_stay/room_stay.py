# -*- coding: utf-8 -*-
# Copyright (c) 2019, PMM and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe.model.document import Document

class RoomStay(Document):
	pass

def create_room_stay(reservation_id_list):
	reservation_id_list = json.loads(reservation_id_list)

	url_list = []
	for reservation_id in reservation_id_list:
		nama = 'RS-' + reservation_id

		if not frappe.db.exists('Room Stay', nama):
			doc = frappe.new_doc('Room Stay')
			doc.nama = nama
			doc.reservation_id = reservation_id
			doc.insert()

		url_list.append(frappe.utils.get_url_to_form('Room Stay', nama))
	
	return url_list
