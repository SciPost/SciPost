$(function() {
    $('[name="accept"]').on('change', function() {
        var val = $('[name="accept"]:checked').val();
        if(val == 'True') {
            $('#ref_reason').hide();
        } else {
            $('#ref_reason').show();
        }
    }).trigger('change');
});
