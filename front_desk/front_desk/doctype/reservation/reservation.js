// Copyright (c) 2019, PMM and contributors
// For license information, please see license.txt

var reservation = null;
var has_deposit = false;
var wrapper = null;
var debit_account_name_list = '';
var room_list = [];

frappe.ui.form.on('Reservation', {
	onload: function(frm, cdt, cdn) {
		frm.fields_dict['room_stay'].grid.get_field('room_id').get_query = function () {
			return {
				filters: {
					'status': 'AV' 
				}
			}
		}
	},
	refresh: function(frm, cdt, cdn) {
		reservation = frappe.get_doc(cdt, cdn);
		if (reservation.deposit > 0) {
			has_deposit = true;
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
			frm.page.add_menu_item(("Print Receipt"), function () {
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
		}

		if (reservation.__islocal == 1) {
			frm.set_df_property('wifi_password', 'hidden', 1);
		} else {
			reservation.room_stay.forEach(element => {
				room_list.push(element.room_id);
			});
		}

		frappe.meta.get_docfield('Room Stay', 'reservation_id', reservation.name).read_only = 1;

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

		if (reservation.status != 'Created') {
			frm.set_df_property('reservation_detail', 'set_only_once', 1);

			frappe.meta.get_docfield('Reservation Detail', 'expected_arrival', reservation.name).read_only = 1;
			frappe.meta.get_docfield('Reservation Detail', 'expected_departure', reservation.name).read_only = 1;
			frappe.meta.get_docfield('Reservation Detail', 'adult', reservation.name).read_only = 1;
			frappe.meta.get_docfield('Reservation Detail', 'child', reservation.name).read_only = 1;
			frappe.meta.get_docfield('Reservation Detail', 'allow_smoke', reservation.name).read_only = 1;
			frappe.meta.get_docfield('Reservation Detail', 'room_type', reservation.name).read_only = 1;
			frappe.meta.get_docfield('Reservation Detail', 'bed_type', reservation.name).read_only = 1;
			frappe.meta.get_docfield('Reservation Detail', 'room_id', reservation.name).read_only = 1;
			frappe.meta.get_docfield('Reservation Detail', 'extra_bed', reservation.name).read_only = 1;
			frappe.meta.get_docfield('Reservation Detail', 'payment_type', reservation.name).read_only = 1;
			frappe.meta.get_docfield('Reservation Detail', 'room_rate', reservation.name).read_only = 1;
		}

		if (!has_deposit) {
			wrapper = frm.get_field("payment_method").$wrapper;
			var html = '<select id="payment_method"></select>';
			wrapper.html(html);
			
			frappe.call({
				method: 'front_desk.front_desk.doctype.reservation.reservation.get_debit_account_name_list',
				args: {

				},
				callback: (response) => {
					for (var i = 0; i < response.message.length; i++) {
						var z = document.createElement('option');
						z.setAttribute('value', response.message[i]);
						var t = document.createTextNode(response.message[i]);
						z.appendChild(t);
						document.getElementById('payment_method').appendChild(z);
					}
				}
			});
		} else {
			frm.set_df_property('deposit', 'set_only_once', 1);
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
						},
						callback: (response) => {
	
						}
					});
				}
			});

			if (!has_deposit && reservation.deposit > 0) {
				var e = document.getElementById('payment_method');
				var v = e.options[e.selectedIndex].value;
	
				frappe.call({
					method: 'front_desk.front_desk.doctype.reservation.reservation.create_deposit_journal_entry',
					args: {
						reservation_id: reservation.name,
						amount: reservation.deposit,
						debit_account_name: v
					},
					callback: (response) => {
						wrapper.html(null);
						has_deposit = true;
					}
				});
			}
		}
	}
});

