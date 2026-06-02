function copyBibtex() {
  const bibtex = document.getElementById("bibtex").innerText;
  navigator.clipboard.writeText(bibtex).then(() => {
    const btn = document.getElementById("copy-btn");
    const original = btn.textContent;
    btn.textContent = "Copied!";
    setTimeout(() => {
      btn.textContent = original;
    }, 2000);
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const copyBtn = document.getElementById("copy-btn");
  if (copyBtn) {
    copyBtn.addEventListener("click", copyBibtex);
  }
});
