frappe.listview_settings['Reservation'] = {
    onload: function(listview) {
        listview.page.add_action_item(__('Check In'), function() {
            frappe.call({
                method: "front_desk.front_desk.doctype.room_stay.room_stay.create_room_stay",
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
    }
}