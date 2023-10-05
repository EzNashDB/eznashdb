import React from "react";
import { createRoot } from "react-dom/client";
import { AddressSearch } from "./components/AddressSearch";

const addressInputContainer = document.querySelector(
  "input[name=address]"
).parentElement;
if (addressInputContainer) {
  createRoot(addressInputContainer).render(<AddressSearch />);
}
