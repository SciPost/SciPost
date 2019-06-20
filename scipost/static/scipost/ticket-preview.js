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
    	url: "/markup/process/",
    	data: {
    	    csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val(),
	    markup_text: $('#id_description').val(),
    	},
	dataType: 'json',
    	success: function(data) {
	    $('#languageElement').text("Language (auto-detected): " + data.language);
	    if (data.errors) {
		$('#preview-title').css('background', '#eedbbe');
		$('#preview-description').css('background', '#feebce');
		$('#submitButton').hide();
		$('#runPreviewButton').show();
		alert("An error has occurred while processing the text:\n\n" + data.errors);
	    }
    	    $('#preview-description').html(data.processed);
	    let preview = document.getElementById('preview-description');
    	    MathJax.Hub.Queue(["Typeset",MathJax.Hub, preview]);
    	},
	error: function(data) {
	    alert("An error has occurred while processing the text:\n\n." + data);
	}
    });
    $('#runPreviewButton').hide();
    $('#preview-title').css('background', '#f1f1f1');
    $('#preview-description').css('background', '#ffffff');
    $('#submitButton').show();
}).trigger('change');
