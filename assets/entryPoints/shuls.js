import React from "react";
import { createRoot } from "react-dom/client";
import { ShulsMap } from "../components/ShulsMap";

document.addEventListener("DOMContentLoaded", () => {
  const shulsMapContainer = document.getElementById("shulsMap");
  createRoot(shulsMapContainer).render(<ShulsMap shuls={shuls} />);
});
