// Copyright (c) 2019, PMM and contributors
// For license information, please see license.txt
var bill_breakdown = null;
var breakdown_shown = false;
var outstanding_now = 0;
var deposit = 0;
var account = null;
var account_against = null;
var cash_used_in_hotel_bill_payment = false;
var need_resave = false;

frappe.ui.form.on('Hotel Bill', {
	onload: function(frm) {
		frm.get_field("bill_breakdown").grid.only_sortable();
		if (frm.doc.is_paid == 1) {
			set_all_read_only();
			frm.disable_save();
		}
		need_resave = false;
	},
	onload_post_render(frm, cdt, cdn) {
		var bp_list = frappe.get_doc(cdt, cdn).bill_payments;
		calculatePayments(frm, bp_list);
		calculateDepositRefund(frm);
	},
	refresh: function(frm, cdt, cdn) {
		var x = frappe.get_doc(cdt, cdn).bill_breakdown;
		x.forEach(hideBreakdown);
		if (frm.doc.is_paid == 0) {
			frm.set_intro(__('Remember to always save the Hotel Bill after every change.'));
			frm.set_intro(__('If there are any billing not yet showing, click the \'Update Billing\' button to trigger the billing update.'));
			frm.set_footnote(__('To finalize the payment, click the \'Make Payment\' button. ' +
				'Once the payment finalized, the Hotel Bill cannot be changed anymore.'));
			frm.add_custom_button(__("Update Billing"), function () {
				frappe.call({
					method: "front_desk.front_desk.doctype.hotel_bill.hotel_bill.update_hotel_bill",
					args: {
						reservation_id: frm.doc.reservation_id
					},
					callback: (r) => {
						if (r.message) {
								frappe.show_alert(__(r.message)); return;
								frm.reload_doc();
						}
					}
				});
			});
		}
		else if (frm.doc.is_paid == 1) {
			frm.set_intro(__('This Hotel Bill Payment successfully finalized. You cannot change it anymore.'));
			frm.set_footnote(__('This Hotel Bill Payment successfully finalized. You cannot change it anymore.'));
			cur_frm.set_df_property('hb_section_break8', 'hidden', 1);
		}
	},
	bill_toggle_details: function(frm, cdt, cdn) {
		bill_breakdown = frappe.get_doc(cdt, cdn).bill_breakdown;
		if (breakdown_shown == false) {
			bill_breakdown.forEach(showBreakdown);
			breakdown_shown = true;
		}
		else {
			bill_breakdown.forEach(hideBreakdown);
			breakdown_shown = false;
		}
	},
	use_deposit: function(frm, cdt, cdn) {
		var bp_list = frappe.get_doc(cdt, cdn).bill_payments;
		calculatePayments(frm, bp_list);
		calculateDepositRefund(frm);
	},
	round_down_change: function(frm, cdt, cdn) {
		var bp_list = frappe.get_doc( 'Hotel Bill', frm.doc.name ).bill_payments;
		calculatePayments(frm, bp_list);
	},
	make_payment: function (frm, cdt, cdn) {
		if (frm.doc.__unsaved != undefined && frm.doc.__unsaved == 1) {
			frappe.msgprint("The Hotel Bill has been modified, please click Save and Reload page, before making payment entry");
		}
		else if (need_resave) {
			frappe.msgprint("The Hotel Bill has been modified, please click Save and Reload page, before making payment entry");
		}
		else {
			frappe.call({
				method: "front_desk.front_desk.doctype.hotel_bill.hotel_bill.make_payment_hotel_bill",
				args: {
					hotel_bill_id: cdn,
					latest_outstanding_amount: frm.doc.bill_outstanding_amount
				},
				callback: (effin_response) => {
					if (effin_response.message) {
						if (effin_response.message == 1) {
							frm.set_intro(__('This Hotel Bill Payment successfully finalized. You cannot change it anymore.'));
							frm.reload_doc();
						}
					}
				}
			});
		}
	}
});

frappe.ui.form.on('Hotel Bill Payments', {
	mode_of_payment: function (frm, cdt, cdn) {
		let child = locals[cdt][cdn];
		if (child.mode_of_payment == 'Cash') {
			cash_used_in_hotel_bill_payment = true;
			if (child.payment_amount > 0) {
				var bp_list = frappe.get_doc( 'Hotel Bill', frm.doc.name ).bill_payments;
				calculatePayments(frm, bp_list);
			}
		}
		else {
			cash_used_in_hotel_bill_payment = false;
			frm.set_value('bill_change_amount', 0);
			frm.set_value('bill_change_round_amount', 0);
			frm.set_value('bill_rounded_change_amount', 0);
		}
	},
	payment_amount: function (frm, cdt, cdn) {
		var bp_list = frappe.get_doc( 'Hotel Bill', frm.doc.name ).bill_payments;
		calculatePayments(frm, bp_list);
	},
	bill_payments_remove: function (frm, cdt, cdn) {
		var bp_list = frappe.get_doc( 'Hotel Bill', frm.doc.name ).bill_payments;
		calculatePayments(frm, bp_list);
	}
});

