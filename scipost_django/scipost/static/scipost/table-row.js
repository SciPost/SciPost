$(document).ready(function($) {
    $(".table-row").on("click", function (event) {
        if (event.ctrlKey || event.metaKey) {
            window.open($(this).data("href"), '_blank');
        } else {
            window.document.location = $(this).data("href");
        }
    })
});
