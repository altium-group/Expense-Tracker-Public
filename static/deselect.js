function deselectAll() {
    var checkboxes = document.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(function(checkbox) {
        checkbox.checked = false;
    });
}
function showButtonsDiv() {
    var buttonsDiv = document.getElementById('buttonsDiv');
    buttonsDiv.style.display = 'block';
}
function hideButtonsDiv() {
    var buttonsDiv = document.getElementById('buttonsDiv');
    buttonsDiv.style.display = 'none';
}
function checkCheckboxes() {
    var checkboxes = document.querySelectorAll('input[type="checkbox"]:not(#masterCheckbox)');
    var anyChecked = false;

    checkboxes.forEach(function(checkbox) {
        if (checkbox.checked) {
            anyChecked = true;
        }
    });

    if (anyChecked) {
        showButtonsDiv();
    } else {
        hideButtonsDiv();
    }
}

var checkboxes = document.querySelectorAll('input[type="checkbox"]:not(#masterCheckbox)');
checkboxes.forEach(function(checkbox) {
    checkbox.addEventListener('click', checkCheckboxes);
});

function toggleSelectAll() {
    var masterCheckbox = document.getElementById('masterCheckbox');
    var checkboxes = document.querySelectorAll('input[type="checkbox"]');

    checkboxes.forEach(function(checkbox) {
        checkbox.checked = masterCheckbox.checked;
    });
}

var masterCheckbox = document.getElementById('masterCheckbox');
masterCheckbox.addEventListener('click', function() {
    toggleSelectAll();
    checkCheckboxes();
});
