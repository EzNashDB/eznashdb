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
      isInitialized = tooltipTriggerEl.attributes["aria-describedby"];
      if (!isInitialized) {
        new bootstrap.Tooltip(tooltipTriggerEl);
      }
    });
  }

  function getOptgroupForOption(option) {
    // Traverse the parent elements and return the first optgroup if found
    var parent = option.parentNode;
    while (parent !== null) {
      if (parent.tagName === "OPTGROUP") {
        return parent;
      } else if (parent.tagName === "SELECT") {
        return null;
      }
      parent = parent.parentNode;
    }
    return null; // Return null if no optgroup is found
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
        window.opts = options;
        options.each(function () {
          let label = "";
          const optgroup = getOptgroupForOption(this);
          if (optgroup) {
            label += `${optgroup.label} - `;
          }
          if ($(this).attr("label") !== undefined) {
            label += $(this).attr("label");
          } else {
            label += $(this).html();
          }
          labels.push(label);
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

  onDocumentEvent("DOMContentLoaded", [
    setBodyHeight,
    initializeTooltips,
    initializeMultiselects,
  ]);
  onDocumentEvent("formsetInitialized", [initializeMultiselects]);
  onDOMChange([initializeMultiselects, initializeTooltips]);
  window.addEventListener("resize", setBodyHeight);
})();
