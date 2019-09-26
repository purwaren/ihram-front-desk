// Copyright (c) 2019, PMM and contributors
// For license information, please see license.txt

var reservation = null;
var has_deposit = false;
var room_list = [];
var reservation_detail_remove_list = [];
var is_remove_reservation_detail = false;
var is_remove_room_stay = false;

frappe.ui.form.on('Reservation', {
	onload: function(frm, cdt, cdn) {
		frm.set_query('payment_method', () => {
			return {
				query: 'front_desk.front_desk.doctype.reservation.reservation.get_debit_account'
			}
		});
	},
	onload_post_render: function(frm, cdt, cdn) {
		$('*[data-fieldname="reservation_detail"]').find('.grid-remove-rows').hide();
		$('*[data-fieldname="room_stay"]').find('.grid-remove-rows').hide();

		reservation = frappe.get_doc(cdt, cdn);

		if (reservation.__islocal == 1) {
			frm.set_df_property('wifi_password', 'hidden', 1);
		} else {
			reservation.room_stay.forEach(element => {
				room_list.push(element.room_id);
			});
		}

		if (reservation.deposit > 0) {
			has_deposit = true;
		}

		if (has_deposit) {
			frm.set_df_property('deposit', 'set_only_once', 1);
			frm.set_df_property('payment_method', 'set_only_once', 1);
		}

		if(reservation.status == 'Created') {
			frm.page.add_menu_item(("Cancel"), function () {
				frappe.confirm(
                (("You are about to cancel Reservation ") + reservation.name + (", are you sure?")),
                () => {
                    frappe.call({
                        method: "front_desk.front_desk.doctype.reservation.reservation.cancel_reservation",
                        args: {
                            reservation_id: reservation.name
                        }
                    });
                    frappe.msgprint(("Reservation ") + reservation.name + (" Canceled"));
                	}
            	);
			});
		}

		if (reservation.status == 'In House') {
			frm.page.add_menu_item(("Check Out"), function () {
				frappe.call({
					method: "front_desk.front_desk.doctype.reservation.reservation.checkout_reservation",
					args: {
						reservation_id: reservation.name
					}
				});
			});
		}
		
		if (reservation.status != 'Cancel' && reservation.status != 'Created') {
			// frm.add_custom_button(__("Trigger Auto Charges"), function () {
			// 	frappe.call({
			// 		method: "front_desk.front_desk.doctype.reservation.reservation.create_room_charge",
			// 		args: {
			// 			reservation_id: reservation.name
			// 		}
			// 	});
			// 	frappe.call({
			// 		method: "front_desk.front_desk.doctype.folio.folio.copy_all_trx_from_sales_invoice_to_folio",
			// 	});
			// });

			frm.add_custom_button(__("Billing"), function () {
				frappe.call({
					method: "front_desk.front_desk.doctype.reservation.reservation.get_hotel_bill_url",
					args: {
						reservation_id: reservation.name
					},
					callback: (r) => {
						if (r.message) {
							var w = window.open(r.message, "_blank");
                        	if (!w) {
                            	frappe.msgprint(__("Please enable pop-ups")); return;
                        	}
						}
					}
				});
			});

			frm.add_custom_button(__("Print Receipt"), function() {
    			frappe.call({
					method: "frappe.client.get_value",
					args: {
						doctype: "Folio",
						filters: {"reservation_id": reservation.name},
						fieldname: "name"
					},
					callback: (r) => {
						if (r.message.name) {
							var w = window.open(frappe.urllib.get_full_url("/printview?"
									+"doctype="+encodeURIComponent("Folio")
									+"&name="+encodeURIComponent(r.message.name)
									+"&trigger_print=1"
									+"&no_letterhead=0"
									))

							if (!w) {
								frappe.msgprint(__("Please enable pop-ups")); return;
							}
						}
					}
				});
			});

			frm.add_custom_button(__("Show Folio"), function() {
    			frappe.call({
					method: "front_desk.front_desk.doctype.reservation.reservation.get_folio_url",
					args: {
						reservation_id: reservation.name
					},
					callback: (r) => {
						if (r.message) {
							var w = window.open(r.message, "_blank");
                        	if (!w) {
                            	frappe.msgprint(__("Please enable pop-ups")); return;
                        	}
						}
					}
				});
			});
		}

		if (reservation.status == 'Cancel' || reservation.status == 'Created') {
			frm.set_df_property('deposit', 'hidden', 1);
			frm.set_df_property('payment_method', 'hidden', 1);
			frm.set_df_property('room_stay_section', 'hidden', 1);
			frm.set_df_property('room_stay', 'hidden', 1);
		}

		if (reservation.status != 'Confirmed' && reservation.status != 'In House') {
			frm.set_df_property('room_stay', 'set_only_once', 1);

			frappe.meta.get_docfield('Room Stay', 'room_id', reservation.name).read_only = 1;
			frappe.meta.get_docfield('Room Stay', 'issue_card', reservation.name).hidden = 1;
		}

		if (reservation.status == 'Cancel' || reservation.status == 'Finish') {
			frm.set_df_property('reservation_detail', 'set_only_once', 1);
		}
	},
	before_save: function(frm, cdt, cdn) {
		if (reservation.__islocal == 1) {
			frm.set_value('wifi_password', make_pin(6));
			frm.set_df_property('wifi_password', 'hidden', 0);
		} else {
			frappe.call({
				method: 'front_desk.front_desk.doctype.hotel_room.hotel_room.set_availability_and_room_status',
				args: {
					room_name_list: room_list,
					availability: (reservation.status == 'Confirmed') ? 'AV' : 'OO',
					room_status: (reservation.status == 'Confirmed') ? 'Vacant Ready' : 'Occupied Dirty'
				},
				callback: (response) => {
					room_list = [];
					reservation.room_stay.forEach(element => {
						room_list.push(element.room_id);
					});
	
					frappe.call({
						method: 'front_desk.front_desk.doctype.hotel_room.hotel_room.set_availability_and_room_status',
						args: {
							room_name_list: room_list,
							availability: 'RS',
							room_status: 'Occupied Clean'
						}
					});
				}
			});

			if (!has_deposit && reservation.deposit > 0) {
				frappe.call({
					method: 'front_desk.front_desk.doctype.reservation.reservation.create_deposit_journal_entry',
					args: {
						reservation_id: reservation.name,
						amount: reservation.deposit,
						debit_account_name: reservation.payment_method
					}
				});
			}
		}
	},
	after_save: function(frm, cdt, cdn) {
		frappe.call({
			method: "front_desk.front_desk.doctype.room_booking.room_booking.cancel_by_reservation",
			args: {
				reservation_detail_list: reservation_detail_remove_list 
			}
		});

		frappe.call({
			method: "front_desk.front_desk.doctype.room_booking.room_booking.update_by_reservation",
			args: {
				reservation_name: frappe.get_doc(cdt, cdn).name
			}
		});

		frm.reload_doc();
	}
});

