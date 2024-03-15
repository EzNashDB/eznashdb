import React from "react";
import { createRoot } from "react-dom/client";
import { ShulsMap } from "../components/ShulsMap";

const renderMap = () => {
  const shulsMapContainer = document.getElementById("shulsMap");
  createRoot(shulsMapContainer).render(<ShulsMap shuls={shuls} />);
};

const renderShulCount = () => {
  const shulCountContainer = document.getElementById("shuls-count");
  const count = shuls.length;
  const shulsLabel = shuls.length == 1 ? "shul" : "shuls";
  shulCountContainer.innerHTML = `${count} ${shulsLabel} found`;
};

["DOMContentLoaded", "shulsDataLoaded"].forEach((eventType) => {
  document.addEventListener(eventType, (e) => {
    renderMap();
    renderShulCount();
  });
});