frappe.ui.form.on('Room Stay', {
	room_stay_add: function(frm, cdt, cdn) {
		locals[cdt][cdn].reservation_id = reservation.name;
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

 frappe.ui.form.on('Room Stay', 'issue_card', function(frm) {
	frm.set_value('status', 'In House');
	frm.save();
 });

 frappe.ui.form.on('Room Stay', 'print', function(frm, cdt, cdn) {
	var w = window.open(frappe.urllib.get_full_url("/printview?"
			+"doctype="+encodeURIComponent("Room Stay")
			+"&name="+encodeURIComponent(frappe.get_doc(cdt, cdn).name)
			+"&no_letterhead=0"
			));

	if (!w) {
		frappe.msgprint(__("Please enable pop-ups")); return;
	}
 });

frappe.ui.form.on('Room Stay', {
	room_id: function (frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		frappe.db.get_value("Hotel Room", child.room_id, "room_type", (hotel_room) => {
			frappe.db.get_value("Customer", frm.doc.customer_id, "customer_group", (customer) => {
				var	grid_row = frm.fields_dict['room_stay'].grid.grid_rows_by_docname[child.name];
				var  field = frappe.utils.filter_dict(grid_row.docfields, {fieldname: "room_rate"})[0];
				field.get_query = function () {
					return {
						filters: {
							'room_type': hotel_room.room_type,
							'customer_group': customer.customer_group
						}
					}
				}
			});
		});
	}
});

frappe.ui.form.on('Reservation Detail',{
	form_render: function(frm, cdt, cdn) {
		var child = locals[cdt][cdn];

		get_room_available(frm, child);
		get_room_type_available(frm, child);
		get_bed_type_available(frm, child);
		get_room_rate(frm, child);
	},
	expected_arrival: function(frm, cdt, cdn) {
		var child = locals[cdt][cdn];

		child.room_id = undefined;
		child.room_type = undefined;
		child.bed_type = undefined;
		child.room_rate = undefined;
		frm.refresh_field('reservation_detail');

		get_room_available(frm, child);
		get_room_type_available(frm, child);
		get_bed_type_available(frm, child);
		get_room_rate(frm, child);
	},
	expected_departure: function(frm, cdt, cdn) {
		var child = locals[cdt][cdn];

		child.room_id = undefined;
		child.room_type = undefined;
		child.bed_type = undefined;
		child.room_rate = undefined;
		frm.refresh_field('reservation_detail');

		get_room_available(frm, child);
		get_room_type_available(frm, child);
		get_bed_type_available(frm, child);
		get_room_rate(frm, child);
	},
	room_id: function(frm, cdt, cdn) {
		var child = locals[cdt][cdn];

		if (child.room_id != undefined) {
			frappe.db.get_value('Hotel Room', {'name': child.room_id}, ['room_type', 'bed_type', 'allow_smoke'], function(response) {
				child.room_type = response.room_type;
				child.bed_type = response.bed_type;
				child.allow_smoke = response.allow_smoke
				frm.refresh_field('reservation_detail');

				get_room_rate(frm, child);
			});
		}
	},
	room_type: function(frm, cdt, cdn) {
		var child = locals[cdt][cdn];

		child.room_id = undefined;
		child.bed_type = undefined;
		child.room_rate = undefined;
		frm.refresh_field('reservation_detail');

		get_room_available(frm, child);
		get_bed_type_available(frm, child);
		get_room_rate(frm, child);
	},
	bed_type: function(frm, cdt, cdn) {
		var child = locals[cdt][cdn];

		child.room_id = undefined;
		frm.refresh_field('reservation_detail');

		get_room_available(frm, child);
	},
	allow_smoke: function(frm, cdt, cdn) {
		var child = locals[cdt][cdn];

		child.room_id = undefined;
		child.room_type = undefined;
		child.bed_type = undefined;
		child.room_rate = undefined;
		frm.refresh_field('reservation_detail');

		get_room_available(frm, child);
		get_room_type_available(frm, child);
		get_bed_type_available(frm, child);
		get_room_rate(frm, child);
	}
});

function get_room_available(frm, child) {
	var	grid_row = frm.fields_dict['reservation_detail'].grid.grid_rows_by_docname[child.name];
	var  field = frappe.utils.filter_dict(grid_row.docfields, {fieldname: "room_id"})[0];

	if (child.bed_type != undefined) {
		field.get_query = function () {
			return {
				query: 'front_desk.front_desk.doctype.reservation.reservation.get_room_available_by_room_type_bed_type',
				filters: {
					'expected_arrival': child.expected_arrival,
					'expected_departure': child.expected_departure,
					'allow_smoke': child.allow_smoke,
					'room_type': child.room_type,
					'bed_type': child.bed_type
				}
			}
		}
	} else if (child.room_type != undefined) {
		field.get_query = function () {
			return {
				query: 'front_desk.front_desk.doctype.reservation.reservation.get_room_available_by_room_type',
				filters: {
					'expected_arrival': child.expected_arrival,
					'expected_departure': child.expected_departure,
					'allow_smoke': child.allow_smoke,
					'room_type': child.room_type
				}
			}
		}
	} else if (child.expected_arrival != undefined && child.expected_departure != undefined) {
		field.get_query = function () {
			return {
				query: 'front_desk.front_desk.doctype.reservation.reservation.get_room_available',
				filters: {
					'expected_arrival': child.expected_arrival,
					'expected_departure': child.expected_departure,
					'allow_smoke': child.allow_smoke
				}
			}
		}
	} else {
		field.get_query = function () {
			return {
				query: 'front_desk.front_desk.doctype.reservation.reservation.get_empty_array'
			}
		}
	}
}

function get_room_type_available(frm, child) {
	var	grid_row = frm.fields_dict['reservation_detail'].grid.grid_rows_by_docname[child.name];
	var  field = frappe.utils.filter_dict(grid_row.docfields, {fieldname: "room_type"})[0];

	if (child.expected_arrival != undefined && child.expected_departure != undefined) {
		field.get_query = function () {
			return {
				query: 'front_desk.front_desk.doctype.reservation.reservation.get_room_type_available',
				filters: {
					'expected_arrival': child.expected_arrival,
					'expected_departure': child.expected_departure,
					'allow_smoke': child.allow_smoke
				}
			}
		}
	} else {
		field.get_query = function () {
			return {
				query: 'front_desk.front_desk.doctype.reservation.reservation.get_empty_array'
			}
		}
	}
}

function get_bed_type_available(frm, child) {
	var	grid_row = frm.fields_dict['reservation_detail'].grid.grid_rows_by_docname[child.name];
	var  field = frappe.utils.filter_dict(grid_row.docfields, {fieldname: "bed_type"})[0];
	
	if (child.room_type != undefined) {
		field.get_query = function () {
			return {
				query: 'front_desk.front_desk.doctype.reservation.reservation.get_bed_type_available',
				filters: {
					'expected_arrival': child.expected_arrival,
					'expected_departure': child.expected_departure,
					'allow_smoke': child.allow_smoke,
					'room_type': child.room_type
				}
			}
		}
	} else {
		field.get_query = function () {
			return {
				query: 'front_desk.front_desk.doctype.reservation.reservation.get_empty_array'
			}
		}
	}
}

function get_room_rate(frm, child) {
	var	grid_row = frm.fields_dict['reservation_detail'].grid.grid_rows_by_docname[child.name];
	var  field = frappe.utils.filter_dict(grid_row.docfields, {fieldname: "room_rate"})[0];

	if (child.room_type != undefined) {
		frappe.db.get_value("Customer", frm.doc.customer_id, "customer_group", (customer) => {
			field.get_query = function () {
				return {
					filters: {
						'room_type': child.room_type
					},
					or_filters: [
						{'customer_group': 'All Customer Groups'},
						{'customer_group': customer.customer_group}
					]
				}
			}
		});
	} else {
		field.get_query = function () {
			return {
				query: 'front_desk.front_desk.doctype.reservation.reservation.get_empty_array'
			}
		}
	}
}