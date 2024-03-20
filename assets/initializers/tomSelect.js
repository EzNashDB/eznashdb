import TomSelect from "tom-select";

export default function initializeTomSelects() {
  document.querySelectorAll("select.tom-select").forEach((el) => {
    if (!!el.tomselect) return;
    let settings = {
      controlInput: null,
      dropdownParent: "body",
      onInitialize: function () {
        updateSelectedDisplay(this);
      },
      onItemAdd: function () {
        updateSelectedDisplay(this);
      },
      onItemRemove: function () {
        updateSelectedDisplay(this);
      },
      plugins: {
        checkbox_options: {
          checkedClassNames: ["ts-checked"],
          uncheckedClassNames: ["ts-unchecked"],
        },
        clear_button: {
          title: "Remove all selected options",
        },
        no_backspace_delete: true,
      },
    };
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
        // Append the div element to the second last position of the desired parent element
        instance.control.insertBefore(divElement, instance.control.lastChild);
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
  }
}
