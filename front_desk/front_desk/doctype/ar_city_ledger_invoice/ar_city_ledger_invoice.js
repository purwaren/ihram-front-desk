// Copyright (c) 2019, PMM and contributors
// For license information, please see license.txt
var cash_used = false;

frappe.ui.form.on('AR City Ledger Invoice', {
	onload: function(frm) {
		check_if_payment_cash(frm, frm.doc.payment_details);
		if (frm.doc.is_paid == 1) {
			set_all_read_only();
			frm.disable_save();
		}
		if (frm.doc.hotel_order_channel) {
			get_folio_by_order_channel(frm);
		}
		if (frm.doc.__islocal == 1) {
			frm.set_df_property('payment_detail_section_break', 'hidden', 1);
			frm.set_df_property('payment_section_break', 'hidden', 1);
			frm.set_df_property('make_payment_section_break', 'hidden', 1);
		}
		else {
			if (frm.doc.folio == undefined || frm.doc.folio.length <= 0) {
				frm.set_df_property('payment_detail_section_break', 'hidden', 1);
				frm.set_df_property('payment_section_break', 'hidden', 1);
			}
			if (frm.doc.payment_details.length <= 0) {
				frm.set_df_property('make_payment_section_break', 'hidden', 1);
			}
		}
	},
	onload_post_render: function(frm) {
		calculate_payments(frm, frm.doc.payment_details);
	},
	refresh: function(frm) {
		if(frm.doc.is_paid == 0) {
			frm.set_intro(__('Remember to always save the AR City Ledger Invoice after every change.'));
		}
		else if (frm.doc.is_paid == 1) {
			frm.set_intro(__('This AR City Ledger Invoice successfully finalized. You cannot change it anymore.'));
			frm.set_footnote(__('This AR City Ledger Invoice successfully finalized. You cannot change it anymore.'));
			frm.set_df_property('make_payment_section_break', 'hidden', 1);
		}
		if (frm.doc.hotel_order_channel) {
			get_folio_by_order_channel(frm);
		}
		if (frm.doc.folio != undefined && frm.doc.folio.length > 0) {
			frm.set_df_property('payment_detail_section_break', 'hidden', 0);
			frm.set_df_property('payment_section_break', 'hidden', 0);
		}
		if (frm.doc.payment_details != undefined && frm.doc.payment_details.length > 0) {
			frm.set_df_property('make_payment_section_break', 'hidden', 0);
		}
	},
	hotel_order_channel: function(frm) {
		get_folio_by_order_channel(frm);
	},
	round_down_change: function (frm) {
		calculate_payments(frm, frm.doc.payment_details);
	},
	make_payment: function (frm, cdt, cdn) {
		if (frm.doc.__unsaved != undefined && frm.doc.unsaved == 1) {
			frappe.msgprint("The AR City Ledger Invoice has been modified. Please click Save and reload the page, before making payment entry");
		}
		else {
			frappe.call({
				method: "front_desk.front_desk.doctype.ar_city_ledger_invoice.ar_city_ledger_invoice.make_payment_ar_city_ledger_invoice",
				args: {
					ar_city_ledger_invoice_id: cdn,
					latest_outstanding_amount: frm.doc.outstanding_amount
				},
				callback: (r) => {
					if (r.message){
						if (r.message == 1) {
							frm.set_intro(__('This AR City Ledger Invoice successfully finalized. You cannot change it anymore.'));
							frm.reload_doc();
						}
					}
				}
			})
		}
	}
});

frappe.ui.form.on('Folio to be Collected', {
	folio_add: function (frm) {
		if (frm.doc.hotel_order_channel == undefined) {
			frappe.msgprint("Please fill & choose Channel first.");
		}
	},
	before_folio_remove: function (frm, cdt, cdn) {
		let child = locals[cdt][cdn];
		if (child.folio_id) {
			console.log("diremove = " + child.folio_id);
			frappe.call({
				method: "front_desk.front_desk.doctype.folio.folio.set_ar_city_ledger_invoice_id_to_null",
				args: {
					folio_id: child.folio_id,
				},
			});
		}
	}
});

