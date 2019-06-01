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
    $.ajax({
    	type: "POST",
    	url: "/process_rst/",
    	data: {
    	    csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val(),
	    rst_text: $('#id_description').val(),
    	},
	dataType: 'json',
    	success: function(data) {
	    if (data.errors) {
		$('#preview-title').css('background', '#eedbbe');
		$('#preview-description').css('background', '#feebce');
		$('#submitButton').hide();
		$('#runPreviewButton').show();
		alert("An error has occurred while processing the ReStructuredText:\n\n" + data.errors);
	    }
    	    $('#preview-description').html(data.processed_rst);
	    let preview = document.getElementById('preview-description');
    	    MathJax.Hub.Queue(["Typeset",MathJax.Hub, preview]);
    	},
	error: function(data) {
	    alert("An error has occurred while processing the ReStructuredText.");
	}
    });
    $('#runPreviewButton').hide();
    $('#preview-title').css('background', '#f1f1f1');
    $('#preview-description').css('background', '#f8f8f8');
    $('#submitButton').show();
}).trigger('change');
