// Base scripts, imported for all pages

import './../css/style.scss'
//import { Button, Navbar, Table } from 'bootstrap';
import 'bootstrap'

// import 'htmx.org'
var htmx = require('htmx.org');
window.htmx = htmx; // Make htmx available globally

// To prevent all tabs from being updated if acad_field or specialty are changed,
// tweak the HTMX request by letting through only the one(s) of the active portal tab:
htmx.on('htmx:configRequest', evt => {
    if (evt.target.closest('div.portal-tab') && !evt.target.closest('div.portal-tab').classList.contains('active')) {
	evt.preventDefault();
    }
});
