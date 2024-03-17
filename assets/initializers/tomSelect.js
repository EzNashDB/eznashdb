import TomSelect from "tom-select";

export default function initializeTomSelects() {
  document.querySelectorAll("select.tom-select").forEach((el) => {
    if (!!el.tomselect) return;
    let settings = {
      controlInput: null,
      dropdownParent: "body",
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
}
