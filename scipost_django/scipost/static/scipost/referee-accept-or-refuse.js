$(document).ready(function(){
    $('[name="accept"]').on('change', function() {
	if($('[name="accept"]:checked').val() == 'False') {
            $('#id_refusal_reason').parents('.form-group').show();
	}
	else {
            $('#id_refusal_reason').parents('.form-group').hide();
	}
    }).trigger('change');
});
