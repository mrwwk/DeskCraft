const form = document.getElementById('request-form');
const emailInput = document.getElementById('email');
const errorMessage = document.getElementById('error-message');

form.addEventListener('submit', (event) => {
  event.preventDefault();
  if (!emailInput.value) {
    errorMessage.classList.add('visible');
  }
});
