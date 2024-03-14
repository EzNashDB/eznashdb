import React from "react";
import { createRoot } from "react-dom/client";
import { ShulsMap } from "../components/ShulsMap";

["DOMContentLoaded", "shulsDataLoaded"].forEach((eventType) => {
  document.addEventListener(eventType, (e) => {
    const shulsMapContainer = document.getElementById("shulsMap");
    createRoot(shulsMapContainer).render(<ShulsMap shuls={shuls} />);
  });
});
