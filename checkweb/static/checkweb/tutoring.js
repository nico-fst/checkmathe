document.addEventListener('DOMContentLoaded', () => {
    document.querySelector('#edit-date').addEventListener('click', (event) => {
        const button = event.target;
        edit_tut(button.getAttribute("data-tut_id", "data"));
  });
});


function edit_tut(tut_id, prop) {
    fetch(`/tutoring/${tut_id}`, {
        method: "PUT",
        body: JSON.stringify({ date: "2023-01-23" })
    }).then((response) => {
        if (response.ok) {
            const tut_date = document.querySelector('#tut_date')
            tut_date.innerHTML = "LOL";
        }
    });
}