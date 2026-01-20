import React from "react";
import { createRoot } from "react-dom/client";
import { AddressInputWithModal } from "../components/AddressInputWithModal";

const initAddressInput = () => {
  const addressInput = document.querySelector("input[name=address]");
  if (!addressInput) return; // Exit if address input doesn't exist

  // Check if already initialized
  const existingContainer = addressInput.closest(
    "div[data-address-input-initialized]"
  );
  if (existingContainer) return; // Exit if already initialized

  const addressParent = addressInput.parentElement;
  // Wrap input in container div to use as react root
  const addressContainer = document.createElement("div");
  addressContainer.setAttribute("data-address-input-initialized", "true");
  addressContainer.appendChild(addressInput);
  addressParent.appendChild(addressContainer);
  const getProps = () => {
    const propsToInputNames = {
      display_name: "address",
      lat: "latitude",
      lon: "longitude",
      place_id: "place_id",
      zoom: "zoom",
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
  createRoot(addressContainer).render(
    <AddressInputWithModal {...getProps()} />
  );
};
document.addEventListener("DOMContentLoaded", initAddressInput);
document.addEventListener("htmx:afterSettle", (e) => {
  // Only re-init if the settled element contains an address input
  // This prevents feedback form from triggering re-initialization
  if (e.target.querySelector && e.target.querySelector("input[name=address]")) {
    initAddressInput();
  }
});
