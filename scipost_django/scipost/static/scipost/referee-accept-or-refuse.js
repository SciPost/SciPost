$(document).ready(function () {
    $('[name="accept"]').on('change', function () {
        $('#id_intended_delivery_date').parents('.form-group').hide();
        $('#id_refusal_reason').parents('.form-group').hide();

        if ($('[name="accept"]:checked').val() == 'True') {
            $('#id_intended_delivery_date').parents('.form-group').show();
        }
        else if($('[name="accept"]:checked').val() == 'False') {
            $('#id_refusal_reason').parents('.form-group').show();
        }
    }).trigger('change');
    $('[name="refusal_reason"]').on('change', function () {
        if ($('[name="refusal_reason"]').val() == 'OTH') {
            $('#id_other_refusal_reason').parents('.form-group').show();
        }
        else {
            $('#id_other_refusal_reason').parents('.form-group').hide();
        }
    }).trigger('change');
});
