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

export const AddressTypeAhead = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [key, setKey] = useState(0);
  const [options, setOptions] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedSearchQuery] = useDebounce(searchQuery, 1000);
  const [isSearchError, setIsSearchError] = useState(false);
  const [selected, setSelected] = useState([])
  // const inputIsHebrew = hasHebrew(initialValue.display_name);
  const handleSearch = (query) => {
    console.log(searchQuery)
    setSearchQuery(query);
  };

  useEffect(() => {
    console.log("useEfect: ", searchQuery)
    console.log("debounced: ", debouncedSearchQuery)
    if (!searchQuery) return;
    setIsLoading(true);
    fetch(`${SEARCH_URL}?q=${searchQuery}`)
      .then((resp) => resp.json())
      .then((items) => {
        if (items.error) {
          throw new Error(items.error);
        }
        setOptions(items);
      })
      .catch((error) => {
        setOptions([]);
        setIsSearchError(true);
        console.error("Error:", error);
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [searchQuery]);

  const handleChange = (selected) => {
    console.log(selected)
    const option = selected[0];
    if (option) {
      setSelected(selected);
    }
  };

  // const handleInputChange = (text, e) => {
  //   onInput(text)
  //   if (isSearchError) setIsSearchError(false);
  //   handleSearch(text);
  // };

  // useEffect(() => {
  //   setOptions([]);
  // }, [inputValue]);

  // Bypass client-side filtering by returning `true`. Results are already
  // filtered by the search endpoint, so no need to do it again.
  const filterBy = () => true;

  const genericSearchError = (
    <div className="alert alert-danger m-0 py-1 px-2 text-wrap" role="alert">
      An error occurred. Please try again.
    </div>
  );

  return (
    <AsyncTypeahead
      key={key}
      // defaultInputValue={initialValue}
      selected={selected}
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
      // onInputChange={(e) => {
      //   onInput(e)
      //   console.log("input change: ", e)
      //   console.log(inputValue)
      // }}
      // onBlur={(e) => {
      //   console.log(e)
      //   onInput('some value');
      //   setKey(key + 1);
      // }}
      placeholder="Search or drag..."
      promptText={isSearchError ? genericSearchError : "Type to search..."}
      inputProps={{
        key: "address-input",
        name: "address",
        // className: `${!isValid && "is-invalid"}`,
        autoComplete: "one-time-code",
        // dir: `${inputIsHebrew ? "rtl" : "ltr"}`,
        // lang: `${inputIsHebrew ? "he" : "en"}`,
      }}
      renderInput={({ inputRef, referenceElementRef, ...inputProps }) => (
        <Hint>
          <InputGroup>
            <Form.Control
              key="address-form-control"
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
