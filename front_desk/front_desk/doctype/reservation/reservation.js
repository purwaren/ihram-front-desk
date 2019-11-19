// Copyright (c) 2019, PMM and contributors
// For license information, please see license.txt
var reservation = null;
var has_deposit = false;
var room_list = [];
var reservation_detail_remove_list = [];
var after_remove = false;
var guest_request = 1;
var cash_used_in_room_bill_payment = false;
var room_bill_cash_count = 0;
var max_discount = 90;

frappe.ui.form.on('Reservation', {
	onload: function(frm, cdt, cdn) {
		frm.set_query('payment_method', () => {
			return {
				query: 'front_desk.front_desk.doctype.reservation.reservation.get_debit_account'
			}
		});
		MakePaymentButtonStatus(frm, cdt,cdn);
		frm.get_field("room_bill_paid").grid.only_sortable();
		if (frm.doc.__islocal != 1) {
			copy_reservation_detail_to_room_stay(frm, cdt, cdn);
		}
	},
	refresh: function(frm) {
		if (cur_frm.doc.deposit > 0) {
			has_deposit = true;
		}
		if (has_deposit) {
			frm.set_df_property('deposit', 'set_only_once', 1);
			frm.set_df_property('payment_method', 'set_only_once', 1);
		}
		if (frm.doc.status == 'In House') {
			if (frm.doc.type == 'INDIVIDUAL') {
				frm.page.add_menu_item(("Cancel"), function () {
					let today = frappe.datetime.nowdate();
					console.log(frm.doc.name);
					frappe.confirm(__("You are about to Cancel the Reservation. Are you sure?"), function() {
						frappe.call({
							method: "front_desk.front_desk.doctype.reservation.reservation.cancel_individual_reservation",
							args: {
								reservation_id: reservation.name,
							},
							callback: (r) => {
								if (r.message == 1) {
									frappe.show_alert(__("Reservation Cancellation Success.")); return;
								}
							}
						});
					});
				});
			}
			frm.page.add_menu_item(("Check Out"), function () {
				frappe.call({
					method: "front_desk.front_desk.doctype.reservation.reservation.checkout_reservation",
					args: {
						reservation_id: reservation.name
					},
					callback: (r) => {
						if (r.message != undefined) {
							if (r.message == 1) {
								frappe.show_alert(__(" Check Out Process Success.")); return;
								frm.reload_doc();
							}
							else if (r.message == 0) {
								frappe.confirm(__("Cannot Check Out before the Hotel Bill Payment is complete. Open Hotel Bill Page?"),
									function() {
										frappe.call({
											method: "front_desk.front_desk.doctype.reservation.reservation.get_hotel_bill_url",
											args: {
												reservation_id: reservation.name
											},
											callback: (r) => {
												if (r.message) {
													var w = window.open(r.message, '_self');
													if (!w) {
														frappe.msgprint(__("Please enable pop-ups")); return;
													}
												}
											}
										});
									}
								)
							}
							else if (r.message == 2) {
								frappe.msgprint("Cannot Check Out, there are still room bills that haven't been paid yet.")
							}
						}
					}
				});
			});
		}
	},
	onload_post_render: function(frm, cdt, cdn) {
		$('*[data-fieldname="reservation_detail"]').find('.grid-remove-rows').hide();
		$('*[data-fieldname="room_stay"]').find('.grid-remove-rows').hide();

		reservation = frappe.get_doc(cdt, cdn);

		frappe.meta.get_docfield('Room Stay', 'reservation_id', reservation.name).hidden = true;
		frm.refresh_field('room_stay');

		if (reservation.__unsaved == 1) {
			frappe.meta.get_docfield('Room Stay', 'section_break_1', reservation.name).hidden = true;
		} else {
			frappe.meta.get_docfield('Room Stay', 'section_break_1', reservation.name).hidden = false;
		}

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
            frm.set_df_property('room_bill_paid_section', 'hidden', 1);
            frm.set_df_property('room_bill_paid', 'hidden', 1);
		}
		else {
			frm.set_df_property('paid_bill_amount', 'hidden', 0);
			frm.set_df_property('is_round_change_amount', 'hidden', 0);
			frm.set_df_property('rbp_change_rounding_amount', 'hidden', 0);
			frm.set_df_property('room_bill_change_amount', 'hidden', 0);
			frm.set_df_property('rbp_rounded_change_amount', 'hidden', 0);
			frm.set_df_property('room_bill_section_break', 'hidden', 0);
			frm.set_df_property('room_bill_payments', 'hidden', 0);
			frm.set_df_property('room_bill_paid_section', 'hidden', 0);
			frm.set_df_property('room_bill_paid', 'hidden', 0);
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
					},
					callback: (r) => {
						if (r.message != undefined) {
							if (r.message == 1) {
								frappe.show_alert(__(" Check Out Process Success.")); return;
								frm.reload_doc();
							}
							else {
								frappe.confirm(__("Cannot Check Out before the Hotel Bill Payment is complete. Open Hotel Bill Page?"),
									function() {
										frappe.call({
											method: "front_desk.front_desk.doctype.reservation.reservation.get_hotel_bill_url",
											args: {
												reservation_id: reservation.name
											},
											callback: (r) => {
												if (r.message) {
													var w = window.open(r.message, '_self');
													if (!w) {
														frappe.msgprint(__("Please enable pop-ups")); return;
													}
												}
											}
										});
									}
								)
							}
						}
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

		if (reservation.status != 'Cancel' && reservation.status != 'Created' && reservation.status != 'Confirmed' && parseFloat(reservation.deposit) > 0) {
			frm.add_custom_button(__("Show Billing"), function () {
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
		}
		// frm.add_custom_button(__("populate"), function () {
		// 	frappe.call({
		// 		method: "front_desk.front_desk.doctype.reservation.reservation.populate_ba_of_all_folio"
		// 	})
		// });
		if (reservation.status != 'Cancel' && reservation.status != 'Created') {
			// frm.add_custom_button(__("Trigger Auto Charges"), function () {
			// 	frappe.call({
			// 		method: "front_desk.front_desk.doctype.reservation.reservation.trigger_room_charge",
			// 		args: {
			// 			reservation_id: reservation.name
			// 		}
			// 	});
			 	// frappe.call({
				// 	method: "front_desk.front_desk.doctype.reservation.reservation.create_additional_charge",
				// 	args: {
				// 		reservation_id: reservation.name
				// 	}
				// });
				// frappe.call({
				// 	method: "front_desk.front_desk.doctype.folio.folio.copy_all_trx_from_sales_invoice_to_folio",
				// });
			// });

			// frm.add_custom_button(__("Print Receipt"), function() {
    		// 	frappe.call({
			// 		method: "frappe.client.get_value",
			// 		args: {
			// 			doctype: "Folio",
			// 			filters: {"reservation_id": reservation.name},
			// 			fieldname: "name"
			// 		},
			// 		callback: (r) => {
			// 			if (r.message.name) {
			// 				var w = window.open(frappe.urllib.get_full_url("/printview?"
			// 						+"doctype="+encodeURIComponent("Folio")
			// 						+"&name="+encodeURIComponent(r.message.name)
			// 						+"&trigger_print=1"
			// 						+"&no_letterhead=0"
			// 						))
			//
			// 				if (!w) {
			// 					frappe.msgprint(__("Please enable pop-ups")); return;
			// 				}
			// 			}
			// 		}
			// 	});
			// });

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
			frm.set_df_property('room_bill_paid_section', 'hidden', 1);
            frm.set_df_property('room_bill_paid', 'hidden', 1);
            frm.set_df_property('room_bill_adjustment_section', 'hidden', 1);
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
		calculateRoomBillPayments(frm, rbp_list);
	},
	make_payment: function(frm, cdt, cdn) {
		frappe.call({
			method: 'front_desk.front_desk.doctype.reservation.reservation.create_room_bill_payment_entry',
			args: {
				reservation_id: reservation.name,
				room_bill_amount: frm.doc.room_bill_amount,
				paid_bill_amount:frm.doc.paid_bill_amount,
				is_round_down_checked: frm.doc.is_round_change_amount,
				change_rounding_amount: frm.doc.rbp_change_rounding_amount,
				change_amount: frm.doc.room_bill_change_amount,
				rounded_change_amount: frm.doc.rbp_rounded_change_amount,
			},
			callback: (response) => {
				frm.set_value('room_bill_amount', response.message);
				frm.save();
				frappe.show_alert("Room Bill Payment successfully made. Please check <b>ROOM PAYMENT HISTORY</b> for the details.")
			}
		});
		MakePaymentButtonStatus(frm, cdt,cdn);
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
		MakePaymentButtonStatus(frm, cdt,cdn);
		frm.reload_doc();
	}
});

var child = undefined;

frappe.ui.form.on('Reservation Detail', {
	form_render: function(frm, cdt, cdn) {
		child = locals[cdt][cdn];

		manage_form_render('reservation_detail');
		manage_filter('', 'reservation_detail');
	},
	expected_arrival: function(frm, cdt, cdn) {
		manage_filter('expected_arrival', 'reservation_detail');
		let child = locals[cdt][cdn];
		if (child.expected_arrival < frappe.datetime.get_today()) {
			child.expected_arrival = frappe.datetime.now_datetime();
			frm.refresh_field('reservation_detail');
			frappe.msgprint("Arrival date must be greater today.");
		}
	},
	expected_departure: function(frm, cdt, cdn) {
		manage_filter('expected_departure', 'reservation_detail');
		let child = locals[cdt][cdn];
		if (child.__islocal == 1) {
			if (child.expected_departure < frappe.datetime.get_today()) {
				child.expected_departure = null;
				frm.refresh_field('reservation_detail');
				frappe.msgprint("Departure date must be greater than today.");
			}
			else if (child.expected_departure < child.expected_arrival) {
				child.expected_departure = null;
				frm.refresh_field('reservation_detail');
				frappe.msgprint("Departure date must be greater than Arrival date.");
			}
		}
	},
	allow_smoke: function(frm, cdt, cdn) {
		manage_filter('allow_smoke', 'reservation_detail');
	},
	room_type: function(frm, cdt, cdn) {
		manage_filter('room_type', 'reservation_detail');
	},
	bed_type: function(frm, cdt, cdn) {
		manage_filter('bed_type', 'reservation_detail');
	},
	room_id: function(frm, cdt, cdn) {
		manage_filter('room_id', 'reservation_detail');
	},
	before_reservation_detail_remove: function(frm, cdt, cdn) {
		if (child.__islocal != 1) {
			reservation_detail_remove_list.push(child);
		}
	},
	reservation_detail_remove: function(frm, cdt, cdn) {
		after_remove = true;
	}
});

frappe.ui.form.on('Room Stay', {
	room_stay_add: function(frm, cdt, cdn) {
		child = locals[cdt][cdn];
		child.reservation_id = reservation.name;
	},
	form_render: function(frm, cdt, cdn) {
		child = locals[cdt][cdn];

		manage_form_render('room_stay');
		manage_filter('', 'room_stay');
		if (child.__islocal == 1) {
			frappe.meta.get_docfield('Room Stay', 'section_break_2', reservation.name).hidden = true;
		}
		else {
			frappe.meta.get_docfield('Room Stay', 'section_break_2', reservation.name).hidden = false;
		}
	},
	arrival: function (frm, cdt, cdn) {
		manage_filter('arrival', 'room_stay');
		let child = locals[cdt][cdn];
		if (child.arrival < frappe.datetime.get_today()) {
			child.arrival = frappe.datetime.now_datetime();
			frm.refresh_field('room_stay');
			frappe.msgprint("Arrival date must be greater today.");
		}
	},
	departure: function (frm, cdt, cdn) {
		let child = locals[cdt][cdn];
		if (child.__islocal == 1) {
			if (child.departure < frappe.datetime.get_today()) {
				child.departure = null;
				frm.refresh_field('room_stay');
				frappe.msgprint("Departure date must be greater than today.");
			}
			else if (child.departure < child.arrival) {
				child.departure = null;
				frm.refresh_field('room_stay');
				frappe.msgprint("Departure date must be greater than Arrival date.");
			}
		}

		frappe.call({
			method: "front_desk.front_desk.doctype.room_stay.room_stay.get_value",
			args: {
				room_stay_id: child.name,
				field: 'departure'
			},
			callback: (r) => {
				 if (r.message != undefined) {
				 	if (r.message < child.departure) {
						child.departure = r.message;
						child.is_need_refund = 0;
						child.old_departure = null;
						child.old_total_bill_amount = 0;
						frm.refresh_field('room_stay');
						frappe.msgprint("Please create New Room Stay instead of extending Departure date.");
					}
				 	else if (r.message == child.departure) {
				 		frm.reload_doc();
					}
				 	else if (child.departure < frappe.datetime.get_today()) {
				 		child.departure = r.message;
				 		child.is_need_refund = 0;
						child.old_departure = null;
						child.old_total_bill_amount = 0;
						frm.refresh_field('room_stay');
						frappe.msgprint("Departure date must be greater than today.");
					}
				 	else if (child.departure < child.arrival) {
				 		child.departure = r.message;
				 		child.is_need_refund = 0;
						child.old_departure = null;
						child.old_total_bill_amount = 0;
						frm.refresh_field('room_stay');
						frappe.msgprint("Departure date must be greater than Arrival date.");
					}
					else {
						child.old_departure = r.message;
						child.is_need_refund = 1;
						frappe.call({
							method: "front_desk.front_desk.doctype.room_stay.room_stay.get_value",
							args: {
								room_stay_id: child.name,
								field: 'total_bill_amount'
							},
							callback: (resp) => {
								if (resp.message) {
									let old_total_bill_amount = resp.message;
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
												if (old_total_bill_amount > 0) {
													child.old_total_bill_amount = old_total_bill_amount;
												}
												child.total_bill_amount = response.message;
												frm.refresh_field('room_stay');
											}
										});
									}
								}
							}
						});
					}
				 }
				 else {
				 	manage_filter('departure', 'room_stay');
				 }
			}
		});
	},
	allow_smoke: function(frm, cdt, cdn) {
		manage_filter('allow_smoke', 'room_stay');
	},
	room_type: function(frm, cdt, cdn) {
		manage_filter('room_type', 'room_stay');
	},
	bed_type: function(frm, cdt, cdn) {
		manage_filter('bed_type', 'room_stay');
	},
	room_id: function (frm, cdt, cdn) {
		manage_filter('room_id', 'room_stay');
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
		var w = window.open(frappe.urllib.get_full_url('/desk#Form/Move%20Room/New%20Move%20Room%201?initial_room_stay=' + child.name));
		
		if (!w) {
			frappe.msgprint(__("Please enable pop-ups")); return;
		}
	},
	discount_percentage: function(frm, cdt, cdn) {
		if (child.discount_percentage >= max_discount) {
			frappe.msgprint("Discount Limit of "  + max_discount+ "% Exceeded. Please input lower Discount Rate.");
			child.discount_percentage = 0;
			frm.refresh_field('room_stay');
		}
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
					frm.refresh_field('room_stay');
				}
			});
		}
	},
	room_rate: function(frm, cdt, cdn) {
		let child = locals[cdt][cdn];
		let old_total_bill_amount = child.total_bill_amount;
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
					if (old_total_bill_amount > 0) {
						child.old_total_bill_amount = old_total_bill_amount;
					}
					child.total_bill_amount = response.message;
					frm.refresh_field('room_stay');
				}
			});
		}
	},
	room_stay_remove: function(frm, cdt, cdn) {
		after_remove = true;
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
			if (child.rbp_amount > 0) {
				calculateRoomBillPayments(frm, rbp_list);
				roomBillCashCount(frm, rbp_list);
			}
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

frappe.ui.form.on("Room Bill Paid", {
	print_rbpd_button: function(frm, cdt, cdn) {
		var w = window.open(frappe.urllib.get_full_url("/printview?"
			+"doctype="+encodeURIComponent("Room Bill Paid")
			+"&name="+encodeURIComponent(cdn)
			+"&format="+encodeURIComponent("Room Bill Payment Receipt")
			+"&no_letterhead=0"
			));

		if (!w) {
			frappe.msgprint(__("Please enable pop-ups")); return;
		}
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

function manage_form_render(doc_field) {
	after_remove = false;
	guest_request = 1;

	if (reservation.status == 'Cancel' || reservation.status == 'Finish') {
		set_all_field_read_only(doc_field, true);
	} else {
		if (doc_field == 'reservation_detail') {
			if (reservation.room_stay != undefined) {
				reservation.room_stay.forEach(element => {
					if (child.room_id == element.room_id && child.expected_arrival < formatDate(element.departure)) {
						set_all_field_read_only('reservation_detail', true);
					}
				});
			} else {
				set_all_field_read_only('reservation_detail', false);
			}
		} else if (doc_field = 'room_stay') {
			frappe.db.get_value('Move Room', {'initial_room_stay':child.name}, 'replacement_room_stay', (move_room) => {
				if (move_room != undefined) {
					set_all_field_read_only('room_stay', true);
				} else {
					set_all_field_read_only('room_stay', false);

					frappe.db.get_value('Move Room', {'replacement_room_stay':child.name}, 'guest_request', (move_room) => {
						if (move_room != undefined) {
							$(".grid-delete-row").hide();

							guest_request = move_room.guest_request;
							if (guest_request == 0) {
								frappe.meta.get_docfield('Room Stay', 'room_rate', reservation.name).read_only = true;
								cur_frm.refresh_field('room_stay');
							}
						}
					});
				}
			});
		}
	}
}

function set_all_field_read_only(doc_field, flag) {
	if (flag == true) {
		$(".grid-delete-row").hide();
	}

	var fields = cur_frm.fields_dict[doc_field].grid.docfields;
	var x = fields.length;

	for (var i = 0; i < x; i++) {
		fields[i].read_only = flag;
	}
	frappe.meta.get_docfield('Room Stay', 'total_bill_amount', reservation.name).read_only = true;
	frappe.meta.get_docfield('Room Stay', 'is_need_refund', reservation.name).read_only = true;
	frappe.meta.get_docfield('Room Stay', 'old_departure', reservation.name).read_only = true;
	frappe.meta.get_docfield('Room Stay', 'old_total_bill_amount', reservation.name).read_only = true;

	cur_frm.refresh_field(doc_field);
}

function manage_filter(child_field, doc_field) {
	if (!after_remove) {
		if (child_field == 'expected_arrival' || child_field == 'expected_departure' || child_field == 'arrival' || child_field == 'departure' || child_field == 'allow_smoke') {

			child.room_type = undefined;
			child.bed_type = undefined;
			child.room_id = undefined;
			if (guest_request == 1) {
				child.room_rate = undefined;
			}
	
			cur_frm.refresh_field(doc_field);
	
			get_available('room_type', doc_field);
			get_available('bed_type', doc_field);
			get_available('room_id', doc_field);
			if (guest_request == 1) {
				get_room_rate(doc_field);
			}
	
		} else if (child_field == 'room_type') {
			
			child.bed_type = undefined;
			child.room_id = undefined;
			if (guest_request == 1) {
				child.room_rate = undefined;
			}
	
			cur_frm.refresh_field(doc_field);
	
			get_available('bed_type', doc_field);
			get_available('room_id', doc_field);
			if (guest_request == 1) {
				get_room_rate(doc_field);
			}
	
		} else if (child_field == 'bed_type') {
			
			child.room_id = undefined;	
			cur_frm.refresh_field(doc_field);
			get_available('room_id', doc_field);
	
		} else if (child_field == 'room_id') {
			let old_room_type = child.room_type;
			let old_bed_type = child.bed_type;
			if (child.room_id != undefined) {
				frappe.db.get_value('Hotel Room', {'name': child.room_id}, ['room_type', 'bed_type'], function(response) {
					child.room_type = response.room_type;
					child.bed_type = response.bed_type;
					if (guest_request == 1) {
						if (old_room_type != child.room_type) {
							child.room_rate = undefined;
						}
					}
	
					cur_frm.refresh_field(doc_field);
	
					get_available('room_type', doc_field);
					get_available('bed_type', doc_field);
					get_available('room_id', doc_field);
					if (guest_request == 1) {
						if (old_room_type != child.room_type) {
							get_room_rate(doc_field);
						}
					}
				});
			}

		} else {
			cur_frm.refresh_field(doc_field);

			get_available('room_type', doc_field);
			get_available('bed_type', doc_field);
			get_available('room_id', doc_field);
			if (guest_request == 1) {
				get_room_rate(doc_field);
			}
		}
	}
}

function get_available(child_field, doc_field) {
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

function get_room_rate(child_field) {
	var field = cur_frm.fields_dict[child_field].grid.fields_map['room_rate'];

	if (child.room_type != undefined) {
		frappe.db.get_value("Customer", cur_frm.doc.customer_id, "customer_group", (customer) => {
			field.get_query = function () {
				return {
					filters: {
						'room_type': child.room_type,
						'is_disabled': 0
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
		if (rbp_list[i].is_paid == 0) {
			total_payment += rbp_list[i].rbp_amount;
		}
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

function MakePaymentButtonStatus(frm, cdt, cdn) {
	reservation = frappe.get_doc(cdt, cdn);
	var rbp_list = frappe.get_doc('Reservation', reservation.name).room_bill_payments;
	var exist_rbp_not_paid = false;
	var i = 0;
	if (rbp_list != undefined && rbp_list.length > 0) {
		for (i = 0; i < rbp_list.length; i++) {
			if (rbp_list[i].is_paid == 0) {
				exist_rbp_not_paid = true;
			}
		}
	}
	console.log("reservation.room_bill_amount: " + reservation.room_bill_amount);
	console.log("exist_rbp_not_paid: " + exist_rbp_not_paid);

	if (reservation.room_bill_amount > 0 && exist_rbp_not_paid) {
		frm.set_df_property('make_payment_section_break', 'hidden', 0);
		frm.set_df_property('make_payment', 'hidden', 0);
		console.log("show make payment");
	} else {
		frm.set_df_property('make_payment_section_break', 'hidden', 1);
		frm.set_df_property('make_payment', 'hidden', 1);
		console.log("hide make payment");
	}
}

function copy_reservation_detail_to_room_stay(frm, cdt, cdn) {
	reservation = frappe.get_doc(cdt, cdn);
	var rd_list = reservation.reservation_detail;
	var rs_list = reservation.room_stay;
	if (rd_list.length > 0 && rs_list.length == 0) {
		frm.set_value('room_stay', []);
		$.each(rd_list, function (i, d) {
			var now_date = new Date();
			var departure = new Date(d.expected_departure);
			var arrival = new Date(d.expected_arrival);
			var arrivalString = arrival.getFullYear() + '-' + ('0' + (arrival.getMonth()+1)).slice(-2) + '-' + ('0' + arrival.getDate()).slice(-2) + ' ' + ('0' + now_date.getHours()).slice(-2) + ':' + ('0' + now_date.getMinutes()).slice(-2) + ':00';
			var departureString = departure.getFullYear() + '-' + ('0' + (departure.getMonth()+1)).slice(-2) + '-' + ('0' + departure.getDate()).slice(-2) + ' ' + ('0' + now_date.getHours()).slice(-2) + ':' + ('0' + now_date.getMinutes()).slice(-2) + ':00';

			frappe.call({
				method: 'front_desk.front_desk.doctype.room_stay.room_stay.calculate_room_stay_bill',
				args: {
					arrival: arrivalString,
					departure: departureString,
					room_rate_id: d.room_rate,
					discount: 0,
				},
				callback: (response) => {
					var item = frm.add_child('room_stay');
					item.reservation_id = cdn;
					item.arrival = arrivalString;
					item.departure = departureString;
					item.room_type = d.room_type;
					item.bed_type = d.bed_type;
					item.room_id = d.room_id;
					item.room_rate = d.room_rate;
					item.total_bill_amount = response.message;
				}
			});
		})
	}
	frm.refresh_field('room_stay');
}