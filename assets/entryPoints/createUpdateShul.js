import React from "react";
import { createRoot } from "react-dom/client";
import { AddressInput } from "../components/AddressInput";

const initAddressInput = () => {
  const addressInput = document.querySelector("input[name=address]");
  const addressParent = addressInput.parentElement;
  // Wrap input in container div to use as react root
  const addressContainer = document.createElement("div");
  addressContainer.appendChild(addressInput);
  addressParent.appendChild(addressContainer);
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
  createRoot(addressContainer).render(<AddressInput {...getProps()} />);
};
document.addEventListener("DOMContentLoaded", initAddressInput);
document.addEventListener("htmx:afterSettle", initAddressInput);
