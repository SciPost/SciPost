import QRCode from 'qrcode';

$(function (){
    $.each($('[data-toggle="qr"]'), function(index, value) {
	var el = $(value);
	QRCode.toDataURL(el.data('qr-value'), function(err, url) {
            el.attr({src: url});
	});
    });
});
