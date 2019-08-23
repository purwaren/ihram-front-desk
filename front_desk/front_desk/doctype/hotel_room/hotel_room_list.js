frappe.listview_settings['Hotel Room'] = {
    onload: function(listview) {
        if (frappe.user.has_role('Housekeeping') || frappe.user.has_role('Housekeeping Supervisor')) {
            listview.page.add_action_item(__('Update Status'), function() {
                frappe.confirm(
                    ('You are about to update status Hotel Rooms ' + listview.get_checked_items(true) + ', are you sure?'),
                    () => {
                        frappe.call({
                            method: "front_desk.front_desk.doctype.hotel_room.hotel_room.upgrade_status",
                            args: {
                                room_name_list: listview.get_checked_items(true)
                            },
                            callback: (response) => {
                                frappe.msgprint(("Hotel Rooms ") + listview.get_checked_items(true) + (" status updated."));
                            }
                        });
                    }
                );
            });
        }
    }
}