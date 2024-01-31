require('jquery-ui/ui/widgets/sortable');
require('jquery-ui/ui/disable-selection');


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

    // Run scripts after htmx settles
    document.body.addEventListener("htmx:afterSettle", () =>{
        activate_tooltip(); // Re-activate tooltips
        $('.alert-dismissible').delay(10000).fadeOut(300); // Auto-hide alerts
    });

    sort_form_list('form ul.sortable-list');
    sort_form_list('table.sortable-rows > tbody');
    select_form_table('.table-selectable');
}


$(function(){
    init_page();
});
