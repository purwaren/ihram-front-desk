frappe.listview_settings['Hotel Room'] = {
    onload: function(listview) {
        if (frappe.user.has_role('Housekeeping') || frappe.user.has_role('Housekeeping Supervisor')) {
            listview.page.add_action_item(__('Update Status'), function() {
                frappe.confirm(
                    ('You are about to update status of Hotel Rooms ' + listview.get_checked_items(true) + ', are you sure?'),
                    () => {
                        frappe.call({
                            method: "front_desk.front_desk.doctype.hotel_room.hotel_room.upgrade_status",
                            args: {
                                room_name_list: listview.get_checked_items(true)
                            },
                            callback: (response) => {
                                cur_list.refresh();
                                frappe.msgprint(("Hotel Rooms ") + listview.get_checked_items(true) + (" status updated."));
                            }
                        });
                    }
                );
            });
            listview.page.add_action_item(__('Clear Door Status'), function() {
                frappe.confirm(
                    ('You are about to clear Door Status of room(s) ' + listview.get_checked_items(true) + ', are you sure?'),
                    () => {
                        frappe.call({
                            method: "front_desk.front_desk.doctype.hotel_room.hotel_room.change_cleaning_status",
                            args: {
                                room_list: listview.get_checked_items(true),
                                to_status: 'No Status'
                            },
                            callback: (response) => {
                                cur_list.refresh();
                                frappe.msgprint(("Hotel Rooms ") + listview.get_checked_items(true) + (" door status cleared."));
                            }
                        });
                    }
                );
            });
            listview.page.add_action_item(__('Do Not Disturb'), function() {
                frappe.confirm(
                    ('You are about to update Door Status of room(s) ' + listview.get_checked_items(true) + ', are you sure?'),
                    () => {
                        frappe.call({
                            method: "front_desk.front_desk.doctype.hotel_room.hotel_room.change_cleaning_status",
                            args: {
                                room_list: listview.get_checked_items(true),
                                to_status: 'Do Not Disturb'
                            },
                            callback: (response) => {
                                cur_list.refresh();
                                frappe.msgprint(("Hotel Rooms ") + listview.get_checked_items(true) + (" door status updated."));
                            }
                        });
                    }
                );
            });
            listview.page.add_action_item(__('Double Lock'), function() {
                frappe.confirm(
                    ('You are about to update Door Status of room(s) ' + listview.get_checked_items(true) + ', are you sure?'),
                    () => {
                        frappe.call({
                            method: "front_desk.front_desk.doctype.hotel_room.hotel_room.change_cleaning_status",
                            args: {
                                room_list: listview.get_checked_items(true),
                                to_status: 'Double Lock'
                            },
                            callback: (response) => {
                                cur_list.refresh();
                                frappe.msgprint(("Hotel Rooms ") + listview.get_checked_items(true) + (" door status updated."));
                            }
                        });
                    }
                );
            });
            listview.page.add_action_item(__('Sleeping Out'), function() {
                frappe.confirm(
                    ('You are about to update Door Status of room(s) ' + listview.get_checked_items(true) + ', are you sure?'),
                    () => {
                        frappe.call({
                            method: "front_desk.front_desk.doctype.hotel_room.hotel_room.change_cleaning_status",
                            args: {
                                room_list: listview.get_checked_items(true),
                                to_status: 'Sleeping Out'
                            },
                            callback: (response) => {
                                cur_list.refresh();
                                frappe.msgprint(("Hotel Rooms ") + listview.get_checked_items(true) + (" door status updated."));
                            }
                        });
                    }
                );
            });
        }
    }
}