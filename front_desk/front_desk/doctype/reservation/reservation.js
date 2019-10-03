// Copyright (c) 2019, PMM and contributors
// For license information, please see license.txt

var reservation = null;
var has_deposit = false;
var room_list = [];
var reservation_detail_remove_list = [];
var is_remove_reservation_detail = false;
var is_remove_room_stay = false;
var guest_request = 1;
var cash_used_in_room_bill_payment = false;
var room_bill_cash_count = 0;

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

		if (frappe.get_doc( 'Reservation', reservation.name ).room_stay != undefined && (frappe.get_doc( 'Reservation', reservation.name ).room_stay).length <= 0) {
			frm.set_df_property('paid_bill_amount', 'hidden', 1);
			frm.set_df_property('is_round_change_amount', 'hidden', 1);
			frm.set_df_property('rbp_change_rounding_amount', 'hidden', 1);
			frm.set_df_property('room_bill_change_amount', 'hidden', 1);
			frm.set_df_property('rbp_rounded_change_amount', 'hidden', 1);
			frm.set_df_property('room_bill_section_break', 'hidden', 1);
			frm.set_df_property('room_bill_payments', 'hidden', 1);
		}
		else {
			frm.set_df_property('paid_bill_amount', 'hidden', 0);
			frm.set_df_property('is_round_change_amount', 'hidden', 0);
			frm.set_df_property('rbp_change_rounding_amount', 'hidden', 0);
			frm.set_df_property('room_bill_change_amount', 'hidden', 0);
			frm.set_df_property('rbp_rounded_change_amount', 'hidden', 0);
			frm.set_df_property('room_bill_section_break', 'hidden', 0);
			frm.set_df_property('room_bill_payments', 'hidden', 0);
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
		//enable for manual trigger scheduler release room
		// frm.add_custom_button(__("Trigger Release Room Scheduler"), function () {
		// 	frappe.call({
		// 		method: "front_desk.front_desk.doctype.reservation.reservation.auto_release_reservation_at_six_pm",
		// 	});
		// });

		// frm.add_custom_button(__("Special Charge"), function () {
		// 	frappe.call({
		// 		method: "front_desk.front_desk.doctype.reservation.reservation.create_special_charge",
		// 		args: {
		// 			reservation_id: reservation.name
		// 		}
		// 	});
		// });
        // frm.add_custom_button(__("Additional Charge"), function () {
		// 	frappe.call({
		// 		method: "front_desk.front_desk.doctype.reservation.reservation.create_additional_charge",
		// 		args: {
		// 			reservation_id: reservation.name
		// 		}
		// 	});
		// });
		if (reservation.status != 'Cancel' && reservation.status != 'Created') {
			// frm.add_custom_button(__("Trigger Auto Charges"), function () {
			// 	frappe.call({
			// 		method: "front_desk.front_desk.doctype.reservation.reservation.create_room_charge",
			// 		args: {
			// 			reservation_id: reservation.name
			// 		}
			// 	});
			// 	frappe.call({
			// 		method: "front_desk.front_desk.doctype.reservation.reservation.create_additional_charge",
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
			frm.set_df_property('room_payment_section', 'hidden', 1);
			frm.set_df_property('room_bill_amount', 'hidden', 1);
			frm.set_df_property('paid_bill_amount', 'hidden', 1);
			frm.set_df_property('room_bill_section_break', 'hidden', 1);
			frm.set_df_property('room_bill_payments', 'hidden', 1);
			frm.set_df_property('additional_charge_section', 'hidden', 1);
			frm.set_df_property('additional_charge', 'hidden', 1);
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
	is_round_change_amount: function(frm, cdt, cdn) {
		var rbp_list = frappe.get_doc( 'Reservation', reservation.name ).room_bill_payments;
		console.log("round change changed")
		calculateRoomBillPayments(frm, rbp_list);
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
				if (reservation.payment_method == undefined) {
					frappe.validated = false;
					frappe.msgprint('Please choose your deposit payment method');
					return false;
				}

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
			set_all_field_reservation_detail_read_only(true);
		} else if (reservation.room_stay != undefined) {
			reservation.room_stay.forEach(element => {
				if (child.room_id == element.room_id && child.expected_arrival < formatDate(element.departure)) {
					set_all_field_reservation_detail_read_only(true);
				}
			});
		} else {
			set_all_field_reservation_detail_read_only(false);
		}

		get_available('room_type', 'reservation_detail', child);
		get_available('bed_type', 'reservation_detail', child);
		get_available('room_id', 'reservation_detail', child);
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

			get_available('room_type', 'reservation_detail', child);
			get_available('bed_type', 'reservation_detail', child);
			get_available('room_id', 'reservation_detail', child);
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

			get_available('room_type', 'reservation_detail', child);
			get_available('bed_type', 'reservation_detail', child);
			get_available('room_id', 'reservation_detail', child);
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
	
			get_available('room_type', 'reservation_detail', child);
			get_available('bed_type', 'reservation_detail', child);
			get_available('room_id', 'reservation_detail', child);
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

			get_available('bed_type', 'reservation_detail', child);
			get_available('room_id', 'reservation_detail', child);
			get_room_rate('reservation_detail', child);
		}
	},
	bed_type: function(frm, cdt, cdn) {
		if (!is_remove_reservation_detail) {
			var child = locals[cdt][cdn];
			child.room_id = undefined;

			frm.refresh_field('reservation_detail');
	
			get_available('room_id', 'reservation_detail', child);
		}
	},
	room_id: function(frm, cdt, cdn) {
		if (!is_remove_reservation_detail) {
			var child = locals[cdt][cdn];

			if (child.room_id != undefined) {
				frappe.db.get_value('Hotel Room', {'name': child.room_id}, ['room_type', 'bed_type', 'allow_smoke'], function(response) {
					child.allow_smoke = response.allow_smoke;
					child.room_type = response.room_type;
					child.bed_type = response.bed_type;
					child.room_rate = undefined;

					frm.refresh_field('reservation_detail');

					get_available('room_type', 'reservation_detail', child);
					get_available('bed_type', 'reservation_detail', child);
					get_available('room_id', 'reservation_detail', child);
					get_room_rate('reservation_detail', child);
				});
			}
		}
	},
	before_reservation_detail_remove: function(frm, cdt, cdn) {
		is_remove_reservation_detail = true;
		var child = locals[cdt][cdn];
		if (child.__islocal != 1) {
			reservation_detail_remove_list.push(child);
		}
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
		frm.refresh_field('room_stay');

		if (reservation.status == 'Cancel' || reservation.status == 'Finish') {
			set_all_field_room_stay_read_only(true);
		} else {
			frappe.db.get_value('Move Room', {'initial_room_stay':child.name}, 'replacement_room_stay', (move_room) => {
				if (move_room != undefined) {
					set_all_field_room_stay_read_only(true);
				} else {
					set_all_field_room_stay_read_only(false);

					frappe.db.get_value('Move Room', {'replacement_room_stay':child.name}, 'guest_request', (move_room) => {
						if (move_room != undefined) {
							$(".grid-delete-row").hide();

							guest_request = move_room.guest_request;
							if (guest_request == 0) {
								frappe.meta.get_docfield('Room Stay', 'room_rate', reservation.name).read_only = true;
								frm.refresh_field('room_stay');
							}
						}
					});
				}
			});
		}

		get_available('room_type', 'room_stay', child);
		get_available('bed_type', 'room_stay', child);
		get_available('room_id', 'room_stay', child);

		if (guest_request == 1) {
			get_room_rate('room_stay', child);
		}
	},
	arrival: function (frm, cdt, cdn) {
		if (!is_remove_room_stay) {
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
				get_room_rate('room_stay', child);
			}
		}
	},
	departure: function (frm, cdt, cdn) {
		if (!is_remove_room_stay) {
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
				get_room_rate('room_stay', child);
			}
		}
	},
	allow_smoke: function(frm, cdt, cdn) {
		if (!is_remove_room_stay) {
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
				get_room_rate('room_stay', child);
			}
		}
	},
	room_type: function(frm, cdt, cdn) {
		if (!is_remove_room_stay) {
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
				get_room_rate('room_stay', child);
			}
		}
	},
	bed_type: function(frm, cdt, cdn) {
		if (!is_remove_room_stay) {
			var child = locals[cdt][cdn];
			child.room_id = undefined;

			frm.refresh_field('room_stay');
	
			get_available('room_id', 'room_stay', child);
		}
	},
	room_id: function (frm, cdt, cdn) {
		if (!is_remove_room_stay) {
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
						get_room_rate('room_stay', child);
					}
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
	discount_percentage: function(frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		if (child.arrival != undefined && child.departure != undefined && child.room_rate != undefined) {
			frappe.call({
				method: 'front_desk.front_desk.doctype.room_stay.room_stay.calculate_room_stay_bill',
				args: {
					arrival: child.arrival,
					departure: child.departure,
					room_rate_id: child.room_rate,
					discount: child.discount_percentage,
				},
				callback: (response) => {
					child.total_bill_amount = response.message;
				}
			});
		}
	},
	room_rate: function(frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		if (child.arrival != undefined && child.departure != undefined && child.room_rate != undefined) {
			frappe.call({
				method: 'front_desk.front_desk.doctype.room_stay.room_stay.calculate_room_stay_bill',
				args: {
					arrival: child.arrival,
					departure: child.departure,
					room_rate_id: child.room_rate,
					discount: child.discount_percentage,
				},
				callback: (response) => {
					child.total_bill_amount = response.message;
				}
			});
		}
	},
	room_stay_remove: function(frm, cdt, cdn) {
		is_remove_room_stay = true;
	}
});

