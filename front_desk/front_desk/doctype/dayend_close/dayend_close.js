// Copyright (c) 2020, PMM and contributors
// For license information, please see license.txt
frappe.ui.form.on('Dayend Close', {
	refresh: function (frm) {
		if (frm.doc.is_closed == 1) {
			frm.set_intro(__('This Dayend detail already Closed.'));
		}
	},
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
						else {
							frappe.call({
								method: "front_desk.front_desk.doctype.dayend_close.dayend_close.precheck_dayend_close",
								args: {
									audit_date: frm.doc.audit_date,
								},
								callback: (r) => {
									if (r.message) {
										//Populate Reservation
										if (r.message[0].length > 0) {
											frm.set_value('dayend_reservation',[]);
											for (let i = 0; i < r.message[0].length; i++) {
												let item = frm.add_child('dayend_reservation');
												item.reservation_id = r.message[0][0]['reservation_id'];
												item.description = r.message[0][0]['description'];
											}
										}
										frm.refresh_field('dayend_reservation');
										//Populate Room Stay
										if (r.message[1].length > 0) {
											frm.set_value('dayend_room_stay',[]);
											for (let i = 0; i < r.message[1].length; i++) {
												let item = frm.add_child('dayend_room_stay');
												item.room_stay_id = r.message[1][0]['room_stay_id'];
												item.description = r.message[1][0]['description'];
											}
										}
										frm.refresh_field('dayend_room_stay');
										// Update is_fetched
										frm.set_value('is_fetched', 1);
									}
								}
							})
						}
					}
				}
			})
		}
		else {
			if (frm.doc.is_closed == 1) {
				set_all_read_only();
				frm.disable_save();
			} else {
				frappe.call({
					method: "front_desk.front_desk.doctype.dayend_close.dayend_close.precheck_dayend_close",
					args: {
						audit_date: frm.doc.audit_date,
					},
					callback: (r) => {
						if (r.message) {
							//Populate Reservation
							if (r.message[0].length > 0) {
								frm.set_value('dayend_reservation',[]);
								for (let i = 0; i < r.message[0].length; i++) {
									let item = frm.add_child('dayend_reservation');
									item.reservation_id = r.message[0][0]['reservation_id'];
									item.description = r.message[0][0]['description'];
								}
							}
							frm.refresh_field('dayend_reservation');
							//Populate Room Stay
							if (r.message[1].length > 0) {
								frm.set_value('dayend_room_stay',[]);
								for (let i = 0; i < r.message[1].length; i++) {
									let item = frm.add_child('dayend_room_stay');
									item.room_stay_id = r.message[1][0]['room_stay_id'];
									item.description = r.message[1][0]['description'];
								}
							}
							frm.refresh_field('dayend_room_stay');

							if (frm.doc.is_fetched == 0){
								frappe.db.set_value(cdt, cdn, 'is_fetched', 1);
							}
						}
					}
				})
			}
		}
	},
	precheck_dayend_close: function (frm, cdt, cdn) {
		frappe.call({
			method: "front_desk.front_desk.doctype.dayend_close.dayend_close.precheck_dayend_close",
			args: {
				audit_date: frm.doc.audit_date,
			},
			callback: (r) => {
				if (r.message) {
					//Populate Reservation
					if (r.message[0].length == 0 && r.message[1].length == 0) {
						frappe.msgprint("No Reservation or Room Stay Needed to be handled.")
						frm.set_value('dayend_reservation',[]);
						frm.set_value('dayend_room_stay',[]);
					}
					if (r.message[0].length > 0) {
						frm.set_value('dayend_reservation',[]);
						for (let i = 0; i < r.message[0].length; i++) {
							let item = frm.add_child('dayend_reservation');
							item.reservation_id = r.message[0][0]['reservation_id'];
							item.description = r.message[0][0]['description'];
						}
					}
					frm.refresh_field('dayend_reservation');
					//Populate Room Stay
					if (r.message[1].length > 0) {
						frm.set_value('dayend_room_stay',[]);
						for (let i = 0; i < r.message[1].length; i++) {
							let item = frm.add_child('dayend_room_stay');
							item.room_stay_id = r.message[1][0]['room_stay_id'];
							item.description = r.message[1][0]['description'];
						}
					}
					frm.refresh_field('dayend_room_stay');
					// Update is_fetched
					if (frm.doc.__islocal == 1) {
						frm.set_value('is_fetched', 1);
					}
					else if (frm.doc.is_fetched == 0){
						frappe.db.set_value(cdt, cdn, 'is_fetched', 1);
					}
				}
			}
		})
	},
	proceed_dayend_close: function (frm, cdt, cdn) {
		if (frm.doc.__unsaved != undefined && frm.doc.__unsaved == 1) {
			frappe.msgprint("The Details has been modified, please click Save first, before proceeding to close.");
		}
		else if (frm.doc.dayend_room_stay.length > 0 || frm.doc.dayend_reservation.length > 0) {
			frappe.msgprint("There are Reservation or Room Stay need to be resolved first.");
		}
		else if (frm.doc.is_closed == 1) {
			frappe.msgprint("Dayend already Closed.");
		}
		else if (frm.doc.is_fetched == 0) {
			frappe.msgprint("Details never been fetched. Please fetch the details first.");
		}
		else {
			frappe.call({
				method: "front_desk.front_desk.doctype.dayend_close.dayend_close.proceed_dayend_close",
				args: {
					dayend_close_id: frm.doc.name,
				},
				callback: (r) => {
					if (r.message) {
						if (r.message == 1) {
							frm.set_intro(__('This Dayend detail already Closed.'));
							frm.reload_doc();
						}
					}
				}
			})
		}
	}
});

