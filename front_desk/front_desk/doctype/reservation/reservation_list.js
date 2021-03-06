frappe.listview_settings['Reservation'] = {
    onload: function(listview) {
        listview.page.add_action_item(__('Check In'), function() {
            frappe.call({
                method: "front_desk.front_desk.doctype.reservation.reservation.check_in",
                args: {
                    reservation_id_list: listview.get_checked_items(true)
                },
                callback: (response) => {
                    console.log(response)
                    for (let i = 0; i < response.message.length; i++){
                        var w = window.open(response.message[i], "_blank");
                        if (!w) {
                            frappe.msgprint(__("Please enable pop-ups")); return;
                        }
                    }
                }
            });
        });

        // listview.page.add_action_item( ('Check Out'), function () {
        //     frappe.call({
        //         method: "front_desk.front_desk.doctype.reservation.reservation.check_out",
        //         args: {
        //             reservation_id_list: listview.get_checked_items(true)
        //         }
        //     });
        // });

        listview.page.add_action_item( ('Cancel'), function () {
            frappe.confirm(
                ("You are about to cancel this Reservation, are you sure?"),
                () => {
                    frappe.call({
                        method: "front_desk.front_desk.doctype.reservation.reservation.cancel",
                        args: {
                            reservation_id_list: listview.get_checked_items(true)
                        }
                    });
                    frappe.msgprint("Reservation Canceled");
                }
            );
        });
    },
    get_indicator: function(doc) {
        return [__(doc.status), {
            "Reserved": "orange",
            "Confirmed": "green",
            "In House": "green",
            "Finish": "blue",
            "Cancel": "red"
        }[doc.status], "status,=," + doc.status];
	}
}