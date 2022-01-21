var scrollToTopBtn = document.getElementById("topbutton");

window.onscroll = function(){
  scrollFunction();
};

function scrollFunction(){
  if(document.body.scrollTop > 20 || document.documentElement.scrollTop > 20) {
    scrollToTopBtn.classList.add("show");
  }
  else{
    scrollToTopBtn.classList.remove("show");
  }
}

scrollToTopBtn.addEventListener("click", scrollToTop);

var rootElement = document.documentElement;

function scrollToTop() {
  rootElement.scrollTo({
    top: 0, 
    behavior: "smooth" 
  });
}