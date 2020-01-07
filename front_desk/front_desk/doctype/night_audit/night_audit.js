// Copyright (c) 2019, PMM and contributors
// For license information, please see license.txt
var night_audit_id = null;

frappe.ui.form.on('Night Audit', {
	onload: function(frm, cdt, cdn) {
		night_audit_id = frappe.get_doc(cdt, cdn).name;
		frm.get_field("night_audit_transaction").grid.only_sortable();
		if (frm.doc.__islocal == 1) {
			frm.set_df_property('section_break_1', 'hidden', 1);
		}
		else {
			frm.set_df_property('section_break_1', 'hidden', 0);
			frappe.call({
				method: "front_desk.front_desk.doctype.night_audit.night_audit.get_total",
				args: {
					na_id: night_audit_id,
				},
				callback: (r) => {
					if (r.message) {
						frm.set_value('amount_to_be_posted', r.message[1]);
						frm.set_value('amount_posted', r.message[2]);
						console.log(r.message[0]);
						console.log(r.message[1]);
						console.log(r.message[2]);
					}
				}
			})
		}
		if (frm.doc.night_audit_transaction.length > 0) {
			frm.set_df_property('fetch_button', 'hidden', 1);
		}
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
							item.customer_id = d.customer_id;
						});
						refresh_field('night_audit_transaction');
					}
					else {
						frappe.msgprint("No Transaction made to  be audited today.")
					}

				}
			}
		})
	},
	post_to_journal: function (frm) {
		frappe.call({
			method: "front_desk.front_desk.doctype.night_audit.night_audit.post_all_to_journal",
			args: {
				na_id: night_audit_id,
			}
		})
		frm.reload_doc();
	}
});
frappe.ui.form.on('Night Audit Transaction', {
	form_render: function(frm, cdt, cdn){
		if (frm.doc.__islocal == 1) {
			frappe.meta.get_docfield('Night Audit Transaction', 'section_break_0', night_audit_id).hidden = 1;
		}
		let child = locals[cdt][cdn];
		if (child.journal_entry_id != null) {
			read_only_nat(frm, true);
		}
		else {
			read_only_nat(frm, false);
		}
	},
	make_journal_entry: function (frm, cdt, cdn) {
		frappe.call({
			method: "front_desk.front_desk.doctype.night_audit_transaction.night_audit_transaction.make_journal_entry",
			args: {
				nat_id: frappe.get_doc(cdt, cdn).name
			},
			callback: (response) => {
				if (response.message) {
					frm.reload_doc();
				}
			}
		})
	}
});

function read_only_nat(frm, flag) {
	console.log(night_audit_id);
	frappe.meta.get_docfield('Night Audit Transaction', 'amount', night_audit_id).read_only = flag;
	frappe.meta.get_docfield('Night Audit Transaction', 'debit_account', night_audit_id).read_only = flag;
	frappe.meta.get_docfield('Night Audit Transaction', 'credit_account', night_audit_id).read_only = flag;
	frm.refresh_field('night_audit_transaction');
}