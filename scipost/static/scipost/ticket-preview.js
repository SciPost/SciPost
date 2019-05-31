$('#id_description').on('keyup', function(){
    $.ajax({
    	type: "POST",
    	url: "/process_rst/",
    	data: {
    	    csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val(),
	    rst_text: $('#id_description').val(),
    	},
	dataType: 'json',
    	success: function(data) {
    	    $('#preview-description').html(data.processed_rst);
	    let preview = document.getElementById('preview-description');
    	    MathJax.Hub.Queue(["Typeset",MathJax.Hub, preview]);
    	},
	error: function(data) {
	    alert("An error has occurred while processing the ReStructuredText.");
	}
    });
}).trigger('change');
