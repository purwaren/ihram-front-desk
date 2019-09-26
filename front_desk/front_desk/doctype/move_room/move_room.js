// Copyright (c) 2019, PMM and contributors
// For license information, please see license.txt

var initial_room_stay = null;
var guest_request = 0;

frappe.ui.form.on('Move Room', {
	refresh: function(frm, cdt, cdn) {
		frappe.call({
			method: 'front_desk.front_desk.doctype.room_stay.room_stay.get_room_stay_by_name',
			args: {
				name: frm.get_doc(cdt, cdn).initial_room_stay
			},
			callback: (r) => {
				initial_room_stay = r.message;
			}
		});

		var doc = locals[cdt][cdn];
		if (doc.__islocal == 1) {
			frm.set_df_property('room_stay', 'read_only', 1);
		} else {
			frm.disable_save();
			frm.set_df_property('room_stay', 'hidden', 1);
		}
	},
	guest_request: function(frm, cdt, cdn) {
		guest_request = locals[cdt][cdn].guest_request;
	},
	after_save: function(frm) {
		var move_room_name = '';

		frappe.call({
			method: 'front_desk.front_desk.doctype.move_room.move_room.get_move_room_name_by_initial_room_stay',
			args: {
				initial_room_stay: initial_room_stay.name 
			},
			callback: (r) => {
				move_room_name = r.message;

				frappe.call({
					method: 'front_desk.front_desk.doctype.move_room.move_room.set_replacement_room_stay_by_name',
					args: {
						name: move_room_name
					}
				});	

				frappe.call({
					method: 'front_desk.front_desk.doctype.room_stay.room_stay.change_parent',
					args: {
						parent_now: move_room_name,
						parentfield_now: 'room_stay',
						parenttype_now: 'Move Room',
						parent_new: initial_room_stay.reservation_id,
						parentfield_new: 'room_stay',
						parenttype_new: 'Reservation'
					}
				});	
			}
		});
	}
});

frappe.ui.form.on('Room Stay', {
	form_render: function(frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		child.reservation_id = initial_room_stay.reservation_id;

		var	grid_row = frm.fields_dict['room_stay'].grid.grid_rows_by_docname[child.name];
		var  field = frappe.utils.filter_dict(grid_row.docfields, {fieldname: "reservation_id"})[0];
		field.hidden = 1;
		var  field = frappe.utils.filter_dict(grid_row.docfields, {fieldname: "is_early_checkin"})[0];
		field.hidden = 1;
		var  field = frappe.utils.filter_dict(grid_row.docfields, {fieldname: "is_late_checkout"})[0];
		field.hidden = 1;
		var  field = frappe.utils.filter_dict(grid_row.docfields, {fieldname: "section_break_1"})[0];
		field.hidden = 1;

		if (guest_request == 0) {
			child.room_rate = initial_room_stay.room_rate;
			var  field = frappe.utils.filter_dict(grid_row.docfields, {fieldname: "room_rate"})[0];
			field.read_only = 1;
		} else {
			child.room_rate = undefined;
			var  field = frappe.utils.filter_dict(grid_row.docfields, {fieldname: "room_rate"})[0];
			field.read_only = 0;
		}

		frm.refresh_field('room_stay');

		get_room_type_available(child);
		get_bed_type_available(child);
		get_room_available(child);

		if (guest_request == 1) {
			get_room_rate(child);
		}
	},
	arrival: function(frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		child.room_type = undefined;
		child.bed_type = undefined;
		child.room_id = undefined;
		
		if (guest_request == 1) {
			child.room_rate = undefined;
		}

		frm.refresh_field('room_stay');

		get_room_type_available(child);
		get_bed_type_available(child);
		get_room_available(child);

		if (guest_request == 1) {
			get_room_rate(child);
		}
	},
	departure: function(frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		child.room_type = undefined;
		child.bed_type = undefined;
		child.room_id = undefined;
		
		if (guest_request == 1) {
			child.room_rate = undefined;
		}

		frm.refresh_field('room_stay');

		get_room_type_available(child);
		get_bed_type_available(child);
		get_room_available(child);

		if (guest_request == 1) {
			get_room_rate(child);
		}
	},
	allow_smoke: function(frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		child.room_type = undefined;
		child.bed_type = undefined;
		child.room_id = undefined;
		
		if (guest_request == 1) {
			child.room_rate = undefined;
		}

		frm.refresh_field('room_stay');

		get_room_type_available(child);
		get_bed_type_available(child);
		get_room_available(child);

		if (guest_request == 1) {
			get_room_rate(child);
		}
	},
	room_type: function(frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		child.bed_type = undefined;
		child.room_id = undefined;
		
		if (guest_request == 1) {
			child.room_rate = undefined;
		}

		frm.refresh_field('room_stay');

		get_bed_type_available(child);
		get_room_available(child);

		if (guest_request == 1) {
			get_room_rate(child);
		}
	},
	bed_type: function(frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		child.room_id = undefined;

		frm.refresh_field('room_stay');

		get_room_available(child);
	},
	room_id: function(frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		if (guest_request == 1) {
			child.room_rate = undefined;
		}
		frm.refresh_field('room_stay');
		
		if (child.room_id != undefined) {
			frappe.db.get_value('Hotel Room', {'name': child.room_id}, ['room_type', 'bed_type', 'allow_smoke'], function(response) {
				child.room_type = response.room_type;
				child.bed_type = response.bed_type;
				child.allow_smoke = response.allow_smoke;

				frm.refresh_field('room_stay');

				get_bed_type_available(child);
				get_room_available(child);

				if (guest_request == 1) {
					get_room_rate(child);
				}
			});
		}
	}
})

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

