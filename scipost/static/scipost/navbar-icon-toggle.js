function navbarIconToggle(x) {
    x.classList.toggle("change");
}

document.addEventListener('DOMContentReady', function () {
    document.getElementById('navbar-toggler-icon')
        .addEventListener('click', navbarIconToggle(this));
});
