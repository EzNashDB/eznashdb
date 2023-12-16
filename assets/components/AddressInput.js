import React, { useCallback, useState } from "react";
import { Button, ButtonGroup } from "react-bootstrap";
import { AddressMap } from "./AddressMap";
import { AddressTypeAhead } from "./AddressTypeAhead";

export const AddressInput = ({ display_name, lat, lon, place_id }) => {
  const hasCoordsInProps = !!parseFloat(lat) && !!parseFloat(lon);
  const [zoom, setZoom] = useState(hasCoordsInProps ? 16 : 1);
  const [inputValue, setInputValue] = useState({ display_name });
  const [locationHistory, setLocationHistory] = useState({
    locations: [
      {
        display_name,
        lat: lat || 0,
        lon: lon || 0,
        place_id,
      },
    ],
    currIdx: 0,
  });

  const setNewLocation = (location) => {
    const prevLocations = locationHistory.locations.slice(
      0,
      locationHistory.currIdx + 1
    );
    const newLocations = [...prevLocations, location];
    setLocationHistory({
      locations: newLocations,
      currIdx: newLocations.length - 1,
    });
  };

  const goToLocationByIndex = (locationIndex) => {
    setLocationHistory({
      ...locationHistory,
      currIdx: locationIndex,
    });
    setInputValue(locationHistory.locations[locationIndex].display_name);
  };

  const goToPrevLocation = (e) => {
    const newIdx = locationHistory.currIdx - 1;
    if (newIdx >= 0) {
      goToLocationByIndex(newIdx);
    }
  };

  const goToNextLocation = (e) => {
    const newIdx = locationHistory.currIdx + 1;
    if (newIdx < locationHistory.locations.length) {
      goToLocationByIndex(newIdx);
    }
  };

  const currLocation = locationHistory.locations[locationHistory.currIdx];

  const handleMapMoveEnd = useCallback(
    (e) => {
      const map = e.target;
      const center = map.getCenter();
      if (
        center.lat.toString() !== currLocation.lat.toString() ||
        center.lng.toString() !== currLocation.lon.toString()
      ) {
        setNewLocation({
          lat: center.lat,
          lon: center.lng,
          place_id: null,
          display_name: `${center.lat}, ${center.lng}`,
        });
        setInputValue({ display_name: `${center.lat}, ${center.lng}` });
      }
      setZoom(map.getZoom());
    },
    [locationHistory]
  );

  const handleAddressSelected = (address) => {
    setZoom(16);
    setInputValue({ display_name: address.display_name });
    setNewLocation(address);
  };

  const handleOnInput = (text) => {
    setInputValue({ display_name: text });
  };

  return (
    <div
      className="h-100 d-inline-block w-100 position-relative"
      style={{ minHeight: "200px" }}
    >
      <div
        className="position-absolute w-100 p-2 pb-0"
        style={{
          zIndex: 1021, // Over leaflet attribution, sticky headers, etc.
        }}
      >
        <div className="d-flex flex-row">
          <ButtonGroup className="me-1">
            <Button
              size="sm"
              variant="light"
              disabled={locationHistory.currIdx === 0}
              className="shadow-sm"
              onClick={goToPrevLocation}
            >
              <i className="fa-solid fa-angle-left"></i>
            </Button>
            <Button
              size="sm"
              variant="light"
              disabled={
                locationHistory.currIdx === locationHistory.locations.length - 1
              }
              className="shadow-sm"
              onClick={goToNextLocation}
            >
              <i className="fa-solid fa-angle-right"></i>
            </Button>
          </ButtonGroup>
          <AddressTypeAhead
            inputValue={inputValue}
            onInput={handleOnInput}
            onAddressSelected={handleAddressSelected}
          />
        </div>
      </div>
      <input
        type="hidden"
        name="latitude"
        id="id_latitude"
        value={currLocation?.lat || ""}
      ></input>
      <input
        type="hidden"
        name="longitude"
        id="id_longitude"
        value={currLocation?.lon || ""}
      ></input>
      <input
        type="hidden"
        name="place_id"
        id="id_place_id"
        value={currLocation?.place_id || ""}
      ></input>
      <AddressMap
        lat={parseFloat(currLocation.lat)}
        lon={parseFloat(currLocation.lon)}
        zoom={zoom}
        onMoveEnd={handleMapMoveEnd}
      />
    </div>
  );
};
