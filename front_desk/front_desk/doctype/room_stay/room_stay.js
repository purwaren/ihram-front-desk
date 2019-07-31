// Copyright (c) 2019, PMM and contributors
// For license information, please see license.txt

frappe.ui.form.on('Room Stay', {
	setup: function(frm, cdt, cdn) {
		frm.set_df_property('deposit', 'set_only_once', 1);

		var room_stay = frappe.get_doc(cdt, cdn);
		if (room_stay.deposit.length <= 0){
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

			var df = null;

			df = frappe.meta.get_docfield('Folio Transaction', 'folio_id', room_stay.name);
			df.read_only = 1;

			df = frappe.meta.get_docfield('Folio Transaction', 'flag', room_stay.name);
			df.read_only = 1;

			df = frappe.meta.get_docfield('Folio Transaction', 'account_id', room_stay.name);
			df.read_only = 1;

			df = frappe.meta.get_docfield('Folio Transaction', 'remark', room_stay.name);
			df.read_only = 1;
		}

		// frm.fields_dict['deposit'].grid.get_field('folio_id').get_query = function () {
		// 	return {
		// 		filters: {
		// 			'reservation_id': room_stay.reservation_id
		// 		}
		// 	}
		// }
	},
	onload: function(frm) {
		
	},
	refresh: function(frm) {
		
	}
});
