$(document).ready(function(){
    $('select#id_discipline').on('change', function() {
        var selection = $(this).val();
        $("ul[id^='id_expertises_']").closest("li").hide();

        switch(selection){
        case "physics":
	    $('li:contains("Physics")').filter(function(){
		return $(this).text().indexOf('Physics') == 0;}).show();
            break;
        case "astrophysics":
	    $('li:contains("Astrophysics")').filter(function(){
		return $(this).text().indexOf('Astrophysics') == 0;}).show();
            break;
        case "mathematics":
	    $('li:contains("Mathematics")').filter(function(){
		return $(this).text().indexOf('Mathematics') == 0;}).show();
            break;
        case "chemistry":
	    $('li:contains("Chemistry")').filter(function(){
		return $(this).text().indexOf('Chemistry') == 0;}).show();
            break;
        case "computerscience":
	    $('li:contains("Computer Science")').filter(function(){
		return $(this).text().indexOf('Computer Science') == 0;}).show();
            break;
        default:
            $("ul[id^='id_expertises_']").closest("li").show();
            break;
        }
    }).trigger('change');

});
