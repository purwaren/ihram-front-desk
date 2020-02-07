// Copyright (c) 2020, PMM and contributors
// For license information, please see license.txt

frappe.ui.form.on('Dayend Close', {
	onload: function(frm) {
		frm.get_field("dayend_reservation").grid.only_sortable();
		frm.get_field("dayend_room_stay").grid.only_sortable();
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
	},
	precheck_dayend_close: function (frm) {
		frappe.call({
			method: "front_desk.front_desk.doctype.dayend_close.dayend_close.precheck_dayend_close",
			args: {
				audit_date: frm.doc.audit_date,
			},
			callback: (r) => {
				if (r.message) {
					if (r.message[0].length > 0) {
						frm.set_value('dayend_reservation',[]);
						for (let i = 0; i < r.message[0].length; i++) {
							let item = frm.add_child('dayend_reservation');
							item.reservation_id = r.message[0][0]['reservation_id'];
							item.description = r.message[0][0]['description'];
						}
					}
					frm.refresh_field('dayend_reservation');
					if (r.message[1].length > 0) {
						frm.set_value('dayend_room_stay',[]);
						for (let i = 0; i < r.message[1].length; i++) {
							let item = frm.add_child('dayend_room_stay');
							item.reservation_id = r.message[1][0]['room_stay_id'];
							item.description = r.message[1][0]['description'];
						}
					}
					frm.refresh_field('dayend_room_stay');
				}
			}
		})
	}
});