frappe.ui.form.on('Reservation Detail', {
	form_render: function(frm, cdt, cdn) {
		is_remove_reservation_detail = false;
		var child = locals[cdt][cdn];

		if (reservation.status == 'Cancel' || reservation.status == 'Finish') {
			$(".grid-delete-row").hide()
			set_all_field_reservation_detail_read_only(true);
		} else if (reservation.room_stay != undefined) {
			reservation.room_stay.forEach(element => {
				if (child.room_id == element.room_id && child.expected_arrival < formatDate(element.departure)) {
					$(".grid-delete-row").hide()
					set_all_field_reservation_detail_read_only(true);
				}
			});
		} else {
			set_all_field_reservation_detail_read_only(false);
		}

		frm.refresh_field('reservation_detail');

		get_room_type_available('reservation_detail', child);
		get_bed_type_available('reservation_detail', child);
		get_room_available('reservation_detail', child);
		get_room_rate('reservation_detail', child);
	},
	expected_arrival: function(frm, cdt, cdn) {
		if (!is_remove_reservation_detail) {
			var child = locals[cdt][cdn];
			child.room_type = undefined;
			child.bed_type = undefined;
			child.room_id = undefined;
			child.room_rate = undefined;

			frm.refresh_field('reservation_detail');

			get_room_type_available('reservation_detail', child);
			get_bed_type_available('reservation_detail', child);
			get_room_available('reservation_detail', child);
			get_room_rate('reservation_detail', child);
		}
	},
	expected_departure: function(frm, cdt, cdn) {
		if (!is_remove_reservation_detail) {
			var child = locals[cdt][cdn];
			child.room_type = undefined;
			child.bed_type = undefined;
			child.room_id = undefined;
			child.room_rate = undefined;

			frm.refresh_field('reservation_detail');

			get_room_type_available('reservation_detail', child);
			get_bed_type_available('reservation_detail', child);
			get_room_available('reservation_detail', child);
			get_room_rate('reservation_detail', child);
		}
	},
	allow_smoke: function(frm, cdt, cdn) {
		if (!is_remove_reservation_detail) {
			var child = locals[cdt][cdn];
			child.room_type = undefined;
			child.bed_type = undefined;
			child.room_id = undefined;
			child.room_rate = undefined;

			frm.refresh_field('reservation_detail');
	
			get_room_type_available('reservation_detail', child);
			get_bed_type_available('reservation_detail', child);
			get_room_available('reservation_detail', child);
			get_room_rate('reservation_detail', child);
		}
	},
	room_type: function(frm, cdt, cdn) {
		if (!is_remove_reservation_detail) {
			var child = locals[cdt][cdn];
			child.bed_type = undefined;
			child.room_id = undefined;
			child.room_rate = undefined;

			frm.refresh_field('reservation_detail');

			get_bed_type_available('reservation_detail', child);
			get_room_available('reservation_detail', child);
			get_room_rate('reservation_detail', child);
		}
	},
	bed_type: function(frm, cdt, cdn) {
		if (!is_remove_reservation_detail) {
			var child = locals[cdt][cdn];
			child.room_id = undefined;

			frm.refresh_field('reservation_detail');
	
			get_room_available('reservation_detail', child);
		}
	},
	room_id: function(frm, cdt, cdn) {
		if (!is_remove_reservation_detail) {
			var child = locals[cdt][cdn];
			child.room_rate = undefined;
			frm.refresh_field('reservation_detail');

			if (child.room_id != undefined) {
				frappe.db.get_value('Hotel Room', {'name': child.room_id}, ['room_type', 'bed_type', 'allow_smoke'], function(response) {
					child.room_type = response.room_type;
					child.bed_type = response.bed_type;
					child.allow_smoke = response.allow_smoke

					frm.refresh_field('reservation_detail');

					get_bed_type_available('reservation_detail', child);
					get_room_available('reservation_detail', child);
					get_room_rate('reservation_detail', child);
				});
			}
		}
	},
	before_reservation_detail_remove: function(frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		if (child.__islocal != 1) {
			reservation_detail_remove_list.push(child);
		}
	},
	reservation_detail_remove: function(frm, cdt, cdn) {
		is_remove_reservation_detail = true;
	}
});

