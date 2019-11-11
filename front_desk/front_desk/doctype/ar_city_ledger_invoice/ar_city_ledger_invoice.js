// Copyright (c) 2019, PMM and contributors
// For license information, please see license.txt

frappe.ui.form.on('AR City Ledger Invoice', {
	hotel_order_channel: function(frm) {
		get_folio_by_order_channel(frm);
	}
});

function get_folio_by_order_channel(frm) {
	let field = frm.fields_dict['folio'].grid.fields_map['folio_id'];
	if (frm.doc.hotel_order_channel) {

		frappe.call({
			method: 'front_desk.front_desk.doctype.reservation.reservation.get_all_reservation_by_order_channel',
			args: {
				hotel_order_channel: frm.doc.hotel_order_channel
			},
			callback: (r) => {
				if (r.message) {
					field.get_query = function () {
						return {
							filters: [
								['Folio', 'reservation_id', 'in', r.message],
							],
						}
					}
				}
			}
		});
	}
}