frappe.ui.form.on('AR City Ledger Invoice Payments', {
	mode_of_payment: function (frm, cdt, cdn) {
		let child = locals[cdt][cdn];
		if (child.mode_of_payment == 'Cash') {
			cash_used = true;
			calculate_payments(frm, frm.doc.payment_details);
		}
		else {
			cash_used = false;
			frm.set_value('change_rounding_amount', 0);
			frm.set_value('change_amount', 0);
			frm.set_value('rounded_change_amount', 0);
		}
	},
	payment_amount: function (frm) {
		calculate_payments(frm, frm.doc.payment_details);
	},
	payment_details_remove: function (frm) {
		calculate_payments(frm, frm.doc.payment_details);
	}
});

function get_folio_by_order_channel(frm) {
	let field = frm.fields_dict['folio'].grid.fields_map['folio_id'];
	if (frm.doc.hotel_order_channel) {
		frappe.call({
			method: 'front_desk.front_desk.doctype.ar_city_ledger.ar_city_ledger.get_folio_list_by_order_channel',
			args: {
				hotel_order_channel: frm.doc.hotel_order_channel
			},
			callback: (r) => {
				if (r.message) {
					console.log(r.message);
					field.get_query = function () {
						return {
							filters: [
								['Folio', 'name', 'in', r.message],
								['Folio', 'room_bill_amount', '!=', 0],
								// ['Folio', 'ar_city_ledger_invoice_id', '!=', null],
								// ['Folio', 'city_ledger_payment_final', '=', 0],
							],
						}
					}
				}
			}
		});
	}
}

function set_all_read_only() {
	cur_frm.set_df_property('round_down_change','read_only', 1);
	cur_frm.get_field("folio").grid.only_sortable();
	cur_frm.get_field("payment_details").grid.only_sortable();

	frappe.meta.get_docfield('Folio to be Collected', 'folio_id', cur_frm.docname).read_only = true;
	frappe.meta.get_docfield('AR City Ledger Invoice Payments', 'mode_of_payment', cur_frm.docname).read_only = true;
	frappe.meta.get_docfield('AR City Ledger Invoice Payments', 'payment_amount', cur_frm.docname).read_only = true;
	frappe.meta.get_docfield('AR City Ledger Invoice Payments', 'payment_reference_no', cur_frm.docname).read_only = true;
	frappe.meta.get_docfield('AR City Ledger Invoice Payments', 'payment_reference_date', cur_frm.docname).read_only = true;
	frappe.meta.get_docfield('AR City Ledger Invoice Payments', 'payment_clearance_date', cur_frm.docname).read_only = true;
}

function calculate_payments(frm, payment_list) {
	var total_payment = 0;
	if (payment_list != undefined && payment_list.length > 0) {
		for (var key in payment_list) {
			total_payment += payment_list[key].payment_amount;
		}
		var diff = total_payment - frm.doc.total_amount;
		if (diff < 0) {
			frm.set_value('outstanding_amount', diff*-1);
			if (cash_used) {
				frm.set_value('change_rounding_amount', 0);
				frm.set_value('change_amount', 0);
				frm.set_value('rounded_change_amount', 0);
			}
		}
		else {
			frm.set_value('outstanding_amount', 0);
			if (cash_used) {
				frm.set_value('change_amount', diff);
				var roundedChange = Math.floor(diff / 100) * 100;
				if (frm.doc.round_down_change == 1) {
					frm.set_value('change_rounding_amount', diff - roundedChange);
					frm.set_value('rounded_change_amount', roundedChange);
				}
				else {
					frm.set_value('change_rounding_amount', 0);
					frm.set_value('rounded_change_amount', diff);
				}
			}
		}
	}
}

function check_if_payment_cash(frm, payment_list) {
	if (payment_list != undefined && payment_list.length > 0) {
		var i;
		for (var key in payment_list) {
			if (payment_list[key].mode_of_payment == 'Cash') {
				cash_used = true;
			}
		}
	}
}

cur_frm.set_query("mode_of_payment", "payment_details", function(doc, cdt, cdn) {
	var d = locals[cdt][cdn];
	return{
		filters: [
			['Mode of Payment', 'mode_of_payment', '!=', 'City Ledger'],
		]
	}
});