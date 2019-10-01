# -*- coding: utf-8 -*-
# Copyright (c) 2019, PMM and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from front_desk.front_desk.doctype.hotel_tax.hotel_tax import calculate_hotel_tax_and_charges

class RoomRate(Document):
	pass

def calculate_total_amount(doc, method):
	total_rate_weekday = 0.0
	total_rate_weekend = 0.0

	# calculate weekday rate
	for item in doc.get('room_rate_breakdown'):
		sub_total = float(item.breakdown_qty) * float(item.breakdown_amount)
		if item.breakdown_name != 'Weekend Rate':
			total_rate_weekday = total_rate_weekday + sub_total

	# calculate weekend rate
	for item in doc.get('room_rate_breakdown'):
		sub_total = float(item.breakdown_qty) * float(item.breakdown_amount)
		if item.breakdown_name != 'Weekday Rate':
			total_rate_weekend = total_rate_weekend + sub_total

	doc.rate_weekday = total_rate_weekday
	doc.rate_weekend = total_rate_weekend

def populate_breakdown_summary(doc,method):
	summary = ""
	breakdown_list = doc.get('room_rate_breakdown')
	for index, item in enumerate(breakdown_list):
		if item.breakdown_name == 'Weekend Rate' or item.breakdown_name == 'Weekday Rate':
			summary = summary + str(index+1) + ". " + item.breakdown_name + ' : Rp.' + item.get_formatted("breakdown_amount") + " per night\n"
		else:
			summary = summary + str(index+1) + ". " + item.breakdown_qty + " " + item.breakdown_name + ' : Rp. ' + item.get_formatted("breakdown_amount") + " per pax\n"

	doc.breakdown_summary = summary

def get_rate_after_tax(room_rate_id, selector, discount):
	room_rate = frappe.get_doc('Room Rate', room_rate_id)
	breakdown_list = room_rate.get('room_rate_breakdown')
	total_weekday = 0.0
	total_weekend = 0.0
	amount_multiplier = 1 - float(discount)/100.0

	if selector == "Weekday Rate":
		for bd_item in breakdown_list:
			if bd_item.breakdown_name != 'Weekend Rate':
				_,_,tb_total = calculate_hotel_tax_and_charges(amount_multiplier * bd_item.breakdown_amount * float(bd_item.breakdown_qty), bd_item.breakdown_tax)
				total_weekday = total_weekday + tb_total[-1]

		return total_weekday

	if selector == "Weekend Rate":
		for bd_item in breakdown_list:
			if bd_item.breakdown_name != 'Weekday Rate':
				_,_,tb_total = calculate_hotel_tax_and_charges(amount_multiplier * bd_item.breakdown_amount * float(bd_item.breakdown_qty), bd_item.breakdown_tax)
				total_weekend = total_weekend + tb_total[-1]

		return total_weekend
