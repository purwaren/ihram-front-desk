// Copyright (c) 2020, PMM and contributors
// For license information, please see license.txt
var total_cash_count = 0;
var total_payment = 0;
var total_refund = 0;

frappe.ui.form.on('Hotel Shift', {
	onload: function(frm) {
		frm.get_field('cc_detail').grid.cannot_add_rows = true;
		frm.get_field('payment_detail').grid.cannot_add_rows = true;
		frm.get_field('refund_detail').grid.cannot_add_rows = true;
		frappe.call({
			method: "front_desk.front_desk.doctype.hotel_shift.hotel_shift.populate_cr_payment",
			callback: (response) => {
				if (response.message) {
					frm.set_value('payment_detail', []);
					$.each(response.message, function (i, d) {
						let item = frm.add_child('payment_detail');
						item.mode_of_payment = d.mode_of_payment;
						item.amount = d.amount;
						total_payment += d.amount;
					});
					frm.set_value('total_payment', total_payment);
				}
				frm.refresh_field('payment_detail');

				frappe.call({
					method: "front_desk.front_desk.doctype.hotel_shift.hotel_shift.populate_cr_refund",
					callback: (response) => {
						if (response.message) {
							frm.set_value('refund_detail', []);
							$.each(response.message, function (i, d) {
								let item = frm.add_child('refund_detail');
								item.type = d.type;
								item.amount = d.amount;
								total_refund += d.amount;
							});
							frm.set_value('total_refund', total_refund);
							frm.set_value('balance', total_payment);
						}
						frm.refresh_field('refund_detail');
					}
				});
			}
		});
		frappe.call({
			method: "front_desk.front_desk.doctype.hotel_shift.hotel_shift.get_cash_balance",
			callback: (response) => {
				if (response.message) {
					frm.set_value('cash_balance', response.message);
				}
			}
		});
		if (frm.doc.__islocal == 1) {
			frappe.call({
				method: "front_desk.front_desk.doctype.hotel_shift.hotel_shift.populate_cash_count",
				callback: (response) => {
					if (response.message) {
						var cc_nominal = response.message;
						frm.set_value('cc_detail', []);
						for (var i = 0; i < cc_nominal.length; i++) {
							var item = frm.add_child('cc_detail');
							item.nominal = cc_nominal[i];
							item.qty = 0;
							item.amount = 0;
						}
					}
					frm.refresh_field('cc_detail');
				}
			});
		}
	}
});

frappe.ui.form.on('CC Detail',{
	qty: function (frm, cdt, cdn) {
		let child = locals[cdt][cdn];
		child.amount = child.nominal*child.qty;
		frm.refresh_field('cc_detail');

		let cc_detail_list = frm.doc.cc_detail;

		for (var i = 0; i < cc_detail_list.length; i++) {
			total_cash_count += cc_detail_list[i].amount;
		}
		frm.set_value('total_cash_count', total_cash_count);
	}
});