function get_room_available(child) {
	var	grid_row = cur_frm.fields_dict['room_stay'].grid.grid_rows_by_docname[child.name];
	var field = frappe.utils.filter_dict(grid_row.docfields, {fieldname: "room_id"})[0];

	if (child.bed_type != undefined) {
		field.get_query = function () {
			return {
				query: 'front_desk.front_desk.doctype.room_booking.room_booking.get_room_available',
				filters: {
					'start': formatDate(child.arrival),
					'end': formatDate(child.departure),
					'parent': initial_room_stay.reservation_id,
					'allow_smoke': child.allow_smoke,
					'room_type': child.room_type,
					'bed_type': child.bed_type
				}
			}
		}
	} else if (child.room_type != undefined) {
		field.get_query = function () {
			return {
				query: 'front_desk.front_desk.doctype.room_booking.room_booking.get_room_available',
				filters: {
					'start': formatDate(child.arrival),
					'end': formatDate(child.departure),
					'parent': initial_room_stay.reservation_id,
					'allow_smoke': child.allow_smoke,
					'room_type': child.room_type,
				}
			}
		}
	} else if (child.arrival != undefined && child.departure != undefined) {
		field.get_query = function () {
			return {
				query: 'front_desk.front_desk.doctype.room_booking.room_booking.get_room_available',
				filters: {
					'start': formatDate(child.arrival),
					'end': formatDate(child.departure),
					'parent': initial_room_stay.reservation_id,
					'allow_smoke': child.allow_smoke,
				}
			}
		}
	} else {
		field.get_query = function () {
			return {
				query: 'front_desk.front_desk.doctype.room_booking.room_booking.get_empty_array'
			}
		}
	}
}

function get_room_type_available(child) {
	var	grid_row = cur_frm.fields_dict['room_stay'].grid.grid_rows_by_docname[child.name];
	var  field = frappe.utils.filter_dict(grid_row.docfields, {fieldname: "room_type"})[0];

	if (child.arrival != undefined && child.departure != undefined) {
		field.get_query = function () {
			return {
				query: 'front_desk.front_desk.doctype.room_booking.room_booking.get_room_type_available',
				filters: {
					'start': formatDate(child.arrival),
					'end': formatDate(child.departure),
					'parent': initial_room_stay.reservation_id,
					'allow_smoke': child.allow_smoke
				}
			}
		}
	} else {
		field.get_query = function () {
			return {
				query: 'front_desk.front_desk.doctype.room_booking.room_booking.get_empty_array'
			}
		}
	}
}

function get_bed_type_available(child) {
	var	grid_row = cur_frm.fields_dict['room_stay'].grid.grid_rows_by_docname[child.name];
	var  field = frappe.utils.filter_dict(grid_row.docfields, {fieldname: "bed_type"})[0];
	
	if (child.room_type != undefined) {
		field.get_query = function () {
			return {
				query: 'front_desk.front_desk.doctype.room_booking.room_booking.get_bed_type_available',
				filters: {
					'start': formatDate(child.arrival),
					'end': formatDate(child.departure),
					'parent': initial_room_stay.reservation_id,
					'allow_smoke': child.allow_smoke,
					'room_type': child.room_type
				}
			}
		}
	} else {
		field.get_query = function () {
			return {
				query: 'front_desk.front_desk.doctype.room_booking.room_booking.get_empty_array'
			}
		}
	}
}

function get_room_rate(child) {
	var	grid_row = cur_frm.fields_dict['room_stay'].grid.grid_rows_by_docname[child.name];
	var field = frappe.utils.filter_dict(grid_row.docfields, {fieldname: "room_rate"})[0];

	if (child.room_id != undefined) {
		frappe.db.get_value('Hotel Room', child.room_id, 'room_type', (hotel_room) => {
			frappe.db.get_value('Reservation', initial_room_stay.reservation_id, 'customer_id', (reservation) => {
				frappe.db.get_value("Customer", reservation.customer_id, "customer_group", (customer) => {
					field.get_query = function () {
						return {
							filters: {
								'room_type': hotel_room.room_type
							},
							or_filters: [
								{'customer_group': 'All Customer Groups'},
								{'customer_group': customer.customer_group}
							]
						}
					}
				});
			});
		});
	} else {
		field.get_query = function () {
			return {
				query: 'front_desk.front_desk.doctype.room_booking.room_booking.get_empty_array'
			}
		}
	}
}