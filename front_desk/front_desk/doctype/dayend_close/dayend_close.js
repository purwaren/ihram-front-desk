// Copyright (c) 2020, PMM and contributors
// For license information, please see license.txt

frappe.ui.form.on('Dayend Close', {
	onload: function(frm) {
		if (frm.doc.__islocal == 1) {
			frappe.call({
				method: "front_desk.front_desk.doctype.dayend_close.dayend_close.is_there_open_dayend_close",
				callback: (r) => {
					if (r.message) {
						if (r.message == 1) {
							frappe.set_route("List", "Dayend Close");
							frappe.msgprint('Cannot Create new Dayend Close, Please proceed previous Dayend Close first.');
						}
					}
				}
			})
		}
	}
});
