# -*- coding: utf-8 -*-
# Copyright (c) 2019, PMM and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import json
import frappe
from frappe.model.document import Document

class Folio(Document):
	pass

def create_folio(reservation_id_list):
	reservation_id_list = json.loads(reservation_id_list)
