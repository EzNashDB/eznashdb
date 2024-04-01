import React, { useEffect, useState } from "react";
import {
  AsyncTypeahead,
  Hint,
  Menu,
  MenuItem,
} from "react-bootstrap-typeahead";
import { Form, InputGroup } from "react-bootstrap";
import { useDebounce } from "use-debounce";
import { hasHebrew } from "../utils/text";

const SEARCH_URL = "/address-lookup";

export const AddressTypeAhead = ({
  inputValue,
  onInput,
  onAddressSelected,
  isValid,
  isDisabled,
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [options, setOptions] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedSearchQuery] = useDebounce(searchQuery, 1000);
  const inputIsHebrew = hasHebrew(inputValue.display_name);
  const handleSearch = (query) => {
    setSearchQuery(query);
  };

  useEffect(() => {
    if (!debouncedSearchQuery) return;
    setIsLoading(true);
    fetch(`${SEARCH_URL}?q=${debouncedSearchQuery}`)
      .then((resp) => resp.json())
      .then((items) => {
        setOptions(items);
        setIsLoading(false);
      })
      .catch((error) => {
        console.error("Error:", error);
      });
  }, [debouncedSearchQuery]);

  const handleChange = (selected) => {
    const option = selected[0];
    if (option) {
      onAddressSelected(option);
    }
  };

  const handleInputChange = (text, e) => {
    onInput(text);
    handleSearch(text);
  };

  useEffect(() => {
    setOptions([]);
  }, [inputValue]);

  // Bypass client-side filtering by returning `true`. Results are already
  // filtered by the search endpoint, so no need to do it again.
  const filterBy = () => true;
  return (
    <AsyncTypeahead
      selected={[inputValue]}
      className="w-100 position-relative shadow-sm"
      filterBy={filterBy}
      id="address-select"
      isLoading={isLoading}
      labelKey="display_name"
      minLength={3}
      onSearch={handleSearch}
      onChange={handleChange}
      useCache={false}
      options={options}
      onInputChange={handleInputChange}
      placeholder="Search or drag..."
      inputProps={{
        name: "address",
        className: `${!isValid && "is-invalid"}`,
        autoComplete: "one-time-code",
        dir: `${inputIsHebrew ? "rtl" : "ltr"}`,
        lang: `${inputIsHebrew ? "he" : "en"}`,
        readOnly: isDisabled,
      }}
      renderInput={({ inputRef, referenceElementRef, ...inputProps }) => (
        <Hint>
          <InputGroup size="sm">
            <Form.Control
              {...inputProps}
              ref={(node) => {
                inputRef(node);
                referenceElementRef(node);
              }}
            />
          </InputGroup>
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
          <Menu {..._menuProps} className="shadow-lg">
            {results.map((result, index) => {
              const isHebrew = hasHebrew(result.display_name);
              return (
                <MenuItem
                  option={result}
                  position={index}
                  key={index}
                  dir={isHebrew ? "rtl" : "ltr"}
                  lang={isHebrew ? "he" : "en"}
                >
                  <span className="text-wrap">{result.display_name}</span>
                </MenuItem>
              );
            })}
          </Menu>
        );
      }}
    />
  );
};
