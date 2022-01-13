function editBioNow() {
    document.getElementById("editBio").setAttribute("hidden", null);
    document.getElementById("saveBio").removeAttribute("hidden");
    document.getElementById("cancleSaveBio").removeAttribute("hidden");
    document.getElementById("teacherBio").removeAttribute("disabled");
}
function cancelBio() {
    document.getElementById("saveBio").setAttribute("hidden", null);
    document.getElementById("cancleSaveBio").setAttribute("hidden", null);
    document.getElementById("editBio").removeAttribute("hidden");
    document.getElementById("teacherBio").setAttribute("disabled", null);
}