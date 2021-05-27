$(document).ready(function(){
    $('button[data-bs-toggle="modal"]').on('click',function(){
	var dataURL = $(this).attr('data-href');
	target_body = $(this).attr('data-target-body');
	$(target_body).load(dataURL);
    });
});
