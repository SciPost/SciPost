import tooltip from './tooltip.js';

function hide_all_alerts() {
    $(".alert").fadeOut(300);
}

var getUrlParameter = function getUrlParameter(sParam) {
    var sPageURL = decodeURIComponent(window.location.search.substring(1)),
        sURLVariables = sPageURL.split('&'),
        sParameterName,
        i;

    for (i = 0; i < sURLVariables.length; i++) {
        sParameterName = sURLVariables[i].split('=');

        if (sParameterName[0] === sParam) {
            return sParameterName[1] === undefined ? true : sParameterName[1];
        }
    }
};

$(function(){
    // Remove all alerts in screen automatically after 15sec.
    setTimeout(function() {hide_all_alerts()}, 15000);

    // Start general toggle
    $('[data-toggle="toggle"]').on('click', function() {
        $($(this).attr('data-target')).toggle();
    });

    // Show right tab if url contains `tab` GET request
    var tab = getUrlParameter('tab')
    if (tab) {
        $('a[href="#' + tab + '"][data-toggle="tab"]').tab('show');
    }

    // Change `tab` GET parameter for page-reload
    $('a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
        var tab_name = e.target.hash.substring(1)
        window.history.replaceState({}, null, '?tab=' + tab_name);
    });
});
