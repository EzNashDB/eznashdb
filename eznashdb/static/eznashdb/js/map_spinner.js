class SpinnerManager {
  constructor() {
    this._spinnerOverlays = Array.from(
      document.getElementsByClassName("spinner-overlay")
    );
  }

  show() {
    this._spinnerOverlays.forEach((spinner) => {
      spinner.classList.remove("opacity-0");
      spinner.classList.add("opacity-50");
    });
  }

  hide() {
    this._spinnerOverlays.forEach((spinner) => {
      spinner.classList.add("opacity-0");
      spinner.classList.remove("opacity-50");
    });
  }
}

document.addEventListener("htmx:beforeSend", (e) => {
  // Show spinner only for elements with data-show-spinner
  const shouldShowSpinner = e.target.closest("[data-show-spinner]");
  if (shouldShowSpinner) {
    new SpinnerManager().show();
  }
});

document.addEventListener("htmx:afterSwap", (e) => {
  // Hide spinner after HTMX swaps (but shulsDataLoaded will also hide it)
  const shouldShowSpinner = e.target.closest("[data-show-spinner]");
  if (shouldShowSpinner) {
    new SpinnerManager().hide();
  }
});

document.addEventListener("shulsDataLoaded", (e) => {
  new SpinnerManager().hide();
});
