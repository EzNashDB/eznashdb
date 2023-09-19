import React from "react";
import { createRoot } from "react-dom/client";
import { AsyncExample } from "./components/CitySelect";

const cityInputContainer =
  document.querySelector("input[name=city]").parentElement;
if (cityInputContainer) {
  createRoot(cityInputContainer).render(<AsyncExample />);
}
