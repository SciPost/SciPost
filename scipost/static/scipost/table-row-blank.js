$(document).ready(function($) {
    $(".table-row").click(function() {
	var addr = $(this).data("href");
	window.open(addr, "_blank");
    });
});
