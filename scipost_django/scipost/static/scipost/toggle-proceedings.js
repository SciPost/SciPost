/* If Proceedings is chosen as Journal, display Proceedings selector */

/* for publications tab */
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

/* for submissions tab */
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
