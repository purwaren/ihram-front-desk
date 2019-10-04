// Copyright (c) 2019, PMM and contributors
// For license information, please see license.txt

var doc = undefined;

frappe.ui.form.on('Room Availability Page', {
	search_button: function(frm, cdt, cdn) {
		doc = locals[cdt][cdn];
		search(doc);
	}
});

function search(doc) {
	if (doc.start != undefined && doc.end != undefined) {
		var wrapper = cur_frm.get_field('html').$wrapper;
		
		var html =	'<div id="room-calendar">\
						<table class="form-grid" id="table-calendar">\
							<tr class="grid-heading-row" id="table-calendar-title">\
								<th class="grid-static-col">Room Number</th>\
								<th class="grid-static-col">Room Type</th>\
								<th class="grid-static-col">Bed Type</th>\
								<th class="grid-static-col">Smoking</th>\
								<th class="grid-static-col">Room View</th>\
								<th class="grid-static-col">Room Status</th>\
							</tr>\
						</table>\
					</div>';
		
		var css = 	'<style>\
						#room-calendar {\
							font-size:12px;\
							height:300px;\
							overflow-y:scroll;\
						}\
					</style>';

		wrapper.html(html+css);
		
		var start = new Date(doc.start);
		var	end = new Date(doc.end);

		if (start > end) {
			frappe.msgprint(__("Start > End")); return;
		}

		while (start <= end) {
			var th = document.createElement('th');
			th.className = 'grid-static-col';
			th.innerHTML = formatDate(start);
			document.getElementById('table-calendar-title').appendChild(th);
		
			start.setDate(start.getDate() + 1);
		}

		frappe.call({
			method: 'front_desk.front_desk.doctype.hotel_room.hotel_room.get_all_hotel_room',
			callback: (resp) => {
				resp.message.forEach(elm => {
					var tr = document.createElement('tr');
					tr.className = 'grid-row';
					
					var td = document.createElement('td');
					td.className = 'grid-static-col';
					td.innerHTML = elm.name;
					tr.appendChild(td);

					var td = document.createElement('td');
					td.className = 'grid-static-col';
					td.innerHTML = elm.room_type;
					tr.appendChild(td);

					var td = document.createElement('td');
					td.className = 'grid-static-col';
					td.innerHTML = elm.bed_type;
					tr.appendChild(td);

					var td = document.createElement('td');
					td.className = 'grid-static-col';
					td.innerHTML = elm.allow_smoke;
					tr.appendChild(td);

					var td = document.createElement('td');
					td.className = 'grid-static-col';
					td.innerHTML = elm.view;
					tr.appendChild(td);

					var td = document.createElement('td');
					td.className = 'grid-static-col';
					td.innerHTML = elm.room_status;
					tr.appendChild(td);

					var start = new Date(doc.start);
					var	end = new Date(doc.end);
					
					var loop = function(start, end) {
						get_availability(start, function(){
							start.setDate(start.getDate() + 1);
							if (start <= end) {
								loop(start, end);
							}
						})
					}

					function get_availability(date, fun) {
						var dateCopied = new Date(date);
						dateCopied = formatDate(dateCopied);

						frappe.call({
							method: 'front_desk.front_desk.doctype.room_availability_page.room_availability_page.get_room_availability',
							args: {
								room_id: elm.name,
								date: formatDate(date)
							},
							callback: (resp) => {
								var td = document.createElement('td');
								td.className = 'grid-static-col';
								td.innerHTML = resp.message;
								td.ondblclick = function() {
									book_dialog(elm.name, dateCopied, resp.message);
								}
								tr.appendChild(td);

								fun();
							}
						});
					}

					loop(start, end);

					document.getElementById('table-calendar').appendChild(tr);
				});
			}
		});

	} else {
		console.log('...');
	}
}

function formatDate(date) {
    var d = new Date(date),
        month = '' + (d.getMonth() + 1),
        day = '' + d.getDate(),
        year = d.getFullYear();

    if (month.length < 2) 
        month = '0' + month;
    if (day.length < 2) 
        day = '0' + day;

    return [year, month, day].join('-');
}

var dialog = undefined;

