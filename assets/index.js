import React from "react";
import { createRoot } from "react-dom/client";
import { AddressSearch } from "./components/AddressSearch";
import { ShulsMap } from "./components/ShulsMap";

document.addEventListener("DOMContentLoaded", () => {
  const addressInputContainer = document.querySelector(
    "input[name=address]"
  ).parentElement;
  if (addressInputContainer) {
    createRoot(addressInputContainer).render(<AddressSearch />);
  }

  const shulsMapContainer = document.getElementById("shulsMap");
  if (shulsMapContainer) {
    console.log(shuls);
    createRoot(shulsMapContainer).render(<ShulsMap shuls={shuls} />);
  }
});
