import tooltip from './tooltip.js';
import notifications from './notifications.js';

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

function init_page() {
    console.log('init!')
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
}

$(function(){
    // Remove all alerts in screen automatically after 15sec.
    setTimeout(function() {hide_all_alerts()}, 15000);

    // Change `tab` GET parameter for page-reload
    $('a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
        var tab_name = e.target.hash.substring(1)
        window.history.replaceState({}, null, '?tab=' + tab_name);
    });

    init_page();

    // Simple simple Angular-like loading!
    $('a[data-toggle="dynamic"]').on('click', function(event) {
        event.preventDefault();
        var self = this,
            url = $(this).attr('href'),
            target = $(this).attr('data-target');
        // console.log('click', url, target);

        $(target).html('<div class="loading"><i class="fa fa-circle-o-notch fa-spin fa-3x fa-fw"></i></div>');

        $.get(url + '?json=1').done(function(data) {
            // console.log('done', data);
            $(target).html(data).promise().done(function() {
                init_page();
            });
            $('[data-target="active-list"]')
                .find('> li')
                .removeClass('active')
            $(self).parents('[data-target="active-list"] > li')
                .addClass('active');
        });
    });
});
