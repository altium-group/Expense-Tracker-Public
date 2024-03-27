// Récupérez les éléments du DOM
const showImageBtn = document.getElementById("showImageBtn");
const imageModal = document.getElementById("imageModal");
const closeImageBtn = document.getElementById("closeImageBtn");

// Ajoutez un gestionnaire d'événements pour afficher la modal
showImageBtn.addEventListener("click", function() {
  imageModal.style.display = "block";
});

// Ajoutez un gestionnaire d'événements pour fermer la modal
closeImageBtn.addEventListener("click", function() {
  imageModal.style.display = "none";
});

// Fermez la modal si l'utilisateur clique en dehors de l'image
window.addEventListener("click", function(event) {
  if (event.target === imageModal) {
    imageModal.style.display = "none";
  }
});