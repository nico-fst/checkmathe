document.addEventListener('DOMContentLoaded', () => {
  document.querySelector('#edit-date').addEventListener('click', (event) => {
    editOrSave(event.target);
  });
});

function editOrSave(button) {
  if (button.classList.contains('Edit')) {
    editTut();
  } else {
    var newDateInput = document.querySelector('#new_date');
    console.log(newDateInput.value);
    saveTut(
        document.querySelector('#tut_id').getAttribute('data-tut_id'),
        {'date': newDateInput.value});
  }
}

// Visual: Replace field with new input and save button
function editTut() {
  // Replace date span with input
  var field = document.querySelector('#tut_date');
  var new_field = document.createElement('input');
  new_field.type = 'text';
  new_field.id = 'new_date';
  field.parentNode.replaceChild(new_field, field);

  // Edit Button -> Save Button, also exchange classes
  var button = document.querySelector('#edit-date');
  button.innerHTML = 'Save';
  button.classList.toggle('Save', true);
  button.classList.toggle('Edit', false);
}

// Data: the actual change saving
function saveTut(tutID, newDict) {
  fetch(`/tutoring/${tutID}`, {
    method: 'PUT',
    body: JSON.stringify({date: newDict['date']})
  }).then((response) => {
    if (response.ok) {
      const tutDate = document.querySelector('#tut_date');

        // Replace input with date span back
        var field = document.querySelector('#new_date');
        var new_field = document.createElement('span');
        new_field.id = 'tut_date';
        new_field.innerHTML = newDict['date'];
        field.parentNode.replaceChild(new_field, field);
    }
  });
}
