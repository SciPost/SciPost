jQuery(function() {
    const radioButtons = $("#div_id_was_used input[name='was_used']");

    toggleUseDetails(radioButtons.filter(":checked").val());

    // Show or hide the use_details field based on the was_used checkbox
    radioButtons.on("change", function() {
        toggleUseDetails($(this).val());
    });
});

function toggleUseDetails(value) {
    if (value === "True") {
        $("#div_id_use_details").closest("div").show();
    } else {
        $("#div_id_use_details").closest("div").hide();
    }
}