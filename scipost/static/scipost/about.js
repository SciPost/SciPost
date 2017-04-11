
$(function() {
    // Toggle Specialization codes block
    $('[data-toggle="toggle-show"]').on('click', function(){
        var el = $($(this).attr('data-target'));
        el.toggle();

        // Switch texts of link
        $('[href="' + $(this).attr('href') + '"]').toggle();

        // Reset active search after closing the box
        if(!el.is(':visible')) {
            $('.all-specializations .specialization')
            .removeClass('active-search')
            .trigger('search-specialization');
        }
    });

    // Hover/Click class to Contributors on hovering specializations
    $('.all-specializations .specialization')
    .on('mouseover', function() {
        var code = $(this).attr('data-specialization');
        $('.single[data-specialization="'+code+'"]')
        .parents('.contributor')
        .addClass('hover-active');
    })
    .on('mouseleave', function() {
        $('.contributor.hover-active').removeClass('hover-active');
    })
    .on('click', function() {
        // Remove hover-class
        $(this)
        .toggleClass('active-search')
        .trigger('search-specialization');
    })
    .on('search-specialization', function() {
        // Reset: searching multiple specializations is not supported
        $('.search-contributors.active-search').removeClass('active-search');
        $('.contributor.active').removeClass('active');
        $('.specialization.active-search').not(this).removeClass('active-search');

        var el = $(this);
        if( el.hasClass('active-search') ) {
            // Add general 'click-active' class
            $('.search-contributors').addClass('active-search');

            // Add class to specialized Contributors
            var code = el.attr('data-specialization');
            $('.single[data-specialization="' + code + '"]')
            .parents('.contributor')
            .addClass('active');
        }
    });
});
