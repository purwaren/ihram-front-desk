// Copyright (c) 2019, PMM and contributors
// For license information, please see license.txt

var wrapper = null;
var room_stay = null;
var has_deposit = false;

frappe.ui.form.on('Room Stay', {
	setup: function(frm, cdt, cdn){

	},
	before_load: function(frm, cdt, cdn) {
		wrapper = frm.get_field("payment_method").$wrapper;
		frm.set_df_property('deposit', 'set_only_once', 1);
		room_stay = frappe.get_doc(cdt, cdn);
		if (room_stay.deposit.length > 0) {
			has_deposit = true;
		}
	},
	onload: function(frm, cdt, cdn) {
		if (!has_deposit) {
			frappe.call({
				method: 'front_desk.front_desk.doctype.folio.folio.get_folio_name',
				args: {
					reservation_id: room_stay.reservation_id
				},
				callback: (response) => {
					frm.add_child('deposit', {
						folio_id: response.message,
						flag: 'Debit',
						account_id: '1172.000 - Deposit Customer - IHRAM',
						remark: 'Deposit'
					});
					frm.refresh_field('deposit');
				}
			});
		}

		// frm.fields_dict['deposit'].grid.get_field('folio_id').get_query = function () {
		// 	return {
		// 		filters: {
		// 			'reservation_id': room_stay.reservation_id
		// 		}
		// 	}
		// }
	},
	refresh: function(frm, cdt, cdn) {
		if (!has_deposit) {
			var df = null;

			df = frappe.meta.get_docfield('Folio Transaction', 'folio_id', room_stay.name);
			df.read_only = 1;

			df = frappe.meta.get_docfield('Folio Transaction', 'flag', room_stay.name);
			df.read_only = 1;

			df = frappe.meta.get_docfield('Folio Transaction', 'account_id', room_stay.name);
			df.read_only = 1;

			df = frappe.meta.get_docfield('Folio Transaction', 'remark', room_stay.name);
			df.read_only = 1;

			var html = '<select id="payment_method"><option value="Cash">Cash</option><option value="Debit">Debit</option></select>';
			wrapper.html(html);
		}
	},
	onload_post_render: function(frm, cdt, cdn) {
		
	},
	before_save: function(frm, cdt, cdn) {
		
	},
	after_save: function(frm, cdt, cdn) {
		if (!has_deposit){
			var e = document.getElementById("payment_method");
			var v = e.options[e.selectedIndex].value;

			wrapper.html(null);
			has_deposit = true;
		}
	}
});
