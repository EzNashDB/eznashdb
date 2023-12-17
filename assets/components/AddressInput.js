import React, { useCallback, useState } from "react";
import { Button, ButtonGroup } from "react-bootstrap";
import { AddressMap } from "./AddressMap";
import { AddressTypeAhead } from "./AddressTypeAhead";
import { isRoundedEqual } from "../utils/math";

export const AddressInput = ({ display_name, lat, lon, place_id }) => {
  const hasCoordsInProps = !!parseFloat(lat) && !!parseFloat(lon);
  const [inputValue, setInputValue] = useState({ display_name });
  const [locationHistory, setLocationHistory] = useState({
    locations: [
      {
        display_name,
        lat: lat || 0,
        lon: lon || 0,
        place_id,
        zoom: hasCoordsInProps ? 16 : 1,
      },
    ],
    currIdx: 0,
  });

  const setNewLocation = (location) => {
    const prevLocations = locationHistory.locations.slice(
      0,
      locationHistory.currIdx + 1
    );
    location.lat = parseFloat(location.lat);
    location.lon = parseFloat(location.lon);
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
    setInputValue({
      display_name: locationHistory.locations[locationIndex].display_name,
    });
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
      const [newLat, newLon, oldLat, oldLon] = [
        center.lat,
        center.lng,
        currLocation.lat,
        currLocation.lon,
      ].map(parseFloat);
      // Round to nearest .00001 to avoid triggering when map shifts on resize
      const isNewCenter =
        !isRoundedEqual(oldLat, newLat, 5) ||
        !isRoundedEqual(oldLon, newLon, 5);
      const isNewZoom = map.getZoom() !== currLocation.zoom;
      if (isNewCenter) {
        setNewLocation({
          lat: center.lat,
          lon: center.lng,
          place_id: null,
          display_name: `${newLat}, ${newLon}`,
          zoom: map.getZoom(),
        });
        setInputValue({ display_name: `${newLat}, ${newLon}` });
      } else if (isNewZoom) {
        setNewLocation({
          ...currLocation,
          zoom: map.getZoom(),
        });
      }
    },
    [locationHistory]
  );

  const handleAddressSelected = (address) => {
    setInputValue({ display_name: address.display_name });
    setNewLocation({ ...address, zoom: 16 });
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
          <ButtonGroup className="me-1 shadow-sm">
            <Button
              size="sm"
              variant="light"
              disabled={locationHistory.currIdx === 0}
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
        lat={currLocation.lat}
        lon={currLocation.lon}
        zoom={currLocation.zoom}
        onMoveEnd={handleMapMoveEnd}
      />
    </div>
  );
};
