// Copyright (c) 2019, PMM and contributors
// For license information, please see license.txt

frappe.ui.form.on('Room Availability Page', {
	search_button: function(frm, cdt, cdn) {
		var doc = locals[cdt][cdn];

		if (doc.start != undefined && doc.end != undefined) {
			var wrapper = frm.get_field('html').$wrapper;
			
			var html =	'<div id="room-calendar">\
							<table class="form-grid" id="table-calendar">\
								<tr class="grid-heading-row" id="table-calendar-title">\
									<th class="grid-static-col">Room Number</th>\
									<th class="grid-static-col">Room Type</th>\
									<th class="grid-static-col">Bed Type</th>\
									<th class="grid-static-col">Smoking</th>\
									<th class="grid-static-col">Room View</th>\
									<th class="grid-static-col">Room Status</th>\
								</tr>\
							</table>\
						</div>';
			
			var css = 	'<style>\
							#room-calendar {\
								font-size:12px;\
								height:300px;\
								overflow-y:scroll;\
							}\
						</style>';

			wrapper.html(html+css);
			
			var start = new Date(doc.start);
			var	end = new Date(doc.end);

			if (start > end) {
				frappe.msgprint(__("Start > End")); return;
			}

			while (start <= end) {
				var th = document.createElement('th');
				th.className = 'grid-static-col';
				th.innerHTML = formatDate(start);
				document.getElementById('table-calendar-title').appendChild(th);
			
				start.setDate(start.getDate() + 1);
			}

			frappe.call({
				method: 'front_desk.front_desk.doctype.hotel_room.hotel_room.get_all_hotel_room',
				callback: (resp) => {
					resp.message.forEach(elm => {
						var tr = document.createElement('tr');
						
						var td = document.createElement('td');
						td.className = 'grid-static-col';
						td.innerHTML = elm.name;
						tr.appendChild(td);

						var td = document.createElement('td');
						td.className = 'grid-static-col';
						td.innerHTML = elm.room_type;
						tr.appendChild(td);

						var td = document.createElement('td');
						td.className = 'grid-static-col';
						td.innerHTML = elm.bed_type;
						tr.appendChild(td);

						var td = document.createElement('td');
						td.className = 'grid-static-col';
						td.innerHTML = elm.allow_smoke;
						tr.appendChild(td);

						var td = document.createElement('td');
						td.className = 'grid-static-col';
						td.innerHTML = elm.view;
						tr.appendChild(td);

						var td = document.createElement('td');
						td.className = 'grid-static-col';
						td.innerHTML = elm.room_status;
						tr.appendChild(td);

						var start = new Date(doc.start);
						var	end = new Date(doc.end);

						
						var loop = function(start, end) {
							get_availability(start, function(){
								start.setDate(start.getDate() + 1);
								if (start <= end) {
									loop(start, end);
								}
							})
						}

						function get_availability(start, fun) {
							frappe.call({
								method: 'front_desk.front_desk.doctype.room_availability_page.room_availability_page.get_room_availability',
								args: {
									room_id: elm.name,
									date: formatDate(start)
								},
								callback: (resp) => {
									var td = document.createElement('td');
									td.className = 'grid-static-col';
									if (resp.message.length > 0) {
										td.innerHTML = resp.message;
									}
									tr.appendChild(td);

									fun();
								}
							});
						}

						loop(start, end);

						document.getElementById('table-calendar').appendChild(tr);
					});
				}
			});

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