// Copyright (c) 2019, PMM and contributors
// For license information, please see license.txt

frappe.ui.form.on('Night Audit', {
	refresh: function(frm) {

	},
	fetch_button: function (frm) {
		frappe.call({
			method: "front_desk.front_desk.doctype.night_audit.night_audit.fetch_transactions",
			callback: (response) => {
				if (response.message) {
					frm.set_value('night_audit_transaction', []);
					if (response.message.length > 0) {
						$.each(response.message, function (i, d) {
							var item = frm.add_child('night_audit_transaction');
							item.transaction_type = d.transaction_type;
							item.transaction_id = d.transaction_id;
							item.reservation_id = d.reservation_id;
							item.folio_id = d.folio_id;
							item.amount = d.amount;
							item.title = d.title;
							item.remark = d.remark;
							item.debit_account = d.debit_account;
							item.credit_account = d.credit_account;
						});
						refresh_field('night_audit_transaction');
					}
					else {
						frappe.msgprint("No Transaction made to  be audited today.")
					}

				}
			}
		})
	}
});
