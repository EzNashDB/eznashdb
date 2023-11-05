import React, { useState } from "react";
import {
  AsyncTypeahead,
  Hint,
  Menu,
  MenuItem,
} from "react-bootstrap-typeahead";
import { Form } from "react-bootstrap";

const SEARCH_URI = "/address-lookup";

export const AddressSearch = ({ display_name, lat, lon, place_id }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [options, setOptions] = useState([]);
  const [selected, setSelected] = useState({
    display_name,
    lat,
    lon,
    place_id,
  });

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

  const handleChange = (options) => {
    setSelected(options[0]);
  };

  // Bypass client-side filtering by returning `true`. Results are already
  // filtered by the search endpoint, so no need to do it again.
  const filterBy = () => true;
  return (
    <>
      <AsyncTypeahead
        className="w-100 position-relative"
        filterBy={filterBy}
        id="address-select"
        isLoading={isLoading}
        labelKey="display_name"
        minLength={3}
        onSearch={handleSearch}
        onChange={handleChange}
        useCache={false}
        options={options}
        placeholder="Search for an address..."
        inputProps={{
          name: "address",
          className: "textinput form-control py-0",
          autoComplete: "one-time-code",
        }}
        defaultInputValue={display_name}
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
      <input
        type="hidden"
        name="latitude"
        id="id_latitude"
        value={selected?.lat || ""}
      ></input>
      <input
        type="hidden"
        name="longitude"
        id="id_longitude"
        value={selected?.lon || ""}
      ></input>
      <input
        type="hidden"
        name="place_id"
        id="id_place_id"
        value={selected?.place_id || ""}
      ></input>
    </>
  );
};
