$(document).ready(function() {

    $('#submitButton').hide();
    $('#preview-remarks_for_editors-div').hide();

    $("#id_comment_text").on('keyup', function(){
	$('#runPreviewButton').show();
	$('#preview-comment_text').css('background', '#feebce');
	$('#submitButton').hide();
    });
    $("#id_remarks_for_editors").on('keyup', function(){
	$('#runPreviewButton').show();
	$('#preview-remarks_for_editors-div').show();
	$('#preview-remarks_for_editors').css('background', '#feebce');
	$('#submitButton').hide();
    });

    $('#runPreviewButton').on('click', function(){
	fetchMarkupPreview('comment_text');
	fetchMarkupPreview('remarks_for_editors');
    	$('#runPreviewButton').hide();
    	$('#preview-comment_text').css('background', '#ffffff');
    	$('#preview-remarks_for_editors').css('background', '#ffffff');
    	$('#submitButton').show();
    }).trigger('change');

    $('input[name$="anonymous"]').on('change', function() {
        $('.anonymous-alert').show()
            .children('span.anonymous_variant').hide()
        if ($(this).prop('checked')) {
                $('.anonymous-yes').show();
        } else {
                $('.anonymous-no').show();
        }
        }).trigger('change');
    });
