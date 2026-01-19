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
  // Don't show spinner for feedback form requests
  const isFeedbackRequest = e.detail.requestConfig.path?.includes("/feedback/");
  if (!isFeedbackRequest) {
    new SpinnerManager().show();
  }
});

document.addEventListener("htmx:afterSwap", (e) => {
  // Hide spinner after HTMX swaps (but shulsDataLoaded will also hide it)
  const isFeedbackRequest =
    e.detail.requestConfig?.path?.includes("/feedback/");
  if (!isFeedbackRequest) {
    new SpinnerManager().hide();
  }
});

document.addEventListener("shulsDataLoaded", (e) => {
  new SpinnerManager().hide();
});
