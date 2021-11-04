/* If home tab is chosen, don't show header forms to set acad_field and specialty. */
document.getElementById('home-tab').addEventListener('show.bs.tab', () => {
    document.getElementById('session_acad_field_form').style.display = 'none'
    document.getElementById('session_specialty_form').style.display = 'none'
})
document.getElementById('home-tab').addEventListener('hide.bs.tab', () => {
    document.getElementById('session_acad_field_form').style.display = 'block'
    document.getElementById('session_specialty_form').style.display = 'block'
})
