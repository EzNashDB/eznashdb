import React from "react";
import { createRoot } from "react-dom/client";
import { AddressInput } from "../components/AddressInput";
import { ShulsMap } from "../components/ShulsMap";
import TomSelect from "tom-select";

document.addEventListener("DOMContentLoaded", () => {
  const addressInput = document.querySelector("input[name=address]");
  if (!!addressInput) {
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
      createRoot(addressInputContainer).render(
        <AddressInput {...getProps()} />
      );
    }
  }

  const shulsMapContainer = document.getElementById("shulsMap");
  if (shulsMapContainer) {
    createRoot(shulsMapContainer).render(<ShulsMap shuls={shuls} />);
  }
});

(() => {
  function onDocumentEvent(eventName, funcs) {
    funcs.forEach((func) => document.addEventListener(eventName, func));
  }

  function onDOMChange(funcs) {
    const targetElement = document.querySelector("body");
    const options = {
      childList: true,
      subtree: true,
    };
    const observer = new MutationObserver((mutationsList, observer) => {
      observer.disconnect();
      funcs.forEach((func) => func());
      observer.observe(targetElement, options);
    });
    observer.observe(targetElement, options);
  }

  function setBodyHeight() {
    document.body.style.height = window.innerHeight + "px";
  }

  function initializeTooltips() {
    const tooltipTriggerList = document.querySelectorAll(
      '[data-bs-toggle="tooltip"]'
    );
    Array.from(tooltipTriggerList).map((tooltipTriggerEl) => {
      const isInitialized = tooltipTriggerEl.attributes["aria-describedby"];
      if (!isInitialized) {
        new bootstrap.Tooltip(tooltipTriggerEl);
      }
    });
  }

  function initializeTomSelects() {
    document.querySelectorAll("select.tom-select").forEach((el) => {
      if (!!el.tomselect) return;
      let settings = {
        searchField: [],
        plugins: {
          checkbox_options: {
            checkedClassNames: ["ts-checked"],
            uncheckedClassNames: ["ts-unchecked"],
          },
          clear_button: {
            title: "Remove all selected options",
          },
          no_backspace_delete: true,
        },
      };
      new TomSelect(el, settings);
    });
  }

  onDocumentEvent("DOMContentLoaded", [
    setBodyHeight,
    initializeTooltips,
    initializeTomSelects,
  ]);
  onDocumentEvent("formsetInitialized", [initializeTomSelects]);
  onDOMChange([initializeTomSelects, initializeTooltips]);
  window.addEventListener("resize", setBodyHeight);
})();
