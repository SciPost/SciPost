$(document).ready(function(){
    $('#ref_reason').hide();
    $('#id_accept').on('change', function() {
	if ($('#id_accept_1').is(':checked')) {
            $('#ref_reason').show();
	}
	else {
            $('#ref_reason').hide();
	}
    });
});
