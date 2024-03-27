const showTableButton = document.getElementById("showTableButton");
const dataTable = document.getElementById("dataTable");
const searchInput = document.getElementById("searchInput");
dataTable.style.display = "none";
searchInput.style.display = "none";

showTableButton.addEventListener("click", function () {
    if (dataTable.style.display === "none") {
        dataTable.style.display = "table";
        searchInput.style.display = "block";
        showTableButton.innerHTML = '<i class="fas fa-eye-slash"></i> Cacher';
    } else {
        dataTable.style.display = "none";
        searchInput.style.display = "none";
        showTableButton.classList.remove("active");
        showTableButton.innerHTML = '<i class="fas fa-eye"></i> Afficher';
    }
});