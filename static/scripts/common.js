//////////////////START OF HAMBURGER MENU JAVASCRIPT //////////////////

let navbtn = document.getElementById("nav-icon");

function btnclick(){
    navbtn.classList.toggle("openTrue"); // it will toggle the class "open", i.e. add class="open" or remove class="open" to the hamburger icon which has the id, nav-icon
}

navbtn.addEventListener("click", btnclick);

////////////////// END OF HAMBURGER MENU JAVASCRIPT //////////////////

//////////////////Start of footer copyright year Javascript //////////////////

let footerCopright = document.getElementById("copyright_year").appendChild(document.createTextNode(new Date().getFullYear()));

////////////////// End of footer copyright year Javascript //////////////////