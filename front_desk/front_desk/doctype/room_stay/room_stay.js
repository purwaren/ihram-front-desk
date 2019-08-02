// Copyright (c) 2019, PMM and contributors
// For license information, please see license.txt

var wrapper = null;
var room_stay = null;
var has_deposit = false;
var credit_account_name = '';
var debit_account_name_list = '';

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
				method: 'front_desk.front_desk.doctype.room_stay.room_stay.get_credit_account_name',
				args: {
					
				},
				callback: (response) => {
					credit_account_name = response.message;

					frappe.call({
						method: 'front_desk.front_desk.doctype.folio.folio.get_folio_name',
						args: {
							reservation_id: room_stay.reservation_id
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

			var html = '<select id="payment_method"></select>';
			wrapper.html(html);

			frappe.call({
				method: 'front_desk.front_desk.doctype.room_stay.room_stay.get_debit_account_name_list',
				args: {

				},
				callback: (response) => {
					console.log(response.message);
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
	},
	onload_post_render: function(frm, cdt, cdn) {
		
	},
	before_save: function(frm, cdt, cdn) {
		
	},
	after_save: function(frm, cdt, cdn) {
		if (!has_deposit) {
			var e = document.getElementById('payment_method');
			var v = e.options[e.selectedIndex].value;

			frappe.call({
				method: 'front_desk.front_desk.doctype.room_stay.room_stay.create_deposit_journal_entry',
				args: {
					reservation_id: room_stay.reservation_id,
					amount: room_stay.deposit[0].amount,
					debit_account_name: v,
					credit_account_name: credit_account_name
				},
				callback: (response) => {
					wrapper.html(null);
					has_deposit = true;
					console.log("SUCCESS");
				}
			});
		}
	}
});

cur_frm.fields_dict['room_id'].get_query = function(doc) {
	return {
		filters: {
			"status": 'AV'
		}
	}
}