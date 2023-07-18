(function setBodyHeight() {
  function resetBodyHeight() {
    document.body.style.height = window.innerHeight + "px";
  }
  window.addEventListener("resize", resetBodyHeight);
  resetBodyHeight();
})();

(function initializeTooltips() {
  const initialize = () => {
    const tooltipTriggerList = document.querySelectorAll(
      '[data-bs-toggle="tooltip"]'
    );
    const tooltipList = [...tooltipTriggerList].map((tooltipTriggerEl) => {
      isInitialized = tooltipTriggerEl.attributes["aria-describedby"];
      if (!isInitialized) {
        new bootstrap.Tooltip(tooltipTriggerEl);
      }
    });
  };
  document.addEventListener("DOMContentLoaded", function () {
    initialize();
    const observer = new MutationObserver((mutationsList, observer) => {
      initialize();
    });
    const targetElement = document.querySelector("body");
    const options = {
      childList: true,
      subtree: true,
    };
    observer.observe(targetElement, options);
  });
})();

(function initializeMultiselects() {
  const initialize = () => {
    $(".bs-multiselect").multiselect({
      includeSelectAllOption: true,
      buttonClass: "form-select",
      buttonWidth: "100%",
      buttonText: function (options, select) {
        if (options.length === 0) {
          return "--------";
        } else if (options.length > 1) {
          return `${options.length} selected`;
        } else {
          var labels = [];
          options.each(function () {
            if ($(this).attr("label") !== undefined) {
              labels.push($(this).attr("label"));
            } else {
              labels.push($(this).html());
            }
          });
          return labels.join(", ") + "";
        }
      },
      templates: {
        button:
          '<button type="button" class="multiselect dropdown-toggle d-block" data-bs-toggle="dropdown"><div class="multiselect-selected-text text-start"></div></button>',
      },
    });
  };

  $(document).ready(function () {
    initialize();
  });
  const observer = new MutationObserver((mutationsList, observer) => {
    initialize();
  });
  const targetElement = document.querySelector("body");
  const options = {
    childList: true,
    subtree: true,
  };
  observer.observe(targetElement, options);
})();
