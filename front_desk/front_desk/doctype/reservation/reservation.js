// Copyright (c) 2019, PMM and contributors
// For license information, please see license.txt

var reservation = null;
var has_deposit = false;
var wrapper = null;
var credit_account_name = '';
var debit_account_name_list = '';
var room_list = [];

frappe.ui.form.on('Reservation', {
	setup: function(frm, cdt, cdn){

	},
	before_load: function(frm, cdt, cdn) {
		reservation = frappe.get_doc(cdt, cdn);
		if (reservation.deposit.length > 0) {
			has_deposit = true;
		}
		if (reservation.status == 'Created' || reservation.status == 'Cancel') {
			frm.set_df_property('room_stay_section', 'hidden', 1);
			frm.set_df_property('room_stay', 'hidden', 1);
			frm.set_df_property('deposit_section', 'hidden', 1);
			frm.set_df_property('deposit', 'hidden', 1);
			frm.set_df_property('payment_method', 'hidden', 1);
		} else if (reservation.status == 'Confirmed') {
			frm.set_df_property('reservation_detail', 'set_only_once', 1);
			frm.set_df_property('deposit', 'set_only_once', 1);
			if (!has_deposit) {
				wrapper = frm.get_field("payment_method").$wrapper;
			}
		} else if (reservation.status == 'Finish') {
			frm.set_df_property('reservation_detail', 'set_only_once', 1);
			frm.set_df_property('room_stay', 'set_only_once', 1);
			frm.set_df_property('deposit', 'set_only_once', 1);
		}
		reservation.room_stay.forEach(element => {
			room_list.push(element.room_id);
		});
	},
	onload: function(frm, cdt, cdn) {
		if (reservation.status == 'Confirmed') {
			if (!has_deposit) {
				frappe.call({
					method: 'front_desk.front_desk.doctype.reservation.reservation.get_credit_account_name',
					args: {
						
					},
					callback: (response) => {
						credit_account_name = response.message;
	
						frappe.call({
							method: 'front_desk.front_desk.doctype.folio.folio.get_folio_name',
							args: {
								reservation_id: reservation.name
							},
							callback: (response) => {
								frm.add_child('deposit', {
									folio_id: response.message,
									flag: 'Debit',
									account_id: credit_account_name,
									remark: 'Deposit'
								});
								frm.refresh_field('deposit');
							}
						});
					}
				});
			}

			frm.fields_dict['room_stay'].grid.get_field('room_id').get_query = function () {
				return {
					filters: {
						'status': 'AV'
					}
				}
			}
		}
	},
	refresh: function(frm, cdt, cdn) {
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
		if (reservation.status != 'Cancel' || reservation.status != 'Created') {
			frm.page.add_menu_item(("Print Receipt"), function () {
				frappe.call({
					method: "front_desk.front_desk.doctype.reservation.reservation.print_receipt_reservation",
					args: {
						reservation_id: reservation.name
					},
					callback: (response) => {
						console.log(response)
						window.open(response.message, "_blank")
					}
				});
			});
		}
		if (reservation.status != 'Created') {
			var df = null;
			df = frappe.meta.get_docfield('Reservation Detail', 'expected_arrival', reservation.name);
			df.read_only = 1;

			df = frappe.meta.get_docfield('Reservation Detail', 'expected_departure', reservation.name);
			df.read_only = 1;

			df = frappe.meta.get_docfield('Reservation Detail', 'adult', reservation.name);
			df.read_only = 1;

			df = frappe.meta.get_docfield('Reservation Detail', 'child', reservation.name);
			df.read_only = 1;

			df = frappe.meta.get_docfield('Reservation Detail', 'room_type', reservation.name);
			df.read_only = 1;

			df = frappe.meta.get_docfield('Reservation Detail', 'bed_type', reservation.name);
			df.read_only = 1;

			df = frappe.meta.get_docfield('Reservation Detail', 'payment_type', reservation.name);
			df.read_only = 1;

			df = frappe.meta.get_docfield('Reservation Detail', 'room_rate', reservation.name);
			df.read_only = 1;
			
		}

		if (reservation.status == 'Confirmed') {
			var df = null;
			df = frappe.meta.get_docfield('Room Stay', 'reservation_id', reservation.name);
			df.read_only = 1;

			if (!has_deposit) {
				df = frappe.meta.get_docfield('Folio Transaction', 'folio_id', reservation.name);
				df.read_only = 1;
	
				df = frappe.meta.get_docfield('Folio Transaction', 'flag', reservation.name);
				df.read_only = 1;
	
				df = frappe.meta.get_docfield('Folio Transaction', 'account_id', reservation.name);
				df.read_only = 1;
	
				df = frappe.meta.get_docfield('Folio Transaction', 'remark', reservation.name);
				df.read_only = 1;
	
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
			}
		}
	},
	onload_post_render: function(frm, cdt, cdn) {
		
	},
	before_save: function(frm, cdt, cdn) {
		frappe.call({
			method: 'front_desk.front_desk.doctype.hotel_room.hotel_room.set_availability',
			args: {
				room_name_list: room_list,
				availability: 'AV'
			},
			callback: (response) => {
				room_list = [];
				reservation.room_stay.forEach(element => {
					room_list.push(element.room_id);
				});

				frappe.call({
					method: 'front_desk.front_desk.doctype.hotel_room.hotel_room.set_availability',
					args: {
						room_name_list: room_list,
						availability: 'RS'
					},
					callback: (response) => {

					}
				});
			}
		});
	},
	after_save: function(frm, cdt, cdn) {
		if (reservation.status == 'Confirmed') {
			if (!has_deposit) {
				var e = document.getElementById('payment_method');
				var v = e.options[e.selectedIndex].value;
	
				frappe.call({
					method: 'front_desk.front_desk.doctype.reservation.reservation.create_deposit_journal_entry',
					args: {
						reservation_id: reservation.name,
						amount: reservation.deposit[0].amount,
						debit_account_name: v,
						credit_account_name: credit_account_name
					},
					callback: (response) => {
						wrapper.html(null);
						has_deposit = true;
					}
				});
			}
		}
	},
});

frappe.ui.form.on('Room Stay', {
	room_stay_add: function(frm, cdt, cdn) {
		locals[cdt][cdn].reservation_id = reservation.name;
	}
});