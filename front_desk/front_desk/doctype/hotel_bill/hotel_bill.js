// Copyright (c) 2019, PMM and contributors
// For license information, please see license.txt
var bill_breakdown = null;
var breakdown_shown = false;
frappe.ui.form.on('Hotel Bill', {
	onload: function(frm) {
		frm.get_field("bill_breakdown").grid.only_sortable();
	},
	refresh: function(frm, cdt, cdn) {
		var x = frappe.get_doc(cdt, cdn).bill_breakdown;
		x.forEach(hideBreakdown);
	},
	onload_post_render: function(frm, cdt, cdn) {
		frm.add_custom_button(__("Toggle Billing Details"), function () {
			bill_breakdown = frappe.get_doc(cdt, cdn).bill_breakdown;
			if (breakdown_shown == false) {
				bill_breakdown.forEach(showBreakdown);
				breakdown_shown = true;
			}
			else {
				bill_breakdown.forEach(hideBreakdown);
				breakdown_shown = false;
			}
		});
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