frappe.ui.form.on('Dayend Reservation', {
	check_in: function (frm, cdt, cdn) {
		let child = locals[cdt][cdn];
		frappe.call({
			method: "front_desk.front_desk.doctype.dayend_close.dayend_close.get_reservation_url",
			args: {
				reservation_id: child.reservation_id,
			},
			callback: (r) => {
				if (r.message) {
					let w = window.open(r.message, '_blank');
					if (!w) {
						frappe.msgprint(__("Please enable pop-ups")); return;
					}
				}
			}
		})
	},
	update_arrival: function (frm, cdt, cdn) {
		let child = locals[cdt][cdn];
		frappe.call({
			method: "front_desk.front_desk.doctype.dayend_close.dayend_close.get_reservation_url",
			args: {
				reservation_id: child.reservation_id,
			},
			callback: (r) => {
				if (r.message) {
					let w = window.open(r.message, '_blank');
					if (!w) {
						frappe.msgprint(__("Please enable pop-ups")); return;
					}
				}
			}
		})
	}
});

frappe.ui.form.on('Dayend Room Stay', {
	check_out: function (frm, cdt, cdn) {
		let child = locals[cdt][cdn];
		frappe.call({
			method: "front_desk.front_desk.doctype.dayend_close.dayend_close.get_room_stay_url",
			args: {
				room_stay_id: child.room_stay_id,
			},
			callback: (r) => {
				if (r.message) {
					let w = window.open(r.message, '_blank');
					if (!w) {
						frappe.msgprint(__("Please enable pop-ups")); return;
					}
				}
			}
		})
	},
	extend: function (frm, cdt, cdn) {
		let child = locals[cdt][cdn];
		frappe.call({
			method: "front_desk.front_desk.doctype.dayend_close.dayend_close.get_room_stay_url",
			args: {
				room_stay_id: child.room_stay_id,
			},
			callback: (r) => {
				if (r.message) {
					let w = window.open(r.message, '_blank');
					if (!w) {
						frappe.msgprint(__("Please enable pop-ups")); return;
					}
				}
			}
		})
	}
});

function set_all_read_only() {
		cur_frm.set_df_property('precheck_dayend_close', 'hidden', 1);
		cur_frm.set_df_property('proceed_dayend_close', 'hidden', 1);
}