frappe.ui.form.on ('Hotel Bill Refund', {
	bill_refund_add: function (frm, cdt, cdn) {
		let child = locals[cdt][cdn];
		frappe.call({
			method: "front_desk.front_desk.doctype.hotel_bill.hotel_bill.deposit_refund_account",
			args: {type: 'account'},
			callback: (resp) => {
				if (resp.message) {
					account = resp.message;
					child.account = account;
					frm.refresh_field('bill_refund');
				}
			}
		});
	}
});

function hideBreakdown(item, index) {
	if(item.is_folio_trx_pairing == 0) {
		$('[data-name='+item.name+']').hide();
	}
}

function showBreakdown(item, index) {
	if(item.is_folio_trx_pairing == 0) {
		$('[data-name='+item.name+']').show();
	}
}

function calculatePayments(frm, bp_list) {
	var total_payment = 0;
	var current_change = frm.doc.bill_change_amount;
	var i;
	for (i = 0; i < bp_list.length; i++) {
		total_payment += bp_list[i].payment_amount;
	}

	if (frm.doc.use_deposit == 1) {
		total_payment += frm.doc.bill_deposit_amount;
	}

	var diff = total_payment - frm.doc.bill_grand_total;
	if (diff < 0) {
		frm.set_value('bill_outstanding_amount', diff*-1);
		if (cash_used_in_hotel_bill_payment) {
			frm.set_value('bill_change_amount', 0);
			frm.set_value('bill_change_round_amount', 0);
			frm.set_value('bill_rounded_change_amount', 0);
		}
	}
	else {
		frm.set_value('bill_outstanding_amount', 0);
		if (cash_used_in_hotel_bill_payment) {
			frm.set_value('bill_change_amount', diff);

			var roundedChange = Math.floor(diff / 100) * 100;

			if (frm.doc.round_down_change == 1) {
				frm.set_value('bill_change_round_amount', diff - roundedChange);
				frm.set_value('bill_rounded_change_amount', roundedChange);
			} else {
				frm.set_value('bill_change_round_amount', 0);
				frm.set_value('bill_rounded_change_amount', diff);
			}
		}
	}
}

