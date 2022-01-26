// for editing teacher's bio
function editBioNow() {
    document.getElementById("originalTextarea").setAttribute("hidden", null);
    document.getElementById("editedTextarea").removeAttribute("hidden");
}
function cancelBio() {
    document.getElementById("originalTextarea").removeAttribute("hidden");
    document.getElementById("editedTextarea").setAttribute("hidden", null);
}