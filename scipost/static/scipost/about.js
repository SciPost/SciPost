
$(function() {
    $('.search-specialization').on('change keyup', function(event) {
        var el = $(this);
        var val = el.val().trim().toLowerCase(),
            spec = el.attr('data-college');
        if(val) {
            $('[data-contributors="'+spec+'"]').addClass('searching');
        } else {
            $('[data-contributors="'+spec+'"]').removeClass('searching')

        }
        $('.contributor').removeClass('active');
        $('[data-contributors="'+spec+'"] [data-specialization*="'+val+'"]').parents('.contributor').addClass('active');
    });
});
