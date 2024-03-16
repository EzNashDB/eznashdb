import React from "react";
import { createRoot } from "react-dom/client";
import { ShulsMap } from "../components/ShulsMap";

const renderMap = () => {
  const shulsMapContainer = document.getElementById("shuls-map");
  createRoot(shulsMapContainer).render(<ShulsMap />);
};

const renderShulCount = () => {
  const shulCountContainer = document.getElementById("shuls-count");
  const count = shuls.length;
  const shulsLabel = shuls.length == 1 ? "shul" : "shuls";
  shulCountContainer.innerHTML = `${count} ${shulsLabel}`;
};

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

document.addEventListener("DOMContentLoaded", (e) => {
  renderMap();
  renderShulCount();
});

document.addEventListener("htmx:beforeSend", (e) => {
  new SpinnerManager().show();
});

document.addEventListener("shulsDataLoaded", (e) => {
  new SpinnerManager().hide();
  renderShulCount();
});
