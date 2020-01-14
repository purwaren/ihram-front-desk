// Copyright (c) 2020, PMM and contributors
// For license information, please see license.txt
var total_cash_count = 0;

frappe.ui.form.on('Hotel Shift', {
	onload: function(frm) {
		frm.get_field('cc_detail').grid.cannot_add_rows = true;
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
			})
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
