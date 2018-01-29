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
    $('.tab-nav-container.dynamic a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
        dynamic_load_tab( e.target )
    })
    $('[data-toggle="tab"][sp-autoload="true"]').tab('show');
});
