let nonRequiredFields = $('form label+:not([required])').parent('div').not('#div_id_use_details').not('#div_id_license_agreement');

$(document).ready(function () {
    $('#showSimpleReportButton').show();
    $('#showFullReportButton').hide();
    $('#reportSelectorButton').on('click', function () {
        nonRequiredFields.toggle();

        $('#previewStrengths').toggle();
        $('#previewWeaknesses').toggle();
        $('#previewRequestedChanges').toggle();
        $('#previewRatings').toggle();
    });
});
	
