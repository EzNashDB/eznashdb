import React from "react";
import { createRoot } from "react-dom/client";
import { AddressInput } from "../components/AddressInput";

document.addEventListener("DOMContentLoaded", () => {
  const addressInput = document.querySelector("input[name=address]");
  const addressInputContainer = addressInput.parentElement;
  if (addressInputContainer) {
    const getProps = () => {
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
      values["initialIsValid"] = !("address" in shulForm.errors);
      return values;
    };
    createRoot(addressInputContainer).render(<AddressInput {...getProps()} />);
  }
});
