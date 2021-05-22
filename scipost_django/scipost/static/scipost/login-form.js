$(function() {
    $('[name="code"]').parents('.form-group').hide();  // Just to prevent having annoying animations.
    $('form [name="username"]').on('change', function() {
        $.ajax({
            type: 'POST',
            url: '/login/info/',
            data: {
                csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val(),
                username: $('form [name="username"]').val(),
            },
            dataType: 'json',
            processData: true,
            success: function(data) {
                if (data.has_totp) {
                    $('[name="code"]').parents('.form-group').show();
                } else {
                    $('[name="code"]').parents('.form-group').hide();
                }
            }
        });
    }).trigger('change');
});
