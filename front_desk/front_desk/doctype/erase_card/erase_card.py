# -*- coding: utf-8 -*-
# Copyright (c) 2020, PMM and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import requests
import datetime
from frappe.model.document import Document

class EraseCard(Document):
	pass

@frappe.whitelist()
def issue_card_check_in(pcId, cmd, technology, cardOperation, encoder, room, activationDate, activationTime, expiryDate,
				  expiryTime, grant, keypad, operator, track1, track2, room2, room3, room4, returnCardId, cardId):

	# Example Post
	# {"pcId": "1", "cmd": "PI", "room": "102", "activationDate": "16/05/2017",
	#  "activationTime": "12:00", "expiryDate": "17/05/2017", "expiryTime": "12:00",
	#  "cardOperation": "RP", "operator": "tesa"}

	# api-endpoint
	url = 'http://tesa-server-url-change-here'

	# defining a params dict for the parameters to be sent to the API
	params = {
		'pcId': pcId,
		'cmd': cmd,
		'technology': technology,
		'cardOperation': cardOperation,
		'encoder': encoder,
		'room': room,
		'activationDate': activationDate,
		'activationTime': activationTime,
		'expiryDate': expiryDate,
		'expiryTime': expiryTime,
		'grant': grant,
		'keypad': keypad,
		'operator': operator,
		'track1': track1,
		'track2': track2,
		'room2': room2,
		'room3': room3,
		'room4': room4,
		'returnCardId': returnCardId,
		'cardId': cardId
	}

	r = requests.post(url=url, params=params)
