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
		frm.refresh_field('room_stay');
	},
	after_save: function(frm) {
		frappe.call({
			method: 'front_desk.front_desk.doctype.move_room.move_room.process_move_room',
			args: {
				initial_room_stay_name: initial_room_stay.name
			}
		});
	}
});

frappe.ui.form.on('Room Stay', {
	form_render: function(frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		child.reservation_id = initial_room_stay.reservation_id;
		child.guest_name = initial_room_stay.guest_name;

		var	grid_row = frm.fields_dict['room_stay'].grid.grid_rows_by_docname[child.name];
		frappe.utils.filter_dict(grid_row.docfields, {fieldname: "reservation_id"})[0].hidden = 1;
		frappe.utils.filter_dict(grid_row.docfields, {fieldname: "is_early_checkin"})[0].hidden = 1;
		frappe.utils.filter_dict(grid_row.docfields, {fieldname: "is_late_checkout"})[0].hidden = 1;
		frappe.utils.filter_dict(grid_row.docfields, {fieldname: "section_break_1"})[0].hidden = 1;

		child.room_bill_paid_id = initial_room_stay.room_bill_paid_id;

		console.log(child);
		if (guest_request == 0) {
			child.room_rate = initial_room_stay.room_rate;
			child.override_rate = initial_room_stay.override_rate;
			child.weekday_rate = initial_room_stay.weekday_rate;
			child.actual_weekday_rate = initial_room_stay.actual_weekday_rate;
			child.weekend_rate = initial_room_stay.weekend_rate;
			child.actual_weekend_rate = initial_room_stay.actual_weekend_rate;
			frappe.utils.filter_dict(grid_row.docfields, {fieldname: "room_rate"})[0].read_only = 1;
			frappe.utils.filter_dict(grid_row.docfields, {fieldname: "override_rate"})[0].read_only = 1;
			frappe.utils.filter_dict(grid_row.docfields, {fieldname: "actual_weekday_rate"})[0].read_only = 1;
			frappe.utils.filter_dict(grid_row.docfields, {fieldname: "actual_weekend_rate"})[0].read_only = 1;

		} else {
			child.room_rate = undefined;
			child.override_rate = 0;
			child.weekday_rate = undefined;
			child.actual_weekday_rate = 0;
			child.weekend_rate = undefined;
			child.actual_weekend_rate = 0;
			frappe.utils.filter_dict(grid_row.docfields, {fieldname: "room_rate"})[0].read_only = 0;
			frappe.utils.filter_dict(grid_row.docfields, {fieldname: "override_rate"})[0].read_only = 0;
			frappe.utils.filter_dict(grid_row.docfields, {fieldname: "actual_weekday_rate"})[0].read_only = 0;
			frappe.utils.filter_dict(grid_row.docfields, {fieldname: "actual_weekend_rate"})[0].read_only = 0;
			frappe.utils.filter_dict(grid_row.docfields, {fieldname: "total_bill_amount"})[0].hidden = 0;
		}

		frm.refresh_field('room_stay');

		get_available('room_type', 'room_stay', child);
		get_available('bed_type', 'room_stay', child);
		get_available('room_id', 'room_stay', child);

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

		get_available('room_type', 'room_stay', child);
		get_available('bed_type', 'room_stay', child);
		get_available('room_id', 'room_stay', child);

		if (guest_request == 1) {
			get_room_rate(child);
		}
		else if (guest_request == 0) {
			// recalculate room stay bill
			if ( child.arrival != undefined && child.departure != undefined && child.room_rate != undefined) {
				frappe.call({
					method: 'front_desk.front_desk.doctype.room_stay.room_stay.calculate_room_stay_bill',
					args: {
						arrival: child.arrival,
						departure: child.departure,
						room_rate_id: child.room_rate,
						discount: child.discount_percentage,
						actual_weekday: child.actual_weekday_rate,
						actual_weekend: child.actual_weekend_rate,
					},
					callback: (response) => {
						child.total_bill_amount = response.message;
						frm.refresh_field('room_stay');
					}
				});
			}
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

		get_available('room_type', 'room_stay', child);
		get_available('bed_type', 'room_stay', child);
		get_available('room_id', 'room_stay', child);

		if (guest_request == 1) {
			get_room_rate(child);
		}
		else if (guest_request == 0) {
			// recalculate room stay bill
			if ( child.arrival != undefined && child.departure != undefined && child.room_rate != undefined) {
				frappe.call({
					method: 'front_desk.front_desk.doctype.room_stay.room_stay.calculate_room_stay_bill',
					args: {
						arrival: child.arrival,
						departure: child.departure,
						room_rate_id: child.room_rate,
						discount: child.discount_percentage,
						actual_weekday: child.actual_weekday_rate,
						actual_weekend: child.actual_weekend_rate,
					},
					callback: (response) => {
						child.total_bill_amount = response.message;
						frm.refresh_field('room_stay');
					}
				});
			}
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

		get_available('room_type', 'room_stay', child);
		get_available('bed_type', 'room_stay', child);
		get_available('room_id', 'room_stay', child);

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

		get_available('bed_type', 'room_stay', child);
		get_available('room_id', 'room_stay', child);

		if (guest_request == 1) {
			get_room_rate(child);
		}
	},
	bed_type: function(frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		child.room_id = undefined;

		frm.refresh_field('room_stay');

		get_available('room_id', 'room_stay', child);
	},
	room_id: function(frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		
		if (child.room_id != undefined) {
			frappe.db.get_value('Hotel Room', {'name': child.room_id}, ['room_type', 'bed_type', 'allow_smoke'], function(response) {
				child.allow_smoke = response.allow_smoke;
				child.room_type = response.room_type;
				child.bed_type = response.bed_type;

				if (guest_request == 1) {
					child.room_rate = undefined;
				}

				frm.refresh_field('room_stay');

				get_available('room_type', 'room_stay', child);
				get_available('bed_type', 'room_stay', child);
				get_available('room_id', 'room_stay', child);

				if (guest_request == 1) {
					get_room_rate(child);
				}
			});
		}
		else {
			get_available('room_id', 'room_stay', child);
		}
	},
	discount_percentage: function(frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		// recalculate room stay bill
		if (child.arrival != undefined && child.departure != undefined && child.room_rate != undefined) {
			frappe.call({
				method: 'front_desk.front_desk.doctype.room_stay.room_stay.calculate_room_stay_bill',
				args: {
					arrival: child.arrival,
					departure: child.departure,
					room_rate_id: child.room_rate,
					discount: child.discount_percentage,
					actual_weekday: child.actual_weekday_rate,
					actual_weekend: child.actual_weekend_rate,
				},
				callback: (response) => {
					child.total_bill_amount = response.message;
					frm.refresh_field('room_stay');
				}
			});
		}
	},
	room_rate: function(frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		// recalculate room stay bill
		if (child.arrival != undefined && child.departure != undefined && child.room_rate != undefined) {
			frappe.call({
				method: 'front_desk.front_desk.doctype.room_stay.room_stay.calculate_room_stay_bill',
				args: {
					arrival: child.arrival,
					departure: child.departure,
					room_rate_id: child.room_rate,
					discount: child.discount_percentage,
					actual_weekday: child.actual_weekday_rate,
					actual_weekend: child.actual_weekend_rate,
				},
				callback: (response) => {
					child.total_bill_amount = response.message;
					frm.refresh_field('room_stay');
				}
			});
		}
	},
	actual_weekday_rate: function(frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		if (child.actual_weekday_rate == undefined) {
			child.actual_weekday_rate = 0;
			frm.refresh_field('room_stay');
		}
		// recalculate room stay bill
		if (child.arrival != undefined && child.departure != undefined && child.room_rate != undefined) {
			frappe.call({
				method: 'front_desk.front_desk.doctype.room_stay.room_stay.calculate_room_stay_bill',
				args: {
					arrival: child.arrival,
					departure: child.departure,
					room_rate_id: child.room_rate,
					discount: child.discount_percentage,
					actual_weekday: child.actual_weekday_rate,
					actual_weekend: child.actual_weekend_rate,
				},
				callback: (response) => {
					child.total_bill_amount = response.message;
					frm.refresh_field('room_stay');
				}
			});
		}
	},
	actual_weekend_rate: function(frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		if (child.actual_weekend_rate == undefined) {
			child.actual_weekend_rate = 0;
			frm.refresh_field('room_stay');
		}
		// recalculate room stay bill
		if (child.arrival != undefined && child.departure != undefined && child.room_rate != undefined) {
			frappe.call({
				method: 'front_desk.front_desk.doctype.room_stay.room_stay.calculate_room_stay_bill',
				args: {
					arrival: child.arrival,
					departure: child.departure,
					room_rate_id: child.room_rate,
					discount: child.discount_percentage,
					actual_weekday: child.actual_weekday_rate,
					actual_weekend: child.actual_weekend_rate,
				},
				callback: (response) => {
					child.total_bill_amount = response.message;
					frm.refresh_field('room_stay');
				}
			});
		}
	},
	override_rate: function (frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		if (child.override_rate == 0) {
			child.actual_weekday_rate = 0;
			child.actual_weekend_rate = 0;
		}
		// recalculate room stay bill
		if (child.arrival != undefined && child.departure != undefined && child.room_rate != undefined) {
			frappe.call({
				method: 'front_desk.front_desk.doctype.room_stay.room_stay.calculate_room_stay_bill',
				args: {
					arrival: child.arrival,
					departure: child.departure,
					room_rate_id: child.room_rate,
					discount: child.discount_percentage,
					actual_weekday: child.actual_weekday_rate,
					actual_weekend: child.actual_weekend_rate,
				},
				callback: (response) => {
					child.total_bill_amount = response.message;
					frm.refresh_field('room_stay');
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

function get_available(child_field, doc_field, child) {
	var field = cur_frm.fields_dict[doc_field].grid.fields_map[child_field];

	var start = undefined;
	var end = undefined;

	if (doc_field == 'reservation_detail') {
		if (child.expected_arrival != undefined && child.expected_departure != undefined){
			start = child.expected_arrival;
			end = child.expected_departure;
		}
	} else if (doc_field == 'room_stay') {
		if (child.arrival != undefined && child.departure != undefined) {
			start = formatDate(child.arrival);
			end = formatDate(child.departure);
		}
	}

	var query = '';

	if (child_field == 'room_id') {
		query = 'front_desk.front_desk.doctype.room_booking.room_booking.get_room_available';
	} else if (child_field == 'room_type') {
		query = 'front_desk.front_desk.doctype.room_booking.room_booking.get_room_type_available';
	} else if (child_field == 'bed_type') {
		query = 'front_desk.front_desk.doctype.room_booking.room_booking.get_bed_type_available';
	}

	field.get_query = function () {
		return {
			query: query,
			filters: {
				'start': start,
				'end': end,
				'parent': initial_room_stay.reservation_id,
				'allow_smoke': child.allow_smoke,
				'room_type': child.room_type,
				'bed_type': child.bed_type,
				'doc_field': doc_field
			}
		}
	}
}
function get_room_rate(child) {
	var start_date = child.arrival;
	var	grid_row = cur_frm.fields_dict['room_stay'].grid.grid_rows_by_docname[child.name];
	var field = frappe.utils.filter_dict(grid_row.docfields, {fieldname: "room_rate"})[0];

	if (child.room_type != undefined) {
		frappe.db.get_value('Reservation', initial_room_stay.reservation_id, 'customer_id', (reservation) => {
			frappe.db.get_value("Customer", reservation.customer_id, "customer_group", (customer) => {
				let customer_group_list = ['All Customer Groups'];
				customer_group_list.push(customer.customer_group);
				field.get_query = function () {
					return {
						filters: [
						['Room Rate', 'room_type', '=', child.room_type],
						['Room Rate', 'is_disabled', '=', 0],
						['Room Rate', 'customer_group', 'in', customer_group_list],
						['Room Rate', 'from_date', '<=', start_date],
						['Room Rate', 'to_date', '>=', start_date],
					]
					}
				}
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