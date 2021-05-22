$(document).ready(function(){
    $('[name="action_option"]').on('change', function() {
        if ($('[name="action_option"][value="refuse"]').is(':checked')) {
            $('#refusal').show();
        }
        else {
            $('#refusal').hide();
        }
    }).trigger('change');
});
