$(document).ready(
	function() {
		//this looks for button clicks
		$("#smashit").click(
			function(e) {
				$.post("/generator", {"smashit": true} )
				.done(
					function(string) {
						$("#smashit").val(string);
						setTimeout(
							function() {
								$("#smashit").val("Toggle Door");
							},
						2000);
					}
				);
				e.preventDefault();
			}
		);

		//start pulling position data
		var loopid = setInterval(
			function() {
				$.post("/generator", {"pos": "req"} )
				.done(
					function(string) {
						var json = jQuery.parseJSON(string);
						$("#isitopen").text(json.spos);
						$("#isitopen").removeClass("closed").removeClass("open").addClass(json.spos == "closed" ? "closed": "open");
						$("#location").val(json.pos);
					}
				);
			}, 200);
	}
);
