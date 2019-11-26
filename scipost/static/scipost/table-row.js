$(document).ready(function($) {
    $(".table-row").on("click", function() {
        window.document.location = $(this).data("href");
    });
});
