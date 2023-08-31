import React from "react";
import ReactDOM from "react-dom";
import Autocomplete from "./vendor/bootstrap5-autocomplete/autocomplete";

const reactTestRoot = document.getElementById("react-hello");
if (reactTestRoot) {
  ReactDOM.render(<h1>Hello, react!</h1>, reactTestRoot);
}

const opts = {
  onSelectItem: console.log,
};
var src = [];
for (let i = 0; i < 50; i++) {
  src.push({
    title: "Option " + i,
    id: "opt" + i,
    data: {
      key: i,
    },
  });
}
Autocomplete.init("input.autocomplete", {
  items: src,
  valueField: "id",
  labelField: "title",
  highlightTyped: true,
  onSelectItem: console.log,
});

Autocomplete.init("input[name=city]", {
  items: src,
  valueField: "id",
  labelField: "title",
  highlightTyped: true,
  fullWidth: true,
  onSelectItem: console.log,
});
