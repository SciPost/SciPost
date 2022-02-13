

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
        $('a[href="#' + tab + '"][data-bs-toggle="tab"]').tab('show');
    }

    // Start general toggle
    $('[data-bs-toggle="toggle"]').on('click', function() {
        $($(this).attr('data-bs-target')).toggle();
    });
}

function dynamic_load_tab( target_tab ) {
    var tab = $(target_tab);
    var url = tab.attr('data-sp-dynamic-load');
    if(tab.data('sp-loaded') == 'true') {
        // window.history.replaceState('scipost', document.title, url);
        return;  // Only load once
    }

    var target = $(tab.attr('href'));
    $(target)
    .show()
    .html('<div class="loading">Loading...</div>');

    $.get(url).done(function(data) {
        $(target).html(data).promise().done(function() {
            tab.data('sp-loaded', 'true');
            init_page();
        });

        // window.history.replaceState('scipost', document.title, url);
    });

}

$(function(){

    init_page();

    // Simple simple Angular-like loading!
    $('a[data-toggle="dynamic"]').on('click', function(event) {
        event.preventDefault();
        var self = this,
            url = $(this).attr('href'),
            target = $(this).attr('data-bs-target');

        $(target)
        .show()
        .html('<div class="loading">Loading...</div>');

        $.get(url + '?json=1').done(function(data) {
            $(target).html(data).promise().done(function() {
                init_page();
            });
            $('[data-bs-target="active-list"]')
                .find('> li')
                .removeClass('active')
            $(self).parents('[data-bs-target="active-list"] > li')
                .addClass('active');

            window.history.replaceState('scipost', document.title, url);
        });
    });


    // Change `tab` GET parameter for page-reload
    $('.tab-nav-container.dynamic a[data-bs-toggle="tab"]').on('shown.bs.tab', function (e) {
	dynamic_load_tab( e.target )
    })
    $('[data-bs-toggle="tab"][data-sp-autoload="true"]').tab('show');

});
