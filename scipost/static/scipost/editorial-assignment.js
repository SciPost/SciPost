$(function() {
    $('[name="decision"]').on('change', function() {
        var val = $('[name="decision"]:checked').val();
        if(val == 'decline') {
            $('[name="refusal_reason"]').closest('.form-group').show();
            $('[name="refereeing_cycle"]').closest('.form-group').hide();
        } else {
            $('[name="refusal_reason"]').closest('.form-group').hide();
            $('[name="refereeing_cycle"]').closest('.form-group').show();
        }
    }).trigger('change');
});
