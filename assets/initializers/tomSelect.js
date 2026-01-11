import TomSelect from "tom-select";

export default function initializeTomSelects() {
  document.querySelectorAll("select.tom-select").forEach((el) => {
    if (el.tomselect) return;

    const isMultiSelect = el.hasAttribute("multiple");
    const isSearchable = el.dataset.searchable === "true";
    const expandOnFocus = el.dataset.expandOnFocus === "true";

    const renderUnescapedContent = (data, escape) => {
      const html =
        data.html ?? data.$option?.innerHTML ?? escape(data.text ?? "");
      return `<div>${html}</div>`;
    };

    // Show "X items selected" when collapsed, individual items when expanded
    function updateSelectionDisplay(instance, expanded) {
      if (!isMultiSelect) return;

      const selectedItems = instance.control.querySelectorAll(".item");
      let placeholder = instance.control.querySelector("#ts-placeholder");
      const numSelected = selectedItems.length;

      if (numSelected > 1 && !expanded) {
        // Collapsed: show placeholder
        selectedItems.forEach((item) => (item.hidden = true));

        if (!placeholder) {
          placeholder = document.createElement("div");
          placeholder.setAttribute("id", "ts-placeholder");
          const input = instance.control.querySelector("input");
          instance.control.insertBefore(placeholder, input);
        }
        placeholder.textContent = numSelected + " items selected";
      } else {
        // Expanded or single item: show individual items
        selectedItems.forEach((item) => (item.hidden = false));
        placeholder?.remove();
      }

      // Fix dropdown position
      if (instance.isOpen) {
        requestAnimationFrame(() => {
          const rect = instance.control.getBoundingClientRect();
          instance.dropdown.style.top = `${rect.bottom}px`;
          instance.dropdown.style.left = `${rect.left}px`;
        });
      }
    }

    let settings = {
      dropdownParent: "body",
      highlight: false,
      render: {
        option: renderUnescapedContent,
        item: renderUnescapedContent,
      },
      onInitialize: function () {
        if (!isMultiSelect) return;

        const instance = this;
        updateSelectionDisplay(instance, false);

        if (expandOnFocus) {
          // Toggle display on focus/blur
          instance.control.addEventListener("focusin", () => {
            updateSelectionDisplay(instance, true);
          });
          instance.control.addEventListener("focusout", (e) => {
            // Only update if focus is leaving the control entirely
            if (!instance.control.contains(e.relatedTarget)) {
              updateSelectionDisplay(instance, false);
            }
          });
        }
      },
      onItemAdd: function () {
        if (!isMultiSelect) return;
        const expanded =
          expandOnFocus && this.control.contains(document.activeElement);
        updateSelectionDisplay(this, expanded);
      },
      onItemRemove: function () {
        if (!isMultiSelect) return;
        const expanded =
          expandOnFocus && this.control.contains(document.activeElement);
        updateSelectionDisplay(this, expanded);
      },
      onChange: function (value) {
        const option = this.options[value];
        const html = option?.html || option?.text || value;

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
          remove_button: {
            title: "Remove this item",
          },
        }),
        clear_button: {
          title: (isMultiSelect && "Clear All") || "Clear",
        },
        no_backspace_delete: true,
      },
    };

    if (!isSearchable) {
      settings.controlInput = null;
    }

    new TomSelect(el, settings);
  });
}