function calculateDepositRefund(frm) {
	let deposit_description = 'Deposit Refund of Reservation: ' + frm.doc.reservation_id;
	let bill_amount = frm.doc.bill_grand_total;
	let deposit_amount = frm.doc.bill_deposit_amount;
	let refund_amount_in_db = 0;

	frappe.call({
		method: "front_desk.front_desk.doctype.hotel_bill_refund.hotel_bill_refund.get_value_by_desc",
		args: {
			desc: deposit_description,
			field: 'name'
		},
		callback: (r) => {

			frappe.call({
				method: "front_desk.front_desk.doctype.hotel_bill_refund.hotel_bill_refund.get_value_by_desc",
				args: {
					desc: deposit_description,
					field: 'refund_amount'
				},
				callback: (r2) => {
					if (r2.message) {
						refund_amount_in_db = r2.message;
					}
					if (r.message) {
						let child = locals['Hotel Bill Refund'][r.message];
						if (child == undefined) {
							frm.reload_doc();
						}
						else {
							if (frm.doc.use_deposit == 1) {
								if (deposit_amount > bill_amount) {
									if (parseFloat(refund_amount_in_db) != 0 && (parseFloat(refund_amount_in_db) != parseFloat(deposit_amount - bill_amount))) {
										console.log("need resave");
										need_resave = true;
									}
									else {
										need_resave = false;
									}
									child.refund_amount = deposit_amount - bill_amount;
									frm.refresh_field('bill_refund');
								}
								else {
									let tbl = frm.doc.bill_refund || [];
									let i = tbl.length;
									while (i--) {
										if (tbl[i].refund_description == deposit_description) {
											frm.get_field("bill_refund").grid.grid_rows[i].remove();
										}
									}
									frm.refresh_field('bill_refund');
								}
							}
							else {
								if ( parseFloat(refund_amount_in_db) != 0 && parseFloat(refund_amount_in_db) != parseFloat(deposit_amount)) {
									console.log("need resave");
									need_resave = true;
								}
								else {
									need_resave = false;
								}
								child.refund_amount = deposit_amount;
								frm.refresh_field('bill_refund');
							}
						}
					}
					else {
						let deposit_refund_exist_not_saved_yet_id = null;
						let refund_list = frm.doc.bill_refund || [];
						let i = refund_list.length;
						while (i--) {
							if (refund_list[i].refund_description == deposit_description) {
								deposit_refund_exist_not_saved_yet_id = refund_list[i].name;
							}
						}
						if (deposit_refund_exist_not_saved_yet_id != null) {
							console.log("masuk ada ghost child");
							let ghost_child = locals['Hotel Bill Refund'][deposit_refund_exist_not_saved_yet_id];
							if (frm.doc.use_deposit == 1) {
								if (deposit_amount > bill_amount) {
									ghost_child.refund_amount = deposit_amount - bill_amount;
									frm.refresh_field('bill_refund');
								}
								else {
									let tbl = frm.doc.bill_refund || [];
									let i = tbl.length;
									while (i--) {
										if (tbl[i].refund_description == deposit_description) {
											frm.get_field("bill_refund").grid.grid_rows[i].remove();
										}
									}
									frm.refresh_field('bill_refund');
								}
							}
							else {
								ghost_child.refund_amount = deposit_amount;
								frm.refresh_field('bill_refund');
							}
						}
						else {
							console.log("masuk di tidak ada ghost child");
							if (frm.doc.use_deposit == 1) {
								console.log("masuk ke use_deposit == 1");
								if (deposit_amount > bill_amount) {
									console.log("masuk ke deposit amount > bill_amount");
									frappe.call({
										method: "front_desk.front_desk.doctype.hotel_bill.hotel_bill.deposit_refund_account",
										args: {type: 'account'},
										callback: (account_resp) => {
											if (account_resp.message) {
												account = account_resp.message;
												frappe.call({
													method: "front_desk.front_desk.doctype.hotel_bill.hotel_bill.deposit_refund_account",
													args: {type: 'against'},
													callback: (against_resp) => {
														if (against_resp.message) {
															account_against = against_resp.message;
															var new_child = frm.add_child('bill_refund');
															new_child.refund_description = deposit_description;
															new_child.refund_amount = deposit_amount - bill_amount;
															new_child.is_refunded = 0;
															new_child.account = account;
															new_child.account_against = account_against;
															frm.refresh_field('bill_refund');
														}
													}
												});
											}
										}
									});
								}
							}
							else {
								console.log("masuk ke use_deposit == 0");
								frappe.call({
									method: "front_desk.front_desk.doctype.hotel_bill.hotel_bill.deposit_refund_account",
									args: {type: 'account'},
									callback: (account_resp) => {
										if (account_resp.message) {
											account = account_resp.message;
											frappe.call({
												method: "front_desk.front_desk.doctype.hotel_bill.hotel_bill.deposit_refund_account",
												args: {type: 'against'},
												callback: (against_resp) => {
													if (against_resp.message) {
														account_against = against_resp.message;
														var new_child = frm.add_child('bill_refund');
														new_child.refund_description = deposit_description;
														new_child.refund_amount = deposit_amount;
														new_child.is_refunded = 0;
														new_child.account = account;
														new_child.account_against = account_against;
														frm.refresh_field('bill_refund');
													}
												}
											});
										}
									}
								});
							}
						}
					}
				}
			});
		}
	});
}

function set_all_read_only() {
	cur_frm.set_df_property('use_deposit', 'read_only', 1);
	cur_frm.get_field("bill_refund").grid.only_sortable();
	cur_frm.get_field("bill_payments").grid.only_sortable();
	cur_frm.set_df_property('round_down_change', 'read_only', 1);

	frappe.meta.get_docfield('Hotel Bill Refund', 'refund_description', cur_frm.docname).read_only = true;
	frappe.meta.get_docfield('Hotel Bill Refund', 'refund_amount', cur_frm.docname).read_only = true;
	frappe.meta.get_docfield('Hotel Bill Refund', 'account', cur_frm.docname).read_only = true;

	frappe.meta.get_docfield('Hotel Bill Payments', 'mode_of_payment', cur_frm.docname).read_only = true;
	frappe.meta.get_docfield('Hotel Bill Payments', 'payment_amount', cur_frm.docname).read_only = true;
	frappe.meta.get_docfield('Hotel Bill Payments', 'payment_reference_no', cur_frm.docname).read_only = true;
	frappe.meta.get_docfield('Hotel Bill Payments', 'payment_reference_date', cur_frm.docname).read_only = true;
	frappe.meta.get_docfield('Hotel Bill Payments', 'payment_clearance_date', cur_frm.docname).read_only = true;
}