import React, { useState } from "react";
import {
  AsyncTypeahead,
  Hint,
  Menu,
  MenuItem,
} from "react-bootstrap-typeahead";
import { Form } from "react-bootstrap";

const SEARCH_URI = "/city-lookup";

export const AsyncExample = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [options, setOptions] = useState([]);

  const handleSearch = (query) => {
    setIsLoading(true);
    fetch(`${SEARCH_URI}?q=${query}`)
      .then((resp) => resp.json())
      .then((items) => {
        setOptions(items);
        setIsLoading(false);
      })
      .catch((error) => {
        console.error("Error:", error);
      });
  };

  // Bypass client-side filtering by returning `true`. Results are already
  // filtered by the search endpoint, so no need to do it again.
  const filterBy = () => true;
  return (
    <AsyncTypeahead
      className="w-100"
      filterBy={filterBy}
      id="city-select"
      isLoading={isLoading}
      labelKey="display_name"
      minLength={3}
      onSearch={handleSearch}
      useCache={false}
      options={options}
      placeholder="Search for a city..."
      inputProps={{
        className: "textinput form-control",
        autoComplete: "one-time-code",
      }}
      className="position-relative"
      renderInput={({ inputRef, referenceElementRef, ...inputProps }) => (
        <Hint>
          <div className="input-group input-group-sm">
            <Form.Control
              {...inputProps}
              ref={(node) => {
                inputRef(node);
                referenceElementRef(node);
              }}
            />
          </div>
        </Hint>
      )}
      renderMenu={(results, menuProps) => {
        const {
          newSelectionPrefix,
          paginationText,
          renderMenuItemChildren,
          ..._menuProps
        } = menuProps;
        return (
          <Menu {..._menuProps} className="position-fixed shadow-lg">
            {results.map((result, index) => (
              <MenuItem option={result} position={index} key={index}>
                <span className="text-wrap">{result.display_name}</span>
              </MenuItem>
            ))}
          </Menu>
        );
      }}
    />
  );
};
