// Copyright (c) 2019, PMM and contributors
// For license information, please see license.txt

frappe.ui.form.on("Hotel Room", {
	refresh: function(frm, cdt, cdn) {
		var hotel_room = frappe.model.get_doc(cdt, cdn);
	
		if (hotel_room.room_type != undefined) {
			var wrapper = frm.get_field("preview_html").$wrapper;

			var head = '' +
				'<head>\
					<meta name="viewport" content="width=device-width, initial-scale=1">\
					<style>\
						* {box-sizing: border-box}\
						body {font-family: Verdana, sans-serif; margin:0}\
						img {vertical-align: middle;}\
						/* Slideshow container */.slideshow-container {max-width: 1000px;position: relative;margin: auto;}\
						/* Next & previous buttons */.prev, .next {cursor: pointer;position: absolute;top: 50%;width: auto;padding: 16px;margin-top: -22px;color: white;font-weight: bold;font-size: 18px;transition: 0.6s ease;border-radius: 0 3px 3px 0;user-select: none;}\
						/* Position the "next button" to the right */.next {right: 0;border-radius: 3px 0 0 3px;}\
						/* On hover, add a black background color with a little bit see-through */.prev:hover, .next:hover {background-color: rgba(0,0,0,0.8);}\
						/* The dots/bullets/indicators */.dot {cursor: pointer;height: 15px;width: 15px;margin: 0 2px;background-color: #bbb;border-radius: 50%;display: inline-block;transition: background-color 0.6s ease;}.active, .dot:hover {background-color: #717171;}\
					</style>\
				</head>'
			
			var script = '' +
				'<script>\
				var slideIndex = 1;\
				showSlides(slideIndex);\
				\
				function plusSlides(n) {\
					showSlides(slideIndex += n);\
				}\
				\
				function currentSlide(n) {\
					showSlides(slideIndex = n);\
				}\
				\
				function showSlides(n) {\
					var i;\
					var slides = document.getElementsByClassName("mySlides");\
					var dots = document.getElementsByClassName("dot");\
					if (n > slides.length) {\
						slideIndex = 1\
					}\
					if (n < 1) {\
						slideIndex = slides.length\
					}\
					for (i = 0; i < slides.length; i++) {\
						slides[i].style.display = "none";\
					}\
					for (i = 0; i < dots.length; i++) {\
						dots[i].className = dots[i].className.replace(" active", "");\
					}\
					if (slides.length > 0) {\
						slides[slideIndex-1].style.display = "block";\
					}\
					if (dots.length > 0) {\
						dots[slideIndex-1].className += " active";\
					}\
				}\
				</script>'
			
			var html = '<html>' + head + '<body><div class="slideshow-container">';
			
			frappe.call({
				method: "front_desk.front_desk.doctype.hotel_room.hotel_room.get_images",
				args: {
					room_type: hotel_room.room_type
				},
				callback: (response) => {
					if (response.message != undefined) {
						for (let i = 0; i < response.message.length; i++) {
							var is_viewable = frappe.utils.is_image_file(response.message[i].file_url);
							if (is_viewable) {
								html = html + '<div class="mySlides"><img src="' + response.message[i].file_url + '" style="width:100%"></div>'
							}
						}

						html = html + '<a class="prev" onclick="plusSlides(-1)">&#10094;</a><a class="next" onclick="plusSlides(1)">&#10095;</a></div>' + script + '</body></html>';
						wrapper.html(html);
						frm.toggle_display("preview_html", true);
					}
					else {
						frm.toggle_display("preview_html", false);
					}
				}
			});	
		} else {
			frm.toggle_display("preview_html", false);
		}
	},
	room_type: function(frm, cdt, cdn) {
		var hotel_room = frappe.model.get_doc(cdt, cdn);
	
		if (hotel_room.room_type != undefined) {
			var wrapper = frm.get_field("preview_html").$wrapper;

			var head = '' +
				'<head>\
					<meta name="viewport" content="width=device-width, initial-scale=1">\
					<style>\
						* {box-sizing: border-box}\
						body {font-family: Verdana, sans-serif; margin:0}\
						img {vertical-align: middle;}\
						/* Slideshow container */.slideshow-container {max-width: 1000px;position: relative;margin: auto;}\
						/* Next & previous buttons */.prev, .next {cursor: pointer;position: absolute;top: 50%;width: auto;padding: 16px;margin-top: -22px;color: white;font-weight: bold;font-size: 18px;transition: 0.6s ease;border-radius: 0 3px 3px 0;user-select: none;}\
						/* Position the "next button" to the right */.next {right: 0;border-radius: 3px 0 0 3px;}\
						/* On hover, add a black background color with a little bit see-through */.prev:hover, .next:hover {background-color: rgba(0,0,0,0.8);}\
						/* The dots/bullets/indicators */.dot {cursor: pointer;height: 15px;width: 15px;margin: 0 2px;background-color: #bbb;border-radius: 50%;display: inline-block;transition: background-color 0.6s ease;}.active, .dot:hover {background-color: #717171;}\
					</style>\
				</head>'
			
			var script = '' +
				'<script>\
				var slideIndex = 1;\
				showSlides(slideIndex);\
				\
				function plusSlides(n) {\
					showSlides(slideIndex += n);\
				}\
				\
				function currentSlide(n) {\
					showSlides(slideIndex = n);\
				}\
				\
				function showSlides(n) {\
					var i;\
					var slides = document.getElementsByClassName("mySlides");\
					var dots = document.getElementsByClassName("dot");\
					if (n > slides.length) {\
						slideIndex = 1\
					}\
					if (n < 1) {\
						slideIndex = slides.length\
					}\
					for (i = 0; i < slides.length; i++) {\
						slides[i].style.display = "none";\
					}\
					for (i = 0; i < dots.length; i++) {\
						dots[i].className = dots[i].className.replace(" active", "");\
					}\
					if (slides.length > 0) {\
						slides[slideIndex-1].style.display = "block";\
					}\
					if (dots.length > 0) {\
						dots[slideIndex-1].className += " active";\
					}\
				}\
				</script>'
			
			var html = '<html>' + head + '<body><div class="slideshow-container">';
			
			frappe.call({
				method: "front_desk.front_desk.doctype.hotel_room.hotel_room.get_images",
				args: {
					room_type: hotel_room.room_type
				},
				callback: (response) => {
					if (response.message != undefined) {
						for (let i = 0; i < response.message.length; i++) {
							var is_viewable = frappe.utils.is_image_file(response.message[i].file_url);
							if (is_viewable) {
								html = html + '<div class="mySlides"><img src="' + response.message[i].file_url + '" style="width:100%"></div>'
							}
						}

						html = html + '<a class="prev" onclick="plusSlides(-1)">&#10094;</a><a class="next" onclick="plusSlides(1)">&#10095;</a></div>' + script + '</body></html>';
						wrapper.html(html);
						frm.toggle_display("preview_html", true);
					}
					else {
						frm.toggle_display("preview_html", false);
					}
				}
			});	
		} else {
			frm.toggle_display("preview_html", false);
		}
	},
	amenities_template: function (frm) {
		if (frm.doc.amenities_template) {
			frappe.call({
			method: "front_desk.front_desk.doctype.hotel_room.hotel_room.copy_amenities_template",
			args: {
				amenities_type_id: frm.doc.amenities_template
			},
			callback: (response) => {
				if (response.message) {
					frm.set_value('amenities', []);
					$.each(response.message, function (i, d) {
						var item = frm.add_child('amenities');
						item.item = d.item;
						item.item_name = d.item_name;
						item.qty = d.qty;
					});
				}
				refresh_field('amenities');
			}
		})
		}
	}
});