$(document).ready(function(){
    $('select#id_submitted_to').on('change', function (){
        var selection = $(this).val();
        $("#id_proceedings, #id_submission_type").parents('.form-group').hide()

        switch(selection){
        case "{{ id_SciPostPhys }}":
            $("#id_submission_type").parents('.form-group').show()
            break;
        case "{{ id_SciPostPhysProc }}":
            $("#id_proceedings").parents('.form-group').show()
            break;
        }
    }).trigger('change');
});
