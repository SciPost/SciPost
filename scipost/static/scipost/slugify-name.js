$(document).ready(function() {
    $("#id_name").keyup(function() {
	slug_value = this.value.split(" ").join("_");
	$("#id_slug").val(slug_value);
    });
});
