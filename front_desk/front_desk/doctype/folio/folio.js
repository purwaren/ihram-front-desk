// Copyright (c) 2019, PMM and contributors
// For license information, please see license.txt

frappe.ui.form.on('Folio', {
	print_type_selected: function(frm, cdt, cdn) {
		let w = window.open(frappe.urllib.get_full_url("/printview?"
				+"doctype="+encodeURIComponent("Folio")
				+"&name="+encodeURIComponent(cdn)
				+"&format="+encodeURIComponent("Print by Type")
				+"&no_letterhead=0"
				));

			if (!w) {
				frappe.msgprint(__("Please enable pop-ups")); return;
			}

	},
});
