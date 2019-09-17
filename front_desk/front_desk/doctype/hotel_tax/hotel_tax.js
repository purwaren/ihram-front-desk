// Copyright (c) 2019, PMM and contributors
// For license information, please see license.txt

frappe.ui.form.on('Hotel Tax', {
	refresh: function(frm) {

	}
});

frappe.ui.form.on('Hotel Tax Breakdown', {
	breakdown_type: function (frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		var type = child.breakdown_type;
		var account = " - " + child.breakdown_account;
		if (child.breakdown_account == undefined) {
			var desc = type;
		}
		else {
			var desc = type.concat(account);
		}
		frappe.model.set_value("Hotel Tax Breakdown", child.name, "breakdown_description", desc);
	},
	breakdown_account: function (frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		var type = child.breakdown_type;
		var account = " - " + child.breakdown_account;
		if (child.breakdown_type == '') {
			var desc = child.breakdown_account;
		}
		else {
			var desc = type.concat(account);
		}
		frappe.model.set_value("Hotel Tax Breakdown", child.name, "breakdown_description", desc);
	}
});
