// Copyright (c) 2019, PMM and contributors
// For license information, please see license.txt

frappe.ui.form.on('Room Rate', {
	refresh: function(frm, cdt, cdn) {
		room_rate = frappe.get_doc(cdt, cdn);
		if (room_rate.__islocal == 1) {
			frm.set_df_property('rate', 'hidden', 1);
		}
		else {

		}
	}
});
