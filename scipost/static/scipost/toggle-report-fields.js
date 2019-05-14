$(document).ready(function(){
    $('#showSimpleReportButton').show();
    $('#showFullReportButton').hide();
    $('#reportSelectorButton').on('click', function () {
	$('#showSimpleReportText').toggle();
	$('#showSimpleReportButton').toggle();
	$('#showFullReportText').toggle();
	$('#showFullReportButton').toggle();
	$('#id_qualification').parent('div').parent('div').toggle();
	$('#id_strengths').parent('div').parent('div').toggle();
	$('#id_weaknesses').parent('div').parent('div').toggle();
	$('#id_requested_changes').parent('div').parent('div').toggle();
	$('#id_validity').parent('div').parent('div').toggle();
	$('#id_significance').parent('div').parent('div').toggle();
	$('#id_originality').parent('div').parent('div').toggle();
	$('#id_clarity').parent('div').parent('div').toggle();
	$('#id_formatting').parent('div').parent('div').toggle();
	$('#id_grammar').parent('div').parent('div').toggle();

	$('#previewStrengths').toggle();
	$('#previewWeaknesses').toggle();
	$('#previewRequestedChanges').toggle();
	$('#previewRatings').toggle();
    });
});
