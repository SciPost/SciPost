function dynamic_load_tab( target_tab ) {
    var tab = $(target_tab);
    var url = tab.attr('sp-dynamic-load');
    if(tab.data('sp-loaded') == 'true') {
        // window.history.replaceState('scipost', document.title, url);
        return;  // Only load once
    }

    var target = $(tab.attr('href'));
    $(target)
    .show()
    .html('<div class="loading"><i class="fa fa-spinner fa-pulse fa-3x fa-fw"></i></div>');

    $.get(url).done(function(data) {
        $(target).html(data).promise().done(function() {
            tab.data('sp-loaded', 'true');
        });

        // window.history.replaceState('scipost', document.title, url);
    });
}

$(function(){
    // Change `tab` GET parameter for page-reload
    $('a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
        dynamic_load_tab( e.target )
    })
    $('[data-toggle="tab"][sp-autoload="true"]').tab('show');

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
