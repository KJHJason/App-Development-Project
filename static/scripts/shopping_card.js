function unavailable() {
    var unavailables = document.getElementsByClassName("unavailable")
    for (var unavailable = 0; unavailable < unavailables.length; unavailable++) {
        document.getElementsByClassName("unavailable")[unavailable].innerHTML += "*Unavailable*"
    }
}

window.onload = unavailable()

function removeCourse(courseID) {
    document.getElementById(courseID).submit()
    console.log(courseID)
}


//https://www.w3schools.com/jsref/tryit.asp?filename=tryjsref_form_submit
