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
  new SpinnerManager().show();
});

document.addEventListener("shulsDataLoaded", (e) => {
  new SpinnerManager().hide();
});
