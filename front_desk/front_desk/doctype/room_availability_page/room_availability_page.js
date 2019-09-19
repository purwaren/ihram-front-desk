// Copyright (c) 2019, PMM and contributors
// For license information, please see license.txt

frappe.ui.form.on('Room Availability Page', {
	refresh: function(frm, cdt, cdn) {
		var doc = locals[cdt][cdn];

		// doc.start = undefined;
		// frm.refresh_field('start');
		
		// doc.end = undefined;
		// frm.refresh_field('end');
	},
	start: function(frm, cdt, cdn) {
		var doc = locals[cdt][cdn];
	},
	end: function(frm, cdt, cdn) {
		var doc = locals[cdt][cdn];
	},
	search_button: function(frm, cdt, cdn) {
		var doc = locals[cdt][cdn];

		if (doc.start != undefined && doc.end != undefined) {
			var wrapper = frm.get_field('html').$wrapper;
			var html = '<div id="table-calendar"><table class="table table-bordered"><tr id="table-calendar-title"><th width="100px">Room Number</th><th width="100px">Room Type</th><th width="100px">Bed Type</th><th width="100px">Smoking</th><th width="100px">Room View</th><th width="100px">Room Status</th></tr></table></div>';
			var css = '<style>#table-calendar {font-size:12px; height:500px; overflow-y:scroll;}</style>';

			wrapper.html(html+css);
			
			var start = new Date(doc.start);
			var	end = new Date(doc.end);
			var today = new Date(formatDate(new Date()));

			if (start < today) {
				frappe.msgprint(__("Start < Today")); return;
			}

			if (start > end) {
				frappe.msgprint(__("Start > End")); return;
			}

			while (start <= end) {
				var z = document.createElement('th');
				z.innerHTML = formatDate(start);
				z.style.cssText = 'width:100px;'
				document.getElementById('table-calendar-title').appendChild(z);
			
				start.setDate(start.getDate() + 1);
			}
		} else {
			console.log('...');
		}
	}
});

function formatDate(date) {
    var d = new Date(date),
        month = '' + (d.getMonth() + 1),
        day = '' + d.getDate(),
        year = d.getFullYear();

    if (month.length < 2) 
        month = '0' + month;
    if (day.length < 2) 
        day = '0' + day;

    return [year, month, day].join('-');
}