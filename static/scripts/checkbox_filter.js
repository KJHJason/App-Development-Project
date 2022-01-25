function toggle(id) {
    var filters = JSON.parse(document.getElementById("checkedFilters").value);
    var checkbox = document.getElementById(id);

    if (checkbox.checked) {
        console.log("Is checked now");
        if (filters.indexOf(id) == -1) {
            filters.push(id)
        }
        console.log(id);
        console.log(filters);
    }
    else {
        console.log("Is not checked now")
        if (filters.indexOf(id) != -1) {
            console.log(filters.indexOf(id));
            filters.splice(filters.indexOf(id), 1);
        }
        console.log(id);
        console.log(filters);
    }
    document.getElementById('checkedFilters').value = JSON.stringify(filters);
}

function searchSubmit() {
    document.getElementById("search-form").submit();
}
