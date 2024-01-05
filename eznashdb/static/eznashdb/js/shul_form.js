const setupNoChildcareInputListeners = () => {
  const registeredInputs = new Set();
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
  const autoSetOnInputChange = () => {
    const unregisteredInputs = Array.from(getChildcareFormsetInputs()).filter(
      (input) => !registeredInputs.has(input)
    );
    unregisteredInputs.forEach((input) => {
      ["change", "input"].forEach((eventType) => {
        input.addEventListener(eventType, function () {
          autoSetNoChildcareInput();
        });
      });
      registeredInputs.add(input);
    });
  };
  const autoSetOnDOMChange = () => {
    const targetElement = document.querySelector(
      ".js-childcare-formset-parent"
    );
    const options = {
      childList: true,
      subtree: true,
    };
    const observer = new MutationObserver((mutationsList, observer) => {
      autoSetNoChildcareInput();
      autoSetOnInputChange();
    });
    observer.observe(targetElement, options);
  };
  const autoSetOnChange = () => {
    autoSetOnDOMChange();
    autoSetOnInputChange();
  };
  autoSetNoChildcareInput();
  autoSetOnChange();
};

document.addEventListener("DOMContentLoaded", () => {
  setupNoChildcareInputListeners();
});
