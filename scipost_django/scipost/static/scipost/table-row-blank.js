$(document).ready(function($) {
    $(".table-row").on("click", function() {
	var addr = $(this).data("href");
	window.open(addr, "_blank");
    });
});
