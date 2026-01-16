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
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [options, setOptions] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedSearchQuery] = useDebounce(searchQuery, 1000);
  const [isSearchError, setIsSearchError] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
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
        if (items.error) {
          throw new Error(items.error);
        }
        setOptions(items);
        setHasSearched(true);
      })
      .catch((error) => {
        setOptions([]);
        setIsSearchError(true);
        setHasSearched(true);
        console.error("Error:", error);
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [debouncedSearchQuery]);

  const handleChange = (selected) => {
    const option = selected[0];
    if (option) {
      onAddressSelected(option);
    }
  };

  const handleInputChange = (text, e) => {
    if (isSearchError) setIsSearchError(false);
    if (hasSearched) setHasSearched(false);
    onInput(text);
    handleSearch(text);
  };

  useEffect(() => {
    setOptions([]);
  }, [inputValue]);

  // Bypass client-side filtering by returning `true`. Results are already
  // filtered by the search endpoint, so no need to do it again.
  const filterBy = () => true;

  const genericSearchError = (
    <div className="alert alert-danger m-0 py-1 px-2 text-wrap" role="alert">
      An error occurred. Please try again.
    </div>
  );

  const noResultsMessage = (
    <div className="alert alert-info m-0 py-1 px-2 text-wrap" role="alert">
      No results found. Try a different search or drag the map.
    </div>
  );

  const getPromptText = () => {
    if (isSearchError) return genericSearchError;
    if (hasSearched && !isLoading && options.length === 0)
      return noResultsMessage;
    return "Type to search...";
  };

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
      placeholder="Search..."
      promptText={getPromptText()}
      inputProps={{
        name: "address",
        className: `${!isValid && "is-invalid"}`,
        autoComplete: "one-time-code",
        dir: `${inputIsHebrew ? "rtl" : "ltr"}`,
        lang: `${inputIsHebrew ? "he" : "en"}`,
      }}
      renderInput={({ inputRef, referenceElementRef, ...inputProps }) => (
        <Hint>
          <InputGroup>
            <InputGroup.Text>
              <i className="fa-solid fa-magnifying-glass"></i>
            </InputGroup.Text>
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
