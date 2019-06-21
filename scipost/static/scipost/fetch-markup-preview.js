function fetchMarkupPreview(label) {

    $.ajax({
    	type: "POST",
    	url: "/markup/process/",
    	data: {
    	    csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val(),
	    markup_text: $('#id_' + label).val(),
    	},
	dataType: 'json',
    	success: function(data) {
	    $('#language-' + label).text("Language (auto-detected): " + data.language);
	    if (data.errors) {
		$('#preview-' + label).css('background', '#feebce');
		$('#submitButton').hide();
		$('#runPreviewButton').show();
		alert("An error has occurred while processing the text:\n\n" + data.errors);
	    }
    	    $('#preview-' + label).html(data.processed);
	    let preview = document.getElementById('preview-' + label);
    	    MathJax.Hub.Queue(["Typeset",MathJax.Hub, preview]);
    	},
	error: function(data) {
	    alert("An error has occurred while processing the text:\n\n." + data);
	}
    });
}