frappe.ui.form.on('Room Stay', {
	room_stay_add: function(frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		child.reservation_id = reservation.name;
		
		frm.refresh_field('room_stay');
	},
	form_render: function(frm, cdt, cdn) {
		is_remove_room_stay = false;
		var child = locals[cdt][cdn];

		if (child.__islocal == 1) {
			frappe.meta.get_docfield('Room Stay', 'section_break_1', reservation.name).hidden = true;
		} else {
			frappe.meta.get_docfield('Room Stay', 'section_break_1', reservation.name).hidden = false;
		}

		frappe.meta.get_docfield('Room Stay', 'reservation_id', reservation.name).hidden = true;
		if (reservation.status == 'Cancel' || reservation.status == 'Finish') {
			$(".grid-delete-row").hide()
			set_all_field_room_stay_read_only(true);
		} else {
			set_all_field_room_stay_read_only(false);
		}
		
		get_room_type_available('room_stay', child);
		get_bed_type_available('room_stay', child);
		get_room_available('room_stay', child);
		get_room_rate('room_stay', child);
		
		frm.refresh_field('room_stay');
	},
	arrival: function (frm, cdt, cdn) {
		if (!is_remove_room_stay) {
			var child = locals[cdt][cdn];
			child.room_type = undefined;
			child.bed_type = undefined;
			child.room_id = undefined;
			child.room_rate = undefined;
			
			frm.refresh_field('room_stay');

			get_room_type_available('room_stay', child);
			get_bed_type_available('room_stay', child);
			get_room_available('room_stay', child);
			get_room_rate('room_stay', child);
		}
	},
	departure: function (frm, cdt, cdn) {
		if (!is_remove_room_stay) {
			var child = locals[cdt][cdn];
			child.room_type = undefined;
			child.bed_type = undefined;
			child.room_id = undefined;
			child.room_rate = undefined;
			
			frm.refresh_field('room_stay');

			get_room_type_available('room_stay', child);
			get_bed_type_available('room_stay', child);
			get_room_available('room_stay', child);
			get_room_rate('room_stay', child);
		}
	},
	allow_smoke: function(frm, cdt, cdn) {
		if (!is_remove_room_stay) {
			var child = locals[cdt][cdn];
			child.room_type = undefined;
			child.bed_type = undefined;
			child.room_id = undefined;
			child.room_rate = undefined;

			frm.refresh_field('room_stay');
	
			get_room_type_available('room_stay', child);
			get_bed_type_available('room_stay', child);
			get_room_available('room_stay', child);
			get_room_rate('room_stay', child);
		}
	},
	room_type: function(frm, cdt, cdn) {
		if (!is_remove_room_stay) {
			var child = locals[cdt][cdn];
			child.bed_type = undefined;
			child.room_id = undefined;
			child.room_rate = undefined;

			frm.refresh_field('room_stay');
	
			get_bed_type_available('room_stay', child);
			get_room_available('room_stay', child);
			get_room_rate('room_stay', child);
		}
	},
	bed_type: function(frm, cdt, cdn) {
		if (!is_remove_room_stay) {
			var child = locals[cdt][cdn];
			child.room_id = undefined;

			frm.refresh_field('room_stay');
	
			get_room_available('room_stay', child);
		}
	},
	room_id: function (frm, cdt, cdn) {
		if (!is_remove_room_stay) {
			var child = locals[cdt][cdn];
			child.room_rate = undefined;
			frm.refresh_field('room_stay');

			if (child.room_id != undefined) {
				frappe.db.get_value('Hotel Room', {'name': child.room_id}, ['room_type', 'bed_type', 'allow_smoke'], function(response) {
					child.room_type = response.room_type;
					child.bed_type = response.bed_type;
					child.allow_smoke = response.allow_smoke;

					frm.refresh_field('room_stay');
	
					get_bed_type_available('room_stay', child);
					get_room_available('room_stay', child);
					get_room_rate('room_stay', child);
				});
			}
		}
	},
	issue_card: function(frm, cdt, cdn) {
		frm.set_value('status', 'In House');
		frm.save();
	},
	print_check_in_receipt: function(frm, cdt, cdn) {
		var w = window.open(frappe.urllib.get_full_url("/printview?"
			+"doctype="+encodeURIComponent("Room Stay")
			+"&name="+encodeURIComponent(frappe.get_doc(cdt, cdn).name)
			+"&no_letterhead=0"
			));

		if (!w) {
			frappe.msgprint(__("Please enable pop-ups")); return;
		}
	},
	move_room: function(frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		var w = window.open(frappe.urllib.get_full_url('/desk#Form/Move%20Room/New%20Move%20Room%201?initial_room_stay=' + child.name));
		
		if (!w) {
			frappe.msgprint(__("Please enable pop-ups")); return;
		}
	},
	room_stay_remove: function(frm, cdt, cdn) {
		is_remove_room_stay = true;
	}
});

