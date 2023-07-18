(function setBodyHeight() {
  function resetBodyHeight() {
    document.body.style.height = window.innerHeight + "px";
  }
  window.addEventListener("resize", resetBodyHeight);
  resetBodyHeight();
})();

(function initializeTooltips() {
  onEventsAndDOMChange(() => {
    const tooltipTriggerList = document.querySelectorAll(
      '[data-bs-toggle="tooltip"]'
    );
    const tooltipList = [...tooltipTriggerList].map((tooltipTriggerEl) => {
      isInitialized = tooltipTriggerEl.attributes["aria-describedby"];
      if (!isInitialized) {
        new bootstrap.Tooltip(tooltipTriggerEl);
      }
    });
  });
})();

(function initializeMultiselects() {
  onEventsAndDOMChange(() => {
    $(".bs-multiselect").multiselect({
      includeSelectAllOption: true,
      buttonClass: "form-select",
      buttonWidth: "100%",
      widthSynchronizationMode: "always",
      enableHTML: true,
      buttonText: function (options, select) {
        var labels = [];
        options.each(function () {
          if ($(this).attr("label") !== undefined) {
            labels.push($(this).attr("label"));
          } else {
            labels.push($(this).html());
          }
        });
        const labelList = labels.join(", ") + "";
        if (options.length === 0) {
          return "--------";
        } else if (options.length > 1) {
          return `<span class="badge bg-light text-dark">${options.length}</span> ${labelList}`;
        } else {
          return labelList;
        }
      },
      templates: {
        button:
          '<button type="button" class="multiselect dropdown-toggle d-block" data-bs-toggle="dropdown"><div class="multiselect-selected-text text-start"></div></button>',
        popupContainer:
          '<div class="multiselect-container dropdown-menu position-fixed shadow-lg"></div>',
        option:
          '<button type="button" class="multiselect-option dropdown-item text-wrap"></button>',
      },
    });
  }, (triggerEvents = ["DOMContentLoaded", "formsetInitialized"]));
})();

function onEventsAndDOMChange(func, triggerEvents) {
  const events = triggerEvents || ["DOMContentLoaded"];
  events.forEach((eventName) => document.addEventListener(eventName, func));
  onDOMChange(func);
}

function onDOMChange(func) {
  const targetElement = document.querySelector("body");
  const options = {
    childList: true,
    subtree: true,
  };
  const observer = new MutationObserver((mutationsList, observer) => {
    observer.disconnect();
    func();
    observer.observe(targetElement, options);
  });
  observer.observe(targetElement, options);
}
