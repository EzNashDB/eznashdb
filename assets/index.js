import React from "react";
import { createRoot } from "react-dom/client";
import { AddressInput } from "./components/AddressInput";
import { ShulsMap } from "./components/ShulsMap";

document.addEventListener("DOMContentLoaded", () => {
  const addressInput = document.querySelector("input[name=address]");
  if (!!addressInput) {
    const addressInputContainer = addressInput.parentElement;
    if (addressInputContainer) {
      const getPropsFromInputs = () => {
        const propsToInputNames = {
          display_name: "address",
          lat: "latitude",
          lon: "longitude",
          place_id: "place_id",
        };
        const values = {};
        for (const prop in propsToInputNames) {
          const inputName = propsToInputNames[prop];
          const input = document.querySelector(`input[name=${inputName}]`);
          values[prop] = input ? input.value : "";
        }
        return values;
      };
      createRoot(addressInputContainer).render(
        <AddressInput {...getPropsFromInputs()} />
      );
    }
  }

  const shulsMapContainer = document.getElementById("shulsMap");
  if (shulsMapContainer) {
    createRoot(shulsMapContainer).render(<ShulsMap shuls={shuls} />);
  }
});
