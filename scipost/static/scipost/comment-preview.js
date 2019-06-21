$(document).ready(function() {

    $('#submitButton').hide();

    $("#id_comment_text").on('keyup', function(){
	$('#runPreviewButton').show();
	$('#preview-comment_text').css('background', '#feebce');
	$('#submitButton').hide();
    });

    $('#runPreviewButton').on('click', function(){
	fetchMarkupPreview('comment_text');
    	$('#runPreviewButton').hide();
    	$('#preview-comment_text').css('background', '#ffffff');
    	$('#submitButton').show();
    }).trigger('change');

    $('input[name$="anonymous"]').on('change', function() {
	$('.anonymous-alert').show()
	    .children('h3').hide()
	if ($(this).prop('checked')) {
            $('.anonymous-yes').show();
	} else {
            $('.anonymous-no').show();
	}
    }).trigger('change');
});
