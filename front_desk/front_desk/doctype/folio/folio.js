// Copyright (c) 2019, PMM and contributors
// For license information, please see license.txt

frappe.ui.form.on('Folio', {
	onload: function (frm) {
		frm.get_field("transaction_detail").grid.only_sortable();
	},
	print_type_selected: function(frm, cdt, cdn) {
		if (frm.doc.__unsaved) {
			frappe.msgprint(__("Folio not saved, Please save the changes before printing."));
		}
		else {
			let w = window.open(frappe.urllib.get_full_url("/printview?"
				+"doctype="+encodeURIComponent("Folio")
				+"&name="+encodeURIComponent(cdn)
				+"&format="+encodeURIComponent("Print by Type")
				+"&no_letterhead=0"
				));
			if (!w) {
				frappe.msgprint(__("Please enable pop-ups")); return;
			}
		}
	},
});