frappe.ui.form.on("Room Bill Payments", {
	mode_of_payment: function (frm, cdt, cdn) {
		let child = locals[cdt][cdn];
		var rbp_list = frappe.get_doc( 'Reservation', frm.doc.name ).room_bill_payments;
		if (child.mode_of_payment == 'Cash') {
			cash_used_in_room_bill_payment = true;
			if (child.rbp_amount > 0) {
				calculateRoomBillPayments(frm, rbp_list);
				roomBillCashCount(frm, rbp_list);
			}
		}
		else {
			console.log("masuk sini dong");
			calculateRoomBillPayments(frm, rbp_list);
			roomBillCashCount(frm, rbp_list);
		}
	},
	rbp_amount: function (frm, cdt, cdn) {
		var rbp_list = frappe.get_doc( 'Reservation', frm.doc.name ).room_bill_payments;
		calculateRoomBillPayments(frm, rbp_list);
	},
	before_room_bill_payments_remove: function (frm, cdt, cdn) {
		let child = locals[cdt][cdn];
		var rbp_list = frappe.get_doc( 'Reservation', frm.doc.name ).room_bill_payments;

		if (child.mode_of_payment == 'Cash') {
			if (rbp_list.length == 1) {
				cash_used_in_room_bill_payment = false;
				frm.set_value('rbp_change_rounding_amount', 0);
				frm.set_value('room_bill_change_amount', 0);
				frm.set_value('rbp_rounded_change_amount', 0);
			}
			else {
				roomBillCashCount(frm, rbp_list);
			}
		}
	},
	room_bill_payments_remove: function (frm, cdt, cdn) {
		var rbp_list = frappe.get_doc( 'Reservation', frm.doc.name ).room_bill_payments;
		calculateRoomBillPayments(frm, rbp_list);
	},
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
	if (flag == true) {
		$(".grid-delete-row").hide();
	}

	cur_frm.fields_dict['reservation_detail'].grid.fields_map['expected_arrival'].read_only = flag;
	cur_frm.fields_dict['reservation_detail'].grid.fields_map['expected_departure'].read_only = flag;
	cur_frm.fields_dict['reservation_detail'].grid.fields_map['adult'].read_only = flag;
	cur_frm.fields_dict['reservation_detail'].grid.fields_map['child'].read_only = flag;
	cur_frm.fields_dict['reservation_detail'].grid.fields_map['allow_smoke'].read_only = flag;
	cur_frm.fields_dict['reservation_detail'].grid.fields_map['room_type'].read_only = flag;
	cur_frm.fields_dict['reservation_detail'].grid.fields_map['bed_type'].read_only = flag;
	cur_frm.fields_dict['reservation_detail'].grid.fields_map['room_id'].read_only = flag;
	cur_frm.fields_dict['reservation_detail'].grid.fields_map['extra_bed'].read_only = flag;
	cur_frm.fields_dict['reservation_detail'].grid.fields_map['payment_type'].read_only = flag;
	cur_frm.fields_dict['reservation_detail'].grid.fields_map['room_rate'].read_only = flag;

	cur_frm.refresh_field('reservation_detail');
}

function set_all_field_room_stay_read_only(flag) {
	if (flag == true) {
		$(".grid-delete-row").hide();
	}

	cur_frm.fields_dict['room_stay'].grid.fields_map['is_early_checkin'].read_only = flag;
	cur_frm.fields_dict['room_stay'].grid.fields_map['early_checkin_rate'].read_only = flag;
	cur_frm.fields_dict['room_stay'].grid.fields_map['arrival'].read_only = flag;
	cur_frm.fields_dict['room_stay'].grid.fields_map['is_late_checkout'].read_only = flag;
	cur_frm.fields_dict['room_stay'].grid.fields_map['late_checkout_rate'].read_only = flag;
	cur_frm.fields_dict['room_stay'].grid.fields_map['departure'].read_only = flag;
	cur_frm.fields_dict['room_stay'].grid.fields_map['reservation_id'].read_only = flag;
	cur_frm.fields_dict['room_stay'].grid.fields_map['allow_smoke'].read_only = flag;
	cur_frm.fields_dict['room_stay'].grid.fields_map['room_type'].read_only = flag;
	cur_frm.fields_dict['room_stay'].grid.fields_map['bed_type'].read_only = flag;
	cur_frm.fields_dict['room_stay'].grid.fields_map['room_id'].read_only = flag;
	cur_frm.fields_dict['room_stay'].grid.fields_map['room_rate'].read_only = flag;
	cur_frm.fields_dict['room_stay'].grid.fields_map['issue_card'].read_only = flag;
	cur_frm.fields_dict['room_stay'].grid.fields_map['print_check_in_receipt'].read_only = flag;
	cur_frm.fields_dict['room_stay'].grid.fields_map['move_room'].read_only = flag;

	cur_frm.refresh_field('room_stay');
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
				'parent': cur_frm.doc.name,
				'allow_smoke': child.allow_smoke,
				'room_type': child.room_type,
				'bed_type': child.bed_type
			}
		}
	}
}

