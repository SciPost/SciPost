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




function init_page() {

    // Auto-submit hook for general form elements
    $("form .auto-submit input, form.auto-submit input, form.auto-submit select").on('change', function(){
        $(this).parents('form').trigger('submit')
    });

    // Start general toggle
    $('[data-bs-toggle="toggle"]').on('click', function() {
        $($(this).attr('data-bs-target')).toggle();
    });

    activate_tooltip();
    sort_form_list('form ul.sortable-list');
    sort_form_list('table.sortable-rows > tbody');
    select_form_table('.table-selectable');
}


$(function(){
    // Remove all alerts in screen automatically after 15sec.
    setTimeout(function() {hide_all_alerts()}, 15000);

    init_page();

});
