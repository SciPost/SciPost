import notifications from './notifications.js';

function hide_all_alerts() {
    $(".alert").fadeOut(300);
}

var activate_tooltip = function() {
    jQuery('[data-toggle="tooltip"]').tooltip({
        animation: false,
        fallbackPlacement: 'clockwise',
        placement: 'auto'
    });
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

function init_page() {
    // Show right tab if url contains `tab` GET request
    var tab = getUrlParameter('tab')
    if (tab) {
        $('a[href="#' + tab + '"][data-toggle="tab"]').tab('show');
    }

    // Auto-submit hook for general form elements
    $("form .auto-submit input, form.auto-submit input, form.auto-submit select").on('change', function(){
        $(this).parents('form').submit()
    });

    // Start general toggle
    $('[data-toggle="toggle"]').on('click', function() {
        $($(this).attr('data-target')).toggle();
    });

    // Make links that could possibly hide html blocks
    $('[data-toggle="hide"]').on('click', function() {
        $($(this).attr('data-target'))
        .hide()
        .parents('.active')
        .removeClass('active');
    });

    activate_tooltip();
}

$(function(){
    // Remove all alerts in screen automatically after 15sec.
    setTimeout(function() {hide_all_alerts()}, 15000);

    init_page();

    // Simple simple Angular-like loading!
    $('a[data-toggle="dynamic"]').on('click', function(event) {
        event.preventDefault();
        var self = this,
            url = $(this).attr('href'),
            target = $(this).attr('data-target');

        $(target)
        .show()
        .html('<div class="loading"><i class="fa fa-circle-o-notch fa-spin fa-3x fa-fw"></i></div>');

        $.get(url + '?json=1').done(function(data) {
            $(target).html(data).promise().done(function() {
                init_page();
            });
            $('[data-target="active-list"]')
                .find('> li')
                .removeClass('active')
            $(self).parents('[data-target="active-list"] > li')
                .addClass('active');

            window.history.replaceState('scipost', document.title, url);
        });
    });
});
