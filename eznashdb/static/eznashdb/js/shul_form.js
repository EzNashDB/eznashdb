const setupNoChildcareInputListeners = () => {
  const getChildcareFormsetInputs = () => {
    const childcareFormset =
      document.getElementsByClassName("childcare-formset")[0];
    return childcareFormset.querySelectorAll(
      'input[type="text"]:not([hidden]), select:not([hidden])'
    );
  };
  const hasProgramInfo = () => {
    const childcareInputs = getChildcareFormsetInputs();
    let hasValue = false;

    childcareInputs.forEach(function (input) {
      if (
        input.value.trim() !== "" ||
        (input.tagName === "SELECT" && input.value !== "")
      ) {
        console.log(input.value, input);
        hasValue = true;
      }
    });
    return hasValue;
  };
  const autoSetNoChildcareInput = () => {
    const noChildcareInput = document.getElementById("id_has_no_childcare");
    if (hasProgramInfo()) {
      noChildcareInput.disabled = true;
      noChildcareInput.checked = false;
    } else {
      noChildcareInput.disabled = false;
    }
  };
  const autoSetOnChange = () => {
    // on DOM change
    (() => {
      const targetElement = document.querySelector(
        ".js-childcare-formset-parent"
      );
      const options = {
        childList: true,
        subtree: true,
      };
      const observer = new MutationObserver((mutationsList, observer) => {
        observer.disconnect();
        autoSetNoChildcareInput();
        observer.observe(targetElement, options);
      });
      observer.observe(targetElement, options);
    })();

    // on input change
    getChildcareFormsetInputs().forEach((input) => {
      if (!input.dataset.js_autosetting_no_childcare) {
        ["change", "input"].forEach((eventType) => {
          input.addEventListener(eventType, function () {
            autoSetNoChildcareInput();
          });
        });
        input.dataset.js_autosetting_no_childcare = true;
      }
    });
  };
  autoSetNoChildcareInput();
  autoSetOnChange();
};

document.addEventListener("DOMContentLoaded", () => {
  setupNoChildcareInputListeners();
});
