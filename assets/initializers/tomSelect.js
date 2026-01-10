import TomSelect from "tom-select";

export default function initializeTomSelects() {
  document.querySelectorAll("select.tom-select").forEach((el) => {
    if (!!el.tomselect) return;
    const isMultiSelect = el.hasAttribute("multiple");
    const renderUnescapedContent = (data, escape) => {
      // prefer explicit data.html, then option.innerHTML, otherwise escape the text
      const html =
        data.html ?? data.$option?.innerHTML ?? escape(data.text ?? "");
      return `<div>${html}</div>`;
    };
    const isSearchable = el.dataset.searchable === "true";
    let settings = {
      dropdownParent: "body",
      render: {
        option: renderUnescapedContent,
        item: renderUnescapedContent,
      },
      onInitialize: function () {
        updateSelectedDisplay(this);
      },
      onItemAdd: function () {
        updateSelectedDisplay(this);
      },
      onItemRemove: function () {
        updateSelectedDisplay(this);
      },
      onChange: function (value) {
        let option = this.options[value];
        let html = option?.html || option?.text || value;

        window.dispatchEvent(
          new CustomEvent("tom-select-changed", {
            detail: {
              html: html,
              fieldName: this.input.name,
              fieldId: this.input.id,
              element: this.input,
            },
          })
        );
      },
      plugins: {
        ...(isMultiSelect && {
          checkbox_options: {
            checkedClassNames: ["ts-checked"],
            uncheckedClassNames: ["ts-unchecked"],
          },
        }),
        clear_button: {
          title: (isMultiSelect && "Clear All") || "Clear",
        },
        no_backspace_delete: true,
      },
    };
    // Disable search input for non-searchable dropdowns
    if (!isSearchable) {
      settings.controlInput = null;
    }
    new TomSelect(el, settings);
  });
  function updateSelectedDisplay(instance) {
    // Based on https://stackoverflow.com/a/76879570/11278892
    const selectedItems = instance.control.querySelectorAll(".item");
    let childElement = instance.control.querySelector("#ts-placeholder");
    const numSelected = selectedItems.length;

    if (numSelected > 1) {
      // hide all existing
      selectedItems.forEach(function (item) {
        item.hidden = true;
      });
      if (!childElement) {
        // add dummy
        const divElement = document.createElement("div");
        // Set attributes
        divElement.setAttribute("id", "ts-placeholder");
        // Set content
        divElement.textContent = numSelected + " items selected";
        // Place the placeholder before the input so the text cursor appears after it when focused.
        const input = instance.control.querySelector("input");
        instance.control.insertBefore(divElement, input);
      } else {
        childElement = instance.control.querySelector("#ts-placeholder");
        childElement.textContent = numSelected + " items selected";
      }
    } else {
      selectedItems.forEach(function (item) {
        item.hidden = false;
      });
      childElement = instance.control.querySelector("#ts-placeholder");
      if (childElement) {
        instance.control.removeChild(childElement);
      }
    }

    // Fix dropdown position after control height changes.
    // Changing the control's content above can cause the dropdown to misalign.
    // Wait for layout to complete, then recalculate the correct position.
    if (instance.isOpen) {
      requestAnimationFrame(() => {
        const rect = instance.control.getBoundingClientRect();
        instance.dropdown.style.top = `${rect.bottom}px`;
        instance.dropdown.style.left = `${rect.left}px`;
      });
    }
  }
}
