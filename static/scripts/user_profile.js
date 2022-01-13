// to set a cookie to contain the file size value upon submission
function filesize(element) {
    document.cookie = `filesize = ${element.files[0].size}`; // using string interpolation to get the value of the image file size and element.files[0] for the first file's size
}

// for editing teacher's bio
function editBioNow() {
    document.getElementById("originalTextarea").setAttribute("hidden", null);
    document.getElementById("editedTextarea").removeAttribute("hidden");
}
function cancelBio() {
    document.getElementById("originalTextarea").removeAttribute("hidden");
    document.getElementById("editedTextarea").setAttribute("hidden", null);
}