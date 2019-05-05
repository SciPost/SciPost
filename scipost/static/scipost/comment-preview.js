$(function(){
    var comment_text_input = $("#id_comment_text");

    comment_text_input.on('keyup', function(){
        var new_text = $(this).val()
        $("#preview-comment_text").text(new_text)
        if( typeof MathJax.Hub !== 'undefined' ) {
            MathJax.Hub.Queue(["Typeset",MathJax.Hub]);
        }
    }).trigger('keyup');

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