function book_dialog(room_id, date, current_status) {
	if (current_status != 'RS') {
		if (current_status == '') {
			dialog = new frappe.ui.Dialog({
				'title': 'Book Room ' + room_id,
				'fields': [
					{'label': 'Start', 'fieldname': 'start', 'fieldtype': 'Date', 'default': date},
					{'label': 'End', 'fieldname': 'end', 'fieldtype': 'Date', 'default': date},
					{'label': 'Availability', 'fieldname': 'availability', 'fieldtype': 'Select', 'options': ['OU', 'HU', 'OO', 'UC']},
					{'label': 'Description', 'fieldname': 'description', 'fieldtype': 'Small Text'}
				],
				primary_action: function() {
					var form = dialog.get_values();
					if (form.start == undefined) {
						frappe.msgprint(__('Choose start')); return;
					} else if (form.end == undefined) {
						frappe.msgprint(__('Choose end')); return;
					} else if (form.end <= form.start) {
						frappe.msgprint(__('Conflict: End cannot be the same or less than start')); return;
					} else if (form.availability == undefined) {
						frappe.msgprint(__('Choose availability')); return;
					} else {
						process_booking(room_id, form, 'new', '');
					}
				}
			});
			dialog.show();
		} else {
			frappe.call({
				method: 'front_desk.front_desk.doctype.room_booking.room_booking.get_room_booking',
				args: {
					room_id: room_id,
					date: date
				},
				callback: (resp) => {
					dialog = new frappe.ui.Dialog({
						'title': 'Book Room ' + room_id,
						'fields': [
							{'label': 'Start', 'fieldname': 'start', 'fieldtype': 'Date', 'default': resp.message[0][1]},
							{'label': 'End', 'fieldname': 'end', 'fieldtype': 'Date', 'default': resp.message[0][2]},
							{'label': 'Availability', 'fieldname': 'availability', 'fieldtype': 'Select', 'options': ['OU', 'HU', 'OO', 'UC'], 'default': resp.message[0][3]},
							{'label': 'Description', 'fieldname': 'description', 'fieldtype': 'Small Text', 'default': resp.message[0][4]},
							{'label': __('Cancel Booking'), 'fieldname': 'cancel_booking', 'fieldtype': 'Button'}
						],
						primary_action: function() {
							var form = dialog.get_values();
							if (form.start == undefined) {
								frappe.msgprint(__('Choose start')); return;
							} else if (form.end == undefined) {
								frappe.msgprint(__('Choose end')); return;
							} else if (form.end <= form.start) {
								frappe.msgprint(__('Conflict: End cannot be the same or less than start')); return;
							} else if (form.availability == undefined) {
								frappe.msgprint(__('Choose availability')); return;
							} else {
								process_booking(room_id, form, 'update', resp.message[0][0]);
							}
						}
					});
					dialog.fields_dict['cancel_booking'].input.onclick = function() {
						frappe.db.set_value('Room Booking', resp.message[0][0], {
							status: 'Canceled'
						}).then(r => {
							search(doc);
							dialog.hide();
							frappe.msgprint(__('Success cancel book room ' + room_id));
						})
					}
					dialog.show();
				}
			});
		}
	}
}

function process_booking(room_id, form, flag, name) {
	frappe.call({
		method: 'front_desk.front_desk.doctype.room_booking.room_booking.is_available',
		args: {
			room_id: room_id,
			start: form.start,
			end: form.end,
			name: name
		},
		callback: (resp) => {
			if (resp.message == true) {
				if (flag == 'new') {
					frappe.db.insert({
						doctype: 'Room Booking',
						status: 'Booked',
						room_id: room_id,
						start: form.start,
						end: form.end,
						room_availability: form.availability,
						note: form.description
					}).then(r => {
						search(doc);
						dialog.hide();
						frappe.msgprint(__('Success book room ' + room_id + ' from ' + form.start + ' until ' + form.end));
					})
				} else if (flag == 'update') {
					frappe.db.set_value('Room Booking', name, {
						start: form.start,
						end: form.end,
						room_availability: form.availability,
						note: form.description
					}).then(r => {
						search(doc);
						dialog.hide();
						frappe.msgprint(__('Success book room ' + room_id + ' from ' + form.start + ' until ' + form.end));
					})
				}
			} else {
				frappe.msgprint(__('Conflict date')); return;
			}
		}
	});
}

