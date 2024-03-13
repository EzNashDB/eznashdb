import TomSelect from "tom-select";

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

  const registerAutoSubmits = () => {
    Array.from(document.getElementsByClassName("js-auto-submit")).forEach(
      (el) => el.addEventListener("change", (e) => el.submit())
    );
  };

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
        controlInput: null,
        dropdownParent: "body",
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
    registerAutoSubmits,
    initializeTooltips,
    initializeTomSelects,
  ]);
  onDocumentEvent("formsetInitialized", [initializeTomSelects]);
  onDOMChange([initializeTomSelects, initializeTooltips]);
  window.addEventListener("resize", setBodyHeight);
})();
