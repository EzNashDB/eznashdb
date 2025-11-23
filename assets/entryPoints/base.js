import setBodyHeight from "../initializers/bodyHeight";
import initializeTomSelects from "../initializers/tomSelect";
import initializeTooltips from "../initializers/tooltips";
import Alpine from "alpinejs";

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

  function initializeAlpine() {
    window.Alpine = Alpine;
    Alpine.start();
  }

  onDocumentEvent("DOMContentLoaded", [
    setBodyHeight,
    initializeTooltips,
    initializeTomSelects,
    initializeAlpine,
  ]);
  onDocumentEvent("formset-initialized", [initializeTomSelects]);
  onDOMChange([initializeTomSelects, initializeTooltips]);
  onDocumentEvent("htmx:afterSettle", [initializeTomSelects]);
  window.addEventListener("resize", setBodyHeight);
})();
