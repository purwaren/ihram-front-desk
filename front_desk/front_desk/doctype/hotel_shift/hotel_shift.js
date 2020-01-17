// Copyright (c) 2020, PMM and contributors
// For license information, please see license.txt
var total_cash_count = 0;
var total_cash_qty = 0;
var total_payment = 0;
var total_refund = 0;

frappe.ui.form.on('Hotel Shift', {
	onload_post_render: function(frm) {
		if (frm.doc.__islocal == 1) {
			cur_frm.set_df_property('section_break_3', 'hidden', 1);
		}
	},
	onload: function(frm) {
		frm.set_df_property('total_cash_qty', 'hidden', 0);
		frm.get_field('cc_detail').grid.cannot_add_rows = true;
		frm.get_field('payment_detail').grid.cannot_add_rows = true;
		frm.get_field('refund_detail').grid.cannot_add_rows = true;
		// if islocal == 1
		// 	if is_there_open_shift == true
		// 		forbid to create new shift
		// 		redirect to hotel shift list page
		// 	else if there_open_shift == false
		// 		get_transaction(null)
		// else if islocal == 0
		// 	if doc.status == 'Open'
		// 		get_transaction(id)
		// 	else if doc.status == 'Closed'
		// 		set all field read only
		// 		hide save button
		if (frm.doc.__islocal == 1) {
			frappe.call({
				method: "front_desk.front_desk.doctype.hotel_shift.hotel_shift.is_there_open_hotel_shift",
				callback: (response) => {
					if (response.message) {
						if (response.message == 1) {
							frappe.set_route("List", "Hotel Shift");
							frappe.msgprint('A Shift already Opened. Please close it first before creating new one.');
						} else {
							frappe.call({
								method: "front_desk.front_desk.doctype.hotel_shift.hotel_shift.populate_cash_count",
								callback: (response) => {
									if (response.message) {
										var cc_nominal = response.message;
										frm.set_value('cc_detail', []);
										for (var i = 0; i < cc_nominal.length; i++) {
											var item = frm.add_child('cc_detail');
											item.nominal = cc_nominal[i];
											item.qty = 0;
											item.amount = 0;
										}
									}
									frm.refresh_field('cc_detail');
								}
							});
							frappe.call({
								method: "front_desk.front_desk.doctype.hotel_shift.hotel_shift.populate_cr_payment",
								args: {
									hotel_shift_id: null,
									selector: 'recap',
								},
								callback: (response) => {
									if (response.message) {
										frm.set_value('payment_detail', []);
										total_payment = 0;
										$.each(response.message, function (i, d) {
											let item = frm.add_child('payment_detail');
											item.mode_of_payment = d.mode_of_payment;
											item.amount = d.amount;
											total_payment += d.amount;
										});
										frm.set_value('total_payment', total_payment);
									}
									frm.refresh_field('payment_detail');

									frappe.call({
										method: "front_desk.front_desk.doctype.hotel_shift.hotel_shift.populate_cr_refund",
										args: {
											hotel_shift_id: null,
											selector: 'recap',
										},
										callback: (response) => {
											if (response.message) {
												frm.set_value('refund_detail', []);
												total_refund = 0;
												$.each(response.message, function (i, d) {
													let item = frm.add_child('refund_detail');
													item.type = d.type;
													item.amount = d.amount;
													total_refund += d.amount;
												});
												frm.set_value('total_refund', total_refund);
												frm.set_value('balance', total_payment);
											}
											frm.refresh_field('refund_detail');
										}
									});
								}
							});

							//second call for populate transaction details
							frappe.call({
								method: "front_desk.front_desk.doctype.hotel_shift.hotel_shift.populate_cr_payment",
								args: {
									hotel_shift_id: null,
									selector: 'detail',
								},
								callback: (response) => {
									if (response.message) {
										frm.set_value('cr_payment_transaction', []);
										$.each(response.message, function (i, d) {
											let item = frm.add_child('cr_payment_transaction');
											item.type = d.type;
											item.trx_id = d.trx_id;
											item.reservation_id = d.reservation_id;
											item.folio_id = d.folio_id;
											item.customer_id = d.customer_id;
											item.account = d.account;
											item.amount = d.amount;
											item.user = d.user;
										});
									}
									frm.refresh_field('cr_payment_transaction');

									frappe.call({
										method: "front_desk.front_desk.doctype.hotel_shift.hotel_shift.populate_cr_refund",
										args: {
											hotel_shift_id: null,
											selector: 'detail',
										},
										callback: (response) => {
											if (response.message) {
												frm.set_value('cr_refund_transaction', []);
												$.each(response.message, function (i, d) {
													let item = frm.add_child('cr_refund_transaction');
													item.type = d.type;
													item.trx_id = d.trx_id;
													item.reservation_id = d.reservation_id;
													item.folio_id = d.folio_id;
													item.customer_id = d.customer_id;
													item.account = d.account;
													item.amount = d.amount;
													item.user = d.user;
												});
											}
											frm.refresh_field('cr_refund_transaction');
										}
									});
								}
							});

							frappe.call({
								method: "front_desk.front_desk.doctype.hotel_shift.hotel_shift.get_cash_balance",
								args: {
									hotel_shift_id: null,
								},
								callback: (response) => {
									if (response.message) {
										frm.set_value('cash_balance', response.message);
									}
								}
							});
						}
					}
				}
			});
		}
		else {
			if (frm.doc.status == 'Open') {
				frappe.call({
					method: "front_desk.front_desk.doctype.hotel_shift.hotel_shift.populate_cr_payment",
					args: {
						hotel_shift_id: frm.doc.name,
						selector: 'recap',
					},
					callback: (response) => {
						if (response.message) {
							frm.set_value('payment_detail', []);
							$.each(response.message, function (i, d) {
								let item = frm.add_child('payment_detail');
								item.mode_of_payment = d.mode_of_payment;
								item.amount = d.amount;
								total_payment += d.amount;
							});
							frm.set_value('total_payment', total_payment);
						}
						frm.refresh_field('payment_detail');

						frappe.call({
							method: "front_desk.front_desk.doctype.hotel_shift.hotel_shift.populate_cr_refund",
							args: {
								hotel_shift_id: frm.doc.name,
								selector: 'recap',
							},
							callback: (response) => {
								if (response.message) {
									frm.set_value('refund_detail', []);
									$.each(response.message, function (i, d) {
										let item = frm.add_child('refund_detail');
										item.type = d.type;
										item.amount = d.amount;
										total_refund += d.amount;
									});
									frm.set_value('total_refund', total_refund);
									frm.set_value('balance', total_payment);
								}
								frm.refresh_field('refund_detail');
							}
						});
					}
				});

				//second call for populate transaction details
				frappe.call({
					method: "front_desk.front_desk.doctype.hotel_shift.hotel_shift.populate_cr_payment",
					args: {
						hotel_shift_id: frm.doc.name,
						selector: 'detail',
					},
					callback: (response) => {
						if (response.message) {
							frm.set_value('cr_payment_transaction', []);
							$.each(response.message, function (i, d) {
								let item = frm.add_child('cr_payment_transaction');
								item.type = d.type;
								item.trx_id = d.trx_id;
								item.reservation_id = d.reservation_id;
								item.folio_id = d.folio_id;
								item.customer_id = d.customer_id;
								item.account = d.account;
								item.amount = d.amount;
								item.user = d.user;
							});
						}
						frm.refresh_field('cr_payment_transaction');

						frappe.call({
							method: "front_desk.front_desk.doctype.hotel_shift.hotel_shift.populate_cr_refund",
							args: {
								hotel_shift_id: frm.doc.name,
								selector: 'detail',
							},
							callback: (response) => {
								if (response.message) {
									frm.set_value('cr_refund_transaction', []);
									$.each(response.message, function (i, d) {
										let item = frm.add_child('cr_refund_transaction');
										item.type = d.type;
										item.trx_id = d.trx_id;
										item.reservation_id = d.reservation_id;
										item.folio_id = d.folio_id;
										item.customer_id = d.customer_id;
										item.account = d.account;
										item.amount = d.amount;
										item.user = d.user;
									});
								}
								frm.refresh_field('cr_refund_transaction');
							}
						});
					}
				});

				frappe.call({
					method: "front_desk.front_desk.doctype.hotel_shift.hotel_shift.get_cash_balance",
					args: {
						hotel_shift_id: frm.doc.name,
					},
					callback: (response) => {
						if (response.message) {
							frm.set_value('cash_balance', response.message);
						}
					}
				});
			}
			else {
				set_all_read_only();
				frm.disable_save();
			}
		}
	},
	print_cash_remittance: function(frm, cdt, cdn) {
		if (frm.doc.__unsaved) {
			frappe.msgprint("Please save the document changes first, before printing report");
		}
		else {
			let w = window.open(frappe.urllib.get_full_url("/printview?"
				+"doctype="+encodeURIComponent("Hotel Shift")
				+"&name="+encodeURIComponent(cdn)
				+"&format="+encodeURIComponent("Cash Remittance")
				+"&no_letterhead=0"
				));

			if (!w) {
				frappe.msgprint(__("Please enable pop-ups")); return;
			}
		}


	},
	print_cashier_report: function(frm, cdt, cdn) {
		if (frm.doc.__unsaved) {
			frappe.msgprint("Please save the document changes first, before printing report");
		}
		else {
			let w = window.open(frappe.urllib.get_full_url("/printview?"
				+"doctype="+encodeURIComponent("Hotel Shift")
				+"&name="+encodeURIComponent(cdn)
				+"&format="+encodeURIComponent("Cashier Report")
				+"&no_letterhead=0"
				));

			if (!w) {
				frappe.msgprint(__("Please enable pop-ups")); return;
			}
		}

	},
	close_shift: function (frm) {
		frappe.confirm(__("You are about to close the shift. Are you sure?"), function() {
			frappe.call({
				method: "front_desk.front_desk.doctype.hotel_shift.hotel_shift.close_shift",
				args: {
					hotel_shift_id: frm.doc.name,
				},
				callback: (r) => {
					if (r.message) {
						frappe.show_alert(__("Shift Closed."));
						frm.reload_doc();
					}
				}
			});
		});
	}
});

frappe.ui.form.on('CC Detail',{
	qty: function (frm, cdt, cdn) {
		let child = locals[cdt][cdn];
		child.amount = child.nominal*child.qty;
		frm.refresh_field('cc_detail');

		let cc_detail_list = frm.doc.cc_detail;
		total_cash_count = 0;
		total_cash_qty = 0;
		for (var i = 0; i < cc_detail_list.length; i++) {
			total_cash_count += cc_detail_list[i].amount;
			total_cash_qty += parseInt(cc_detail_list[i].qty, 10);
		}
		frm.set_value('total_cash_count', total_cash_count);
		frm.set_value('total_cash_qty', total_cash_qty);
	}
});

function set_all_read_only() {
	cur_frm.set_df_property('employee', 'read_only', 1);
	cur_frm.set_df_property('close_shift', 'hidden', 1);
	cur_frm.get_field("cc_detail").grid.only_sortable();
	cur_frm.get_field("payment_detail").grid.only_sortable();
	cur_frm.get_field("refund_detail").grid.only_sortable();
	frappe.meta.get_docfield('CC Detail', 'qty', cur_frm.docname).read_only = true;
}