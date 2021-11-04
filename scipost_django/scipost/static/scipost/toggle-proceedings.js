/* If Proceedings is chosen as Journal, display Proceedings selector */

/* for portal publications tab */
if (document.getElementById("id_journal")) {
    document.getElementById("id_journal").addEventListener("change", () => {
	var e = document.getElementById("id_journal")
	if (e.options[e.selectedIndex].text.includes('Proceedings')) {
	    document.getElementById("row_proceedings").style.display = 'block'
	} else {
	    document.getElementById("row_proceedings").style.display = 'none'
	    document.getElementById("id_proceedings").value = null
	}
    })
}

/* for portal/pool submissions tab */
if (document.getElementById("id_submitted_to")) {
    document.getElementById("id_submitted_to").addEventListener("change", () => {
	var e = document.getElementById("id_submitted_to")
	if (e.options[e.selectedIndex].text.includes('Proceedings')) {
	    document.getElementById("row_proceedings").style.display = 'block'
	} else {
	    document.getElementById("row_proceedings").style.display = 'none'
	    document.getElementById("id_proceedings").value = null
	}
    })
}

/* For pool. If user opts for viewing submissions for which they are EIC, toggle
   editor_in_charge selector and set status to 'all' */
document.getElementsByName("search_set").forEach(e => {
    e.addEventListener("change", () => {
	if (e.checked && e.value == 'eic') {
	    document.getElementById("id_editor_in_charge").value = null
	    document.getElementById("col_eic").style.display = 'none'
	    document.getElementById("id_status").value = 'all'
	} else {
	    document.getElementById("col_eic").style.display = 'block'
	}
    })
})
