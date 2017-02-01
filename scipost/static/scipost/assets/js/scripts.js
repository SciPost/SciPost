function hide_all_alerts() {
    $(".alert").fadeOut(300);
}


$(function(){
    // Remove all alerts in screen automatically after 4sec.
    setTimeout(function() {hide_all_alerts()}, 4000);
});
