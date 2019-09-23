// Copyright (c) 2019, PMM and contributors
// For license information, please see license.txt

frappe.ui.form.on('Hotel Bill', {
	onload: function(frm) {
		frm.get_field("bill_breakdown").grid.only_sortable();
	}
});
