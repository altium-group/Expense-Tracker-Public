function deleteSelectedExpenses() {
    var checkboxes = document.getElementsByName('expense-checkbox');
    var selectedExpenses = [];
    for (var i = 0; i < checkboxes.length; i++) {
        if (checkboxes[i].checked && !checkboxes[i].closest('.hidden')) {
            selectedExpenses.push(checkboxes[i].value);
        }
    }
    if (selectedExpenses.length === 0) {
        alert("Veuillez sélectionner au moins une dépense à supprimer.");
        return;
    }
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/delete", true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 200) {
            window.location.reload();
        }
    };
    var data = JSON.stringify({ "selectedExpenses": selectedExpenses });
    xhr.send(data);
}