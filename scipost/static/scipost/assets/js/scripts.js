function hide_all_alerts() {
    $(".alert").fadeOut(300);
}

$(function(){
    // Remove all alerts in screen automatically after 10sec.
    setTimeout(function() {hide_all_alerts()}, 10000);

    // Start general toggle
    $('[data-toggle="toggle"]').on('click', function() {
        $($(this).attr('data-target')).toggle();
    });
});
