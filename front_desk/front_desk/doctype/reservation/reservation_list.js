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
                        window.open(response.message[i], "_blank")
                    }
                }
            });
        });

        listview.page.add_action_item( ('Check Out'), function () {
            const docnames = listview.get_checked_items(true).map(docname => docname.toString());
            frappe.call({
                method: "front_desk.front_desk.doctype.reservation.reservation.check_out",
                args: {
                    reservation_id_list: listview.get_checked_items(true)
                }
            });
        });

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
                }
            );
        });
    }
}