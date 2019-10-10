// Copyright (c) 2019, PMM and contributors
// For license information, please see license.txt
var bill_breakdown = null;
var breakdown_shown = false;
var outstanding_now = 0;
var deposit = 0;
var cash_used_in_hotel_bill_payment = false;

frappe.ui.form.on('Hotel Bill', {
	onload: function(frm) {
		frm.get_field("bill_breakdown").grid.only_sortable();
	},
	onload_post_render(frm, cdt, cdn) {
		var bp_list = frappe.get_doc(cdt, cdn).bill_payments;
		calculatePayments(frm, bp_list);

		frm.add_custom_button(__("Update Billing"), function () {
				frappe.call({
					method: "front_desk.front_desk.doctype.hotel_bill.hotel_bill.update_hotel_bill",
					args: {
						reservation_id: frm.doc.reservation_id
					},
					callback: (r) => {
						if (r.message) {
                            	frappe.msgprint(__(r.message)); return;
                            	frm.reload_doc();
						}
					}
				});
			});
	},
	refresh: function(frm, cdt, cdn) {
		var x = frappe.get_doc(cdt, cdn).bill_breakdown;
		x.forEach(hideBreakdown);
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
	frappe.call({
		method: "front_desk.front_desk.doctype.hotel_bill_refund.hotel_bill_refund.get_value_by_desc",
		args: {
			desc: deposit_description,
			field: 'name'
		},
		callback: (r) => {
			let child = locals['Hotel Bill Refund'][r.message];
			let bill_amount = frm.doc.bill_grand_total;
			let deposit_amount = frm.doc.bill_deposit_amount;
			var account = '';
			var account_against = '';

			if (frm.doc.use_deposit == 1) {
				if (deposit_amount > bill_amount) {
					child.refund_amount = deposit_amount - bill_amount;
					frm.refresh_field('bill_refund');
				}
				else {
					var tbl = frm.doc.bill_refund || [];
					var i = tbl.length;
					while (i--) {
						if (tbl[i].refund_description == deposit_description) {
							frm.get_field("bill_refund").grid.grid_rows[i].remove();
						}
					}
					frm.refresh_field('bill_refund');
				}
			} else {
				if (child != undefined) {
					child.refund_amount = deposit_amount;
					frm.refresh_field('bill_refund');
				}
				else {
					frappe.call({
						method: "front_desk.front_desk.doctype.hotel_bill.hotel_bill.deposit_refund_account",
						args: {type: 'account'},
						callback: (account) => {
							account = account.message;
							frappe.call({
								method: "front_desk.front_desk.doctype.hotel_bill.hotel_bill.deposit_refund_account",
								args: {type: 'against'},
								callback: (against) => {
									account_against = against.message;
									var new_child = frm.add_child('bill_refund');
									new_child.refund_description = deposit_description;
									new_child.refund_amount = deposit_amount;
									new_child.is_refunded = 0;
									new_child.account = account;
									new_child.account_against = account_against;
									frm.refresh_field('bill_refund');
								}
							});
						}
					});
				}
			}
		}
	});
}