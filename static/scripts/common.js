////////////////// Boostrap 5 Tooltip Javascript //////////////////

var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
  return new bootstrap.Tooltip(tooltipTriggerEl)
})

////////////////// End of Boostrap 5 Tooltip Javascript //////////////////

//////////////////START OF HAMBURGER MENU JAVASCRIPT //////////////////

document.addEventListener('click',function(e){
    // Hamburger menu
    if(e.target.classList.contains('hamburger-toggle')){
      e.target.children[0].classList.toggle('active');
    }
})   

////////////////// END OF HAMBURGER MENU JAVASCRIPT //////////////////

//////////////////Start of footer copyright year Javascript //////////////////

let footerCopright = document.getElementById("copyright_year").appendChild(document.createTextNode(new Date().getFullYear()));

////////////////// End of footer copyright year Javascript //////////////////