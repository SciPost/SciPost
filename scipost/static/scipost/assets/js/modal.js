require('bootstrap-loader');

jQuery('[data-toggle="modal"]').on('click', function(){
    var target = $(this).attr('data-target');
    $(target).modal('show');
});
