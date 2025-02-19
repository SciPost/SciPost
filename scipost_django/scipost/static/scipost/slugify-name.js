jQuery(function() {
	$("#id_name").on("keyup", function() {
	slug_value = this.value.split(" ").join("-").toLowerCase();
	$("#id_slug").val(slug_value);
	});
});
