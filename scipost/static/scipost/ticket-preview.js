$('#submitButton').hide();

$('#id_title').on('keyup', function(){
    $('#runPreviewButton').show();
    $('#preview-title').css('background', '#eedbbe');
    $('#preview-description').css('background', '#feebce');
    $('#submitButton').hide();
});

$('#id_description').on('keyup', function(){
    $('#runPreviewButton').show();
    $('#preview-title').css('background', '#eedbbe');
    $('#preview-description').css('background', '#feebce');
    $('#submitButton').hide();
});

$('#runPreviewButton').on('click', function(){
    $('#preview-title').text($('#id_title').val());
    fetchMarkupPreview('description');
    $('#runPreviewButton').hide();
    $('#preview-title').css('background', '#f1f1f1');
    $('#preview-description').css('background', '#ffffff');
    $('#submitButton').show();
}).trigger('change');
