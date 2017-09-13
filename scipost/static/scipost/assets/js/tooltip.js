var activate_tooltip = function() {
    jQuery('[data-toggle="tooltip"]').tooltip({
        animation: false,
        fallbackPlacement: 'clockwise',
        placement: 'auto'
    });
}

activate_tooltip();