function make_pin(length) {
	var result           = '';
	var characters       = '0123456789';
	var charactersLength = characters.length;
	for ( var i = 0; i < length; i++ ) {
	   result += characters.charAt(Math.floor(Math.random() * charactersLength));
	}
	return result;
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

function set_all_field_reservation_detail_read_only(flag) {
	frappe.meta.get_docfield('Reservation Detail', 'expected_arrival', reservation.name).read_only = flag;
	frappe.meta.get_docfield('Reservation Detail', 'expected_departure', reservation.name).read_only = flag;
	frappe.meta.get_docfield('Reservation Detail', 'adult', reservation.name).read_only = flag;
	frappe.meta.get_docfield('Reservation Detail', 'child', reservation.name).read_only = flag;
	frappe.meta.get_docfield('Reservation Detail', 'allow_smoke', reservation.name).read_only = flag;
	frappe.meta.get_docfield('Reservation Detail', 'room_type', reservation.name).read_only = flag;
	frappe.meta.get_docfield('Reservation Detail', 'bed_type', reservation.name).read_only = flag;
	frappe.meta.get_docfield('Reservation Detail', 'room_id', reservation.name).read_only = flag;
	frappe.meta.get_docfield('Reservation Detail', 'extra_bed', reservation.name).read_only = flag;
	frappe.meta.get_docfield('Reservation Detail', 'payment_type', reservation.name).read_only = flag;
	frappe.meta.get_docfield('Reservation Detail', 'room_rate', reservation.name).read_only = flag;
}

function set_all_field_room_stay_read_only(flag) {
	frappe.meta.get_docfield('Room Stay', 'is_early_checkin', reservation.name).read_only = flag;
	frappe.meta.get_docfield('Room Stay', 'early_checkin_rate', reservation.name).read_only = flag;
	frappe.meta.get_docfield('Room Stay', 'arrival', reservation.name).read_only = flag;
	frappe.meta.get_docfield('Room Stay', 'is_late_checkout', reservation.name).read_only = flag;
	frappe.meta.get_docfield('Room Stay', 'late_checkout_rate', reservation.name).read_only = flag;
	frappe.meta.get_docfield('Room Stay', 'departure', reservation.name).read_only = flag;
	frappe.meta.get_docfield('Room Stay', 'reservation_id', reservation.name).read_only = flag;
	frappe.meta.get_docfield('Room Stay', 'room_id', reservation.name).read_only = flag;
	frappe.meta.get_docfield('Room Stay', 'room_rate', reservation.name).read_only = flag;
	frappe.meta.get_docfield('Room Stay', 'issue_card', reservation.name).read_only = flag;
	frappe.meta.get_docfield('Room Stay', 'print_check_in_receipt', reservation.name).read_only = flag;
}

function get_room_available(child_field, child) {
	var	grid_row = cur_frm.fields_dict[child_field].grid.grid_rows_by_docname[child.name];
	var field = frappe.utils.filter_dict(grid_row.docfields, {fieldname: "room_id"})[0];

	var start = undefined;
	var end = undefined;

	if (child_field == 'reservation_detail') {
		if (child.expected_arrival != undefined && child.expected_departure != undefined){
			start = child.expected_arrival;
			end = child.expected_departure;
		}
	} else if (child_field == 'room_stay') {
		if (child.arrival != undefined && child.departure != undefined) {
			start = formatDate(child.arrival);
			end = formatDate(child.departure);
		}
	}

	if (child.bed_type != undefined) {
		field.get_query = function () {
			return {
				query: 'front_desk.front_desk.doctype.room_booking.room_booking.get_room_available',
				filters: {
					'start': start,
					'end': end,
					'parent': cur_frm.doc.name,
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
					'start': start,
					'end': end,
					'parent': cur_frm.doc.name,
					'allow_smoke': child.allow_smoke,
					'room_type': child.room_type,
				}
			}
		}
	} else if (start != undefined && end != undefined) {
		field.get_query = function () {
			return {
				query: 'front_desk.front_desk.doctype.room_booking.room_booking.get_room_available',
				filters: {
					'start': start,
					'end': end,
					'parent': cur_frm.doc.name,
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

function get_room_type_available(child_field, child) {
	var	grid_row = cur_frm.fields_dict[child_field].grid.grid_rows_by_docname[child.name];
	var field = frappe.utils.filter_dict(grid_row.docfields, {fieldname: "room_type"})[0];

	var start = undefined;
	var end = undefined;

	if (child_field == 'reservation_detail') {
		if (child.expected_arrival != undefined && child.expected_departure != undefined){
			start = child.expected_arrival;
			end = child.expected_departure;
		}
	} else if (child_field == 'room_stay') {
		if (child.arrival != undefined && child.departure != undefined) {
			start = formatDate(child.arrival);
			end = formatDate(child.departure);
		}
	}

	if (start != undefined && end != undefined) {
		field.get_query = function () {
			return {
				query: 'front_desk.front_desk.doctype.room_booking.room_booking.get_room_type_available',
				filters: {
					'start': start,
					'end': end,
					'parent': cur_frm.doc.name,
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

function get_bed_type_available(child_field, child) {
	var	grid_row = cur_frm.fields_dict[child_field].grid.grid_rows_by_docname[child.name];
	var field = frappe.utils.filter_dict(grid_row.docfields, {fieldname: "bed_type"})[0];

	var start = undefined;
	var end = undefined;

	if (child_field == 'reservation_detail') {
		if (child.expected_arrival != undefined && child.expected_departure != undefined){
			start = child.expected_arrival;
			end = child.expected_departure;
		}
	} else if (child_field == 'room_stay') {
		if (child.arrival != undefined && child.departure != undefined) {
			start = formatDate(child.arrival);
			end = formatDate(child.departure);
		}
	}
	
	if (child.room_type != undefined) {
		field.get_query = function () {
			return {
				query: 'front_desk.front_desk.doctype.room_booking.room_booking.get_bed_type_available',
				filters: {
					'start': start,
					'end': end,
					'parent': cur_frm.doc.name,
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

function get_room_rate(child_field, child) {
	var	grid_row = cur_frm.fields_dict[child_field].grid.grid_rows_by_docname[child.name];
	var field = frappe.utils.filter_dict(grid_row.docfields, {fieldname: "room_rate"})[0];

	if (child.room_id != undefined) {
		frappe.db.get_value("Hotel Room", child.room_id, "room_type", (hotel_room) => {
			frappe.db.get_value("Customer", cur_frm.doc.customer_id, "customer_group", (customer) => {
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
	} else {
		field.get_query = function () {
			return {
				query: 'front_desk.front_desk.doctype.room_booking.room_booking.get_empty_array'
			}
		}
	}
}