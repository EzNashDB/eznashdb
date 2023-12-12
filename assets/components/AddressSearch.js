import React, { useCallback, useEffect, useState } from "react";
import {
  AsyncTypeahead,
  Hint,
  Menu,
  MenuItem,
} from "react-bootstrap-typeahead";
import { Form } from "react-bootstrap";
import {
  MapContainer,
  TileLayer,
  useMapEvents,
  ZoomControl,
} from "react-leaflet";
import { useMap } from "react-leaflet/hooks";
import { useDebounce } from "use-debounce";

const SEARCH_URL = "/address-lookup";

export const AddressSearch = ({ display_name, lat, lon, place_id }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [options, setOptions] = useState([]);
  const [zoom, setZoom] = useState(1);
  const [searchedLoc, setSearchedLoc] = useState({
    display_name,
    lat,
    lon,
    place_id,
  });
  const [draggedLoc, setDraggedLoc] = useState();
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedSearchQuery] = useDebounce(searchQuery, 250);

  const selectedLoc = draggedLoc || searchedLoc;

  const MapEvents = useCallback(() => {
    useMapEvents({
      dragend: (e) => {
        const center = e.target.getCenter();
        setDraggedLoc({
          lat: center.lat,
          lon: center.lng,
          place_id: null,
          display_name: `${center.lat}, ${center.lng}`,
        });
        setSearchedLoc(null);
        setOptions([]);
      },
      zoomend: (e) => {
        setZoom(e.target.getZoom());
      },
    });
    return null;
  }, []);

  const ChangeView = useCallback(({ center, zoom }) => {
    const map = useMap();
    map.setView(center, zoom);
    return null;
  }, []);

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
      setSearchedLoc(option);
      setZoom(16);
    }
  };

  const handleInputChange = (text, e) => {
    setSearchedLoc({ ...selectedLoc, display_name: text });
    setDraggedLoc(null);
    handleSearch(text);
  };

  // Bypass client-side filtering by returning `true`. Results are already
  // filtered by the search endpoint, so no need to do it again.
  const filterBy = () => true;
  return (
    <div
      width="500px"
      className="h-100 d-inline-block w-100 position-relative"
      style={{ minHeight: "200px" }}
    >
      <div className="position-absolute w-100 p-2 pb-0" style={{ zIndex: 500 }}>
        <AsyncTypeahead
          selected={[selectedLoc]}
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
          placeholder="Search for an address..."
          inputProps={{
            name: "address",
            className: "textinput form-control rounded",
            autoComplete: "one-time-code",
          }}
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
      </div>
      <input
        type="hidden"
        name="latitude"
        id="id_latitude"
        value={selectedLoc?.lat || ""}
      ></input>
      <input
        type="hidden"
        name="longitude"
        id="id_longitude"
        value={selectedLoc?.lon || ""}
      ></input>
      <input
        type="hidden"
        name="place_id"
        id="id_place_id"
        value={selectedLoc?.place_id || ""}
      ></input>
      <div height="500px">
        <div className="h-100 d-inline-block w-100 position-absolute">
          <div
            className="position-absolute"
            style={{
              top: "50%",
              left: "50%",
              transform: "translate(-50%, -100%)",
              zIndex: 401, // Above map TileLayer
            }}
          >
            <img
              src="/static/dist/images/marker-icon-2x.png"
              style={{
                width: "25px",
                height: "41px",
              }}
            ></img>
          </div>
          <MapContainer
            center={[selectedLoc.lat, selectedLoc.lon]}
            zoom={zoom}
            scrollWheelZoom={true}
            style={{ height: "100%" }}
            minZoom={1}
            worldCopyJump={true}
            className="position-relative rounded"
            zoomControl={false}
          >
            <ChangeView
              center={[selectedLoc.lat, selectedLoc.lon]}
              zoom={zoom}
            />
            <MapEvents />
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <ZoomControl position="bottomleft" />
          </MapContainer>
        </div>
      </div>
    </div>
  );
};
