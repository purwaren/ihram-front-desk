frappe.listview_settings['Hotel Shift'] = {
    get_indicator: function(doc) {
        return [__(doc.status), {
            "Open": "green",
            "Closed": "red"
        }[doc.status], "status,=," + doc.status];
	}
}