import React from "react";
import { createRoot } from "react-dom/client";
import { AddressInputWithModal } from "../components/AddressInputWithModal";

const initAddressInput = () => {
  // Server-rendered placeholder that already reserves the map's height, with
  // the (hidden) address input already inside it - see shul_form.html. Skip
  // if already initialized, or not rendered yet.
  const addressContainer = document.getElementById("address-map-container");
  if (!addressContainer || addressContainer.dataset.addressInputInitialized) {
    return;
  }
  if (!addressContainer.querySelector("input[name=address]")) return;
  addressContainer.dataset.addressInputInitialized = "true";
  // createRoot() below replaces the placeholder (hidden input + spinner)
  // with the rendered map.
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
