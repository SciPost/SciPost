function searchHeader() {
    document.getElementById("header-search-button").addEventListener("click", function(event){
        if (document.documentElement.clientWidth > 768) {
            event.preventDefault();
            var x = document.getElementById("header-search-form");
            if (x.style.display === "none") {
                x.style.display = "block";
            } else {
                x.style.display = "none";
            }
        }
    });

    document.getElementById("header-search-close-btn").addEventListener("click", function(event){
        var x = document.getElementById("header-search-form");
        x.style.display = "none";
    });

    if (document.documentElement.clientWidth <= 768) {
        // Force-close if form is prefilled.
        var x = document.getElementById("header-search-form");
        x.style.display = "none";
    }
}
searchHeader();
