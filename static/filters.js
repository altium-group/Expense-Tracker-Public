function filterTable() {
    let dropdown = document.getElementById("filterDropdown");
    let selectedValue = dropdown.value.toLowerCase();

    let table = document.getElementById("dataTable");
    let tr = table.getElementsByTagName("tr");

    for (let i = 0; i < tr.length; i++) {
        let td = tr[i].getElementsByTagName("td")[5];
        if (td) {
            let cellText = td.textContent.toLowerCase();
            if (selectedValue === "all" || cellText.includes(selectedValue)) {
                tr[i].classList.remove("hidden");
            } else {
                tr[i].classList.add("hidden");
            }
        }
    }
}

function Calendar() {
    let calendar = document.getElementById("calendarInput");
    let selectedDate = calendar.value;

    let table = document.getElementById("dataTable");
    let tr = table.getElementsByTagName("tr");

    for (let i = 1; i < tr.length; i++) {
        let row = tr[i];
        let rowDate = row.getAttribute("data-date");

        if (selectedDate === "" || selectedDate === rowDate) {
            row.style.display = "table-row";
        } else {
            row.style.display = "none";
        }
    }
}

var columnIndex = parseInt(document.querySelector('script[data-column-index]').getAttribute('data-column-index'));

function searchTable() {
    let input, filter, table, tr, td, i, txtValue;
    input = document.getElementById("searchInput");
    filter = input.value.toUpperCase();
    table = document.getElementById("dataTable");
    tr = table.getElementsByTagName("tr");

    let resultCount = 0;

    for (i = 0; i < tr.length; i++) {
        td = tr[i].getElementsByTagName("td")[columnIndex];
        if (td) {
            txtValue = td.textContent || td.innerText;
            if (txtValue.toUpperCase().indexOf(filter) > -1) {
                tr[i].classList.remove("hidden");
                resultCount++;
            } else {
                tr[i].classList.add("hidden");
            }
        }
    }
    const resultCountElement = document.getElementById("resultCount");

    if (filter === "") {
        resultCountElement.style.display = "none";
    } else {
        resultCountElement.style.display = "block";
        resultCountElement.textContent = `${resultCount} résultat(s)`;
    }
}