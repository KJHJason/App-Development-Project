function unavailable() {
    var unavailables = document.getElementsByClassName("unavailable")
    for (var unavailable = 0; unavailable < unavailables.length; unavailable++) {
        document.getElementsByClassName("unavailable")[unavailable].innerHTML += "*Unavailable*"
    }
}
