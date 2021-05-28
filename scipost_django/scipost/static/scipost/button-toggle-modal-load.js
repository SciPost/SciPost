$(document).ready(function(){
    $('button[data-bs-toggle="modal"]').on('click',function(){
	var dataURL = $(this).attr('data-bs-href');
	target_body = $(this).attr('data-bs-target-body');
	$(target_body).load(dataURL);
    });
});
