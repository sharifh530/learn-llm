document.querySelectorAll("[data-preview]").forEach(button => button.addEventListener("click", () => {
  document.querySelectorAll("[data-preview]").forEach(choice => choice.setAttribute("aria-pressed", String(choice === button)));
  document.querySelector("#preview-feedback").textContent = button.dataset.preview === "tea"
    ? "Tea fits the usual pattern. A likely next word is a prediction, not a fact check."
    : `${button.dataset.preview === "socks" ? "Socks" : "Moon"} could fit a silly story. Tea is the ordinary continuation here. Try another guess.`;
}));
