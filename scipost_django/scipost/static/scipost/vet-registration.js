$(function() {
    $('[name="decision"]').on('click change', function(){
        if($(this).filter(':checked').val() == 'False') {
            $('#id_refusal_reason, #id_email_response_field').parents('.form-group').show();
        } else {
            $('#id_refusal_reason, #id_email_response_field').parents('.form-group').hide();
        }
    }).trigger('change');
});
