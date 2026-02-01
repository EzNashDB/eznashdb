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
import { v4 as uuidv4 } from "uuid";

const SEARCH_URL = "/address-lookup";
const DETAILS_URL = "/address-lookup/details";

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
  const [sessionToken, setSessionToken] = useState(() => uuidv4());
  const inputIsHebrew = hasHebrew(inputValue.display_name);
  const handleSearch = (query) => {
    setSearchQuery(query);
  };

  useEffect(() => {
    if (!debouncedSearchQuery) return;
    setIsLoading(true);
    fetch(
      `${SEARCH_URL}?q=${debouncedSearchQuery}&session_token=${sessionToken}`
    )
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
  }, [debouncedSearchQuery, sessionToken]);

  const handleChange = (selected) => {
    const option = selected[0];
    if (option) {
      // If this is a Google Places result, fetch details first
      if (option.source === "google") {
        setIsLoading(true);
        fetch(
          `${DETAILS_URL}?place_id=${option.place_id}&session_token=${sessionToken}`
        )
          .then((resp) => resp.json())
          .then((details) => {
            if (details.error) {
              throw new Error(details.error);
            }
            // Pass the enriched option with coordinates
            onAddressSelected(details);
            // Reset session token after successful selection
            setSessionToken(uuidv4());
          })
          .catch((error) => {
            console.error("Error fetching place details:", error);
            setIsSearchError(true);
          })
          .finally(() => {
            setIsLoading(false);
          });
      } else {
        // OSM result already has coordinates
        onAddressSelected(option);
        // Reset session token for next search
        setSessionToken(uuidv4());
      }
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
      No results found. <br />
      Try searching city or street, then drag the map.
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
