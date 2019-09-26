// Copyright (c) 2019, PMM and contributors
// For license information, please see license.txt
var bill_breakdown = null;
var breakdown_shown = false;
var outstanding_now = 0;
var deposit = 0;

frappe.ui.form.on('Hotel Bill', {
	onload: function(frm) {
		frm.get_field("bill_breakdown").grid.only_sortable();
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
		outstanding_now = frm.doc.bill_outstanding_amount;
		deposit = frm.doc.bill_deposit_amount;
		if (frm.doc.use_deposit == 1) {
			if (deposit <= frm.doc.bill_grand_total) {
				frm.set_value('bill_outstanding_amount', frm.doc.bill_grand_total - deposit);
				frm.set_value('bill_change_amount', 0);
			}
			else {
				frm.set_value('bill_outstanding_amount', 0);
				frm.set_value('bill_change_amount', deposit - frm.doc.bill_grand_total);

			}
		} else {
			frm.set_value('bill_outstanding_amount', frm.doc.bill_grand_total);
			frm.set_value('bill_change_amount', deposit);
		}
	},
	after_save: function (frm) {
		frm.reload_doc()
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


