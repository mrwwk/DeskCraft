const openButton = document.getElementById('openDialog');
const legacyModal = document.getElementById('legacyModal');

openButton.addEventListener('click', () => {
  legacyModal.classList.add('is-open');
});
