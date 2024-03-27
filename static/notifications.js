const notifications = document.querySelector(".notifications"),
buttons = document.querySelectorAll(".buttons .btn");

const removeToast = (toast) => {
    toast.classList.add("hide");
    if(toast.timeoutId) clearTimeout(toast.timeoutId); // Clearing the timeout for the toast
    setTimeout(() => toast.remove(), 500); // Removing the toast after 500ms
}

const createToast = (id, icon, text) => {
    // Getting the icon and text for the toast based on the id passed
    // const { icon, text } = toastDetails[id];
    const toast = document.createElement("li"); // Creating a new 'li' element for the toast
    toast.className = `toast ${id}`; // Setting the classes for the toast
    // Setting the inner HTML for the toast
    toast.innerHTML = `<div class="column">
                         <i class="fa-solid ${icon}"></i>
                         <span>${text}</span>
                      </div>
                      <i class="fa-solid fa-xmark" onclick="removeToast(this.parentElement)"></i>`;
    notifications.appendChild(toast); // Append the toast to the notification ul
    // Setting a timeout to remove the toast after the specified duration
    toast.timeoutId = setTimeout(() => removeToast(toast), 5000);
}

// Code exécuté lorsque la page index est chargée
window.addEventListener('DOMContentLoaded', (event) => {
    // Vérifiez si le code spécifique est passé à la page
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');

    // Si le code est égal à 1, exécutez le code correspondant
    if (code === '0') {
        createToast('error', 'fa-circle-xmark', 'Erreur');
    } if (code === '1') {
        createToast('success', 'fa-circle-check', 'Dépense ajouté');
    } if (code === '2') {
        createToast('success', 'fa-circle-check', 'Dépense modifié');
    } if (code === '3') {
        createToast('info', 'fa-circle-info', 'Dépense suprimé');
    } if (code === '4') {
        createToast('success', 'fa-circle-check', 'Catégorie ajouté');
    } if (code === '5') {
        createToast('success', 'fa-circle-check', 'Catégorie modifié');
    } if (code === '6') {
        createToast('info', 'fa-circle-info', 'Catégorie suprimé');
    } if (code === '7') {
        createToast('warning', 'fa-triangle-exclamation', 'Catégorie non trouvé');
    } if (code === '8') {
        createToast('warning', 'fa-triangle-exclamation', 'Dépense non trouvé');
    } if (code === '9') {
        createToast('error', 'fa-triangle-exclamation', 'identifiant / mot de passe incorect')
    } if (code === '10') {
        createToast('success', 'fa-circle-check', 'compte crée avec succès')
    } if (code === '11') {
        createToast('error', 'fa-triangle-exclamation', "Nom d'utilisateur déjà utilisé")
    } if (code === '12') {
        createToast('error', 'fa-triangle-exclamation', "Mot de passe non correspondant")
    } if (code === '13') {
        createToast('error', 'fa-triangle-exclamation', "Mail déjà utilisé")
    } if (code === '14') {
        createToast('error', 'fa-triangle-exclamation', "Fichier non conforme")
    } if (code === '15') {
        createToast('error', 'fa-triangle-exclamation', "Paramètre inconu")
    }
});