function get_room_rate(child_field, child) {
	var field = cur_frm.fields_dict[child_field].grid.fields_map['room_rate'];

	if (child.room_type != undefined) {
		frappe.db.get_value("Customer", cur_frm.doc.customer_id, "customer_group", (customer) => {
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
				query: 'front_desk.front_desk.doctype.room_booking.room_booking.get_empty_array'
			}
		}
	}
}

function calculateRoomBillPayments(frm, rbp_list) {
	var total_payment = 0;
	var current_change = frm.doc.room_bill_change_amount;
	var i;
	for (i = 0; i < rbp_list.length; i++) {
		total_payment += rbp_list[i].rbp_amount;
	}
	frm.set_value('paid_bill_amount', total_payment);
	var diff = total_payment - frm.doc.room_bill_amount;

	if (diff < 0) {
		if (cash_used_in_room_bill_payment) {
			frm.set_value('rbp_change_rounding_amount', 0);
			frm.set_value('room_bill_change_amount', 0);
			frm.set_value('rbp_rounded_change_amount', 0);
		}
	}
	else {
		if (cash_used_in_room_bill_payment) {
			frm.set_value('room_bill_change_amount', diff);

			var roundedChange = Math.floor(diff / 100) * 100;

			if (frm.doc.is_round_change_amount == 1) {
				frm.set_value('rbp_change_rounding_amount', diff - roundedChange);
				frm.set_value('rbp_rounded_change_amount', roundedChange);
			} else {
				frm.set_value('rbp_change_rounding_amount', 0);
				frm.set_value('rbp_rounded_change_amount', diff);
			}
		}
	}
}

function roomBillCashCount(frm, rbp_list) {
	if (rbp_list.length > 0) {
		for (let i = 0; i < rbp_list.length; i++) {
			if (rbp_list[i].mode_of_payment === 'Cash') {
				room_bill_cash_count = room_bill_cash_count + 1;
				cash_used_in_room_bill_payment = true;
			}
		}
	}
	if (room_bill_cash_count <= 0) {
		cash_used_in_room_bill_payment = false;
		frm.set_value('rbp_change_rounding_amount', 0);
		frm.set_value('room_bill_change_amount', 0);
		frm.set_value('rbp_rounded_change_amount', 0);
	}
}