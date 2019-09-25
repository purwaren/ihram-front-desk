// Copyright (c) 2019, PMM and contributors
// For license information, please see license.txt

var initial_room_stay = null;

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

		frm.refresh_field('room_stay');
	}
})
