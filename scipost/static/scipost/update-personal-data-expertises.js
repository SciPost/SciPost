$(document).ready(function(){
    $('select#id_discipline').on('change', function() {
        var selection = $(this).val();
        $("ul[id^='id_expertises_']").closest("li").hide();

        switch(selection){
        case "physics":
            $("#id_expertises_0").closest("li").show();
            break;
        case "astrophysics":
            $("#id_expertises_1").closest("li").show();
            break;
        case "mathematics":
            $("#id_expertises_2").closest("li").show();
            break;
        case "computerscience":
            $("#id_expertises_3").closest("li").show();
            break;
        default:
            $("ul[id^='id_expertises_']").closest("li").show();
            break;
        }
    }).trigger('change');

});
