document.addEventListener('DOMContentLoaded', () => {
  document.querySelector('#edit-date').addEventListener('click', (event) => {
    editOrSave(event.target, 'date');
  })

  document.querySelector('#edit-duration').addEventListener('click', (event) => {
    editOrSave(event.target, 'duration');
  })

  document.querySelector('#edit-content').addEventListener('click', (event) => {
    editOrSave(event.target, 'content');
  })

  document.querySelector('#delete-btn').addEventListener('click', (event) => {
    const tutID = document.querySelector('#tut_id').getAttribute('data-tut_id');
    deleteTutoring(tutID);
  })
})

// Decides wether UI should be updated  (for editing) or data saved
function editOrSave(button, fieldType) {
  if (button.classList.contains('Edit')) {
    editTut(fieldType)
  } else {
    var newFieldInput = document.querySelector(`#new_${fieldType}`)
    saveTut(
      document.querySelector('#tut_id').getAttribute('data-tut_id'), // tutID
      { [fieldType]: newFieldInput.value }
    ) // dict with all props to change
      .then((newDict) => {
        // update UI after saving
        // update spans with new values
        const field = document.querySelector(`#tut_${fieldType}`)
        const newSpan = document.createElement('span')
        newSpan.id = `tut_${fieldType}`
        newSpan.innerHTML = newDict[fieldType]
        newFieldInput.parentNode.replaceChild(newSpan, newFieldInput)

        // switch back to edit button
        const editButton = document.querySelector(`#edit-${fieldType}`)
        editButton.innerHTML = 'Edit'
        editButton.classList.toggle('Save', false)
        editButton.classList.toggle('Edit', true)
      })
  }
}

// Visual update: Replace field with new input and save button for all three
// fields
function editTut(fieldType) {
  // Replace field span with input
  var field = document.querySelector(`#tut_${fieldType}`)
  var newField

  if (fieldType === 'date') {
    // Create a date picker for the 'date' field
    newField = document.createElement('input')
    newField.type = 'date'
  } else {
    // For 'duration' and 'content' fields, create a text input
    newField = document.createElement('input')
    newField.type = 'text'
  }

  newField.id = `new_${fieldType}`
  newField.value = field.innerText // Set the initial value
  field.parentNode.replaceChild(newField, field)

  // Edit Button -> Save Button, also exchange classes
  var button = document.querySelector(`#edit-${fieldType}`)
  button.innerHTML = 'Save'
  button.classList.toggle('Save', true)
  button.classList.toggle('Edit', false)
}

// Data update: the actual change saving
function saveTut(tutID, newDict) {
  // validate and collect props to edit
  const keysToUpdate = Object.keys(newDict) // keys from newDict
  const updatePayload = {} // store props to update
  keysToUpdate.forEach((key) => {
    // check per key if valid prop (for Tutoring model)
    if (['date', 'duration', 'subject', 'teacher', 'student', 'content'].includes(key)) {
      // If the key is valid, add it to the updatePayload
      if (key === 'date' && newDict[key]) {
        // Format the date as yyyy-mm-dd
        updatePayload[key] = new Date(newDict[key]).toISOString().split('T')[0]
      } else {
        updatePayload[key] = newDict[key]
      }
    }
  })

  // PUT edit request to backend
  return fetch(`/tutoring/${tutID}`, {
    method: 'PUT',
    body: JSON.stringify(updatePayload),
  }).then((response) => {
    if (response.ok) {
      return updatePayload // returns updated data
    }
    throw new Error('Failed to save data')
  });
}

function deleteTutoring(tutID) {
  return fetch(`/tutoring/${tutID}`, {
    method: 'DELETE',
  }).then((response) => {
      if (response.ok) {
        // Deleting success
        window.location.href = '/';
      } else {
        console.error('Failed to delete tutoring:', response.statusText)
      }
    })
    .catch((error) => {
      console.error('Error:', error)
    })
}