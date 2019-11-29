// Copyright (c) 2019, PMM and contributors
// For license information, please see license.txt

frappe.ui.form.on('Room Rate', {
	refresh: function(frm, cdt, cdn) {
		if (frm.doc.__islocal == 1) {
			frm.set_value('room_rate_breakdown', []);

		let weekend = frm.add_child('room_rate_breakdown');
		weekend.breakdown_name = 'Weekend Rate';
		weekend.breakdown_qty = 1;

		let weekday = frm.add_child('room_rate_breakdown');
		weekday.breakdown_name = 'Weekday Rate';
		weekday.breakdown_qty = 1;

		frm.refresh_field('room_rate_breakdown');
		}
	}
});
