$(function(){
    function set_preview(el) {
        $('[data-receive$="' + $(el).attr('id').split('id_')[1] + '"]').text($(el).val())
    }
    function set_preview_select(el) {
        $('[data-receive$="' + $(el).attr('id').split('id_')[1] + '"]').text($(el).find('option:selected').text())
    }
    function update_identity_preview(show_identity) {
        $('[data-receive="report-identity"] [if-anonymous]').hide();
        if (show_identity) {
            $('[data-receive="report-identity"] [if-anonymous="false"]').show();
        } else {
            $('[data-receive="report-identity"] [if-anonymous="true"]').show();
        }
    }
    $('#id_weaknesses, #id_strengths, #id_report, #id_requested_changes').on('keyup', function(){
        set_preview(this)
        if (typeof MathJax.Hub !== "undefined") {
            // First trigger will fail since MathJax is loaded in the footer.
            MathJax.Hub.Queue(["Typeset",MathJax.Hub]);
        }
    }).trigger('keyup');
    $('#id_validity, #id_originality, #id_significance, #id_clarity, #id_formatting, #id_grammar').on('change', function(){
        set_preview_select(this);
    }).trigger('change');

    $('input[name$="anonymous"]').on('change', function() {
        $('.anonymous-alert').show()
	    .children('h3').hide()
        if ($(this).prop('checked')) {
            update_identity_preview(false);
            $('.anonymous-yes').show();
        } else {
            update_identity_preview(true);
            $('.anonymous-no').show();
        }
    }).trigger('change');
});
