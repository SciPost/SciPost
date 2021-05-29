require('jquery-ui/ui/widgets/sortable');
require('jquery-ui/ui/disable-selection');

function hide_all_alerts() {
    $(".alert").remove('.no-dismiss').fadeOut(300);
}

var activate_tooltip = function() {
    jQuery('[data-bs-toggle="tooltip"]').tooltip({
        animation: false,
        fallbackPlacement: 'clockwise',
        placement: 'auto'
    });
}

var select_form_table = function(table_el) {
    $(table_el + ' tbody tr input[type="checkbox"]').on('change', function() {
        if ( $(this).prop('checked') ) {
            $(this).parents('tr').addClass('table-info')
        } else {
            $(this).parents('tr').removeClass('table-info')
        }
    }).trigger('change');
};

var sort_form_list = function(list_el) {
    $(list_el).sortable({handle: ".handle, li"})
    .on('sortupdate', function() {
        $.each($(list_el + ' > *'), function(index, el) {
            $(el).find('input[name$=ORDER]').val(index + 1);
        });
    }).trigger('sortupdate');
};



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

    // Auto-submit hook for general form elements
    $("form .auto-submit input, form.auto-submit input, form.auto-submit select").on('change', function(){
        $(this).parents('form').trigger('submit')
    });

    // Start general toggle
    $('[data-bs-toggle="toggle"]').on('click', function() {
        $($(this).attr('data-bs-target')).toggle();
    });

    // Make links that could possibly hide html blocks
    $('[data-toggle="hide"]').on('click', function() {
        $($(this).attr('data-bs-target'))
        .hide()
        .parents('.active')
        .removeClass('active');
    });

    activate_tooltip();
    sort_form_list('form ul.sortable-list');
    sort_form_list('table.sortable-rows > tbody');
    select_form_table('.table-selectable');
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
    // Remove all alerts in screen automatically after 15sec.
    setTimeout(function() {hide_all_alerts()}, 15000);

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


    // Backdrop for main nav dropdowns.
    $('#main-navbar .dropdown').on('shown.bs.dropdown', function () {
      $('.backdrop').show();
    })
    $('#main-navbar .dropdown').on('hide.bs.dropdown hidden.bs.dropdown	', function () {
      $('#backdrop').hide();
    })

});
