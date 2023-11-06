(() => {
  function onEvent(eventName, funcs) {
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
      isInitialized = tooltipTriggerEl.attributes["aria-describedby"];
      if (!isInitialized) {
        new bootstrap.Tooltip(tooltipTriggerEl);
      }
    });
  }

  function initializeMultiselects() {
    $(".bs-multiselect").multiselect({
      includeSelectAllOption: true,
      buttonClass: "form-select",
      buttonWidth: "100%",
      widthSynchronizationMode: "ifPopupIsSmaller",
      enableHTML: true,
      buttonTitle: (options, select) => null,
      buttonText: function (options, select) {
        var labels = [];
        options.each(function () {
          if ($(this).attr("label") !== undefined) {
            labels.push($(this).attr("label"));
          } else {
            labels.push($(this).html());
          }
        });
        const labelList = labels.join("; ") + "";
        if (options.length === 0) {
          return "---------";
        } else {
          return `
            <span>
              <span
                class="badge bg-secondary-subtle text-dark"
                data-bs-toggle="tooltip"
                data-bs-title="${options.length} selected: ${labelList}"
              >${options.length}</span>
              <span>${labelList}</span>
            </span>
          `;
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
  }

  onEvent("DOMContentLoaded", [
    setBodyHeight,
    initializeTooltips,
    initializeMultiselects,
  ]);
  onEvent("resize", [setBodyHeight]);
  onEvent("formsetInitialized", [initializeMultiselects]);
  onDOMChange([initializeMultiselects, initializeTooltips]);
})();
