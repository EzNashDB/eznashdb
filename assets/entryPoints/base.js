import setBodyHeight from "../initializers/bodyHeight";
import initializeScrollShadows from "../initializers/scrollShadows";
import initializeTomSelects from "../initializers/tomSelect";
import initializeTooltips from "../initializers/tooltips";

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

  onDocumentEvent("DOMContentLoaded", [
    setBodyHeight,
    initializeTooltips,
    initializeTomSelects,
    initializeScrollShadows,
  ]);
  onDocumentEvent("formsetInitialized", [initializeTomSelects]);
  onDOMChange([initializeTomSelects, initializeTooltips]);
  window.addEventListener("resize", setBodyHeight);
})();
