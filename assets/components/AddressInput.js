import React, { useCallback, useState, useEffect, useRef } from "react";
import { Button } from "react-bootstrap";
import { AddressMap } from "./AddressMap";
import { AddressTypeAhead } from "./AddressTypeAhead";
import { isRoundedEqual } from "../utils/math";

export const AddressInput = ({
  // Controlled props from parent (new controlled mode)
  initialLocation,
  currLocation,
  setCurrLocation,
  inputValue,
  setInputValue,
  initialIsValid,
  // Optional props
  onExpand, // callback to open modal
  isModal = false, // whether rendering in modal
}) => {
  const isValid = initialIsValid;
  const isFirstRender = useRef(true);

  // Dispatch change events when lat/lon change
  useEffect(() => {
    // Skip the first render
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }

    const latInput = document.getElementById("id_latitude");
    const lonInput = document.getElementById("id_longitude");

    if (latInput && currLocation.lat) {
      latInput.dispatchEvent(new Event("change", { bubbles: true }));
    }
    if (lonInput && currLocation.lon) {
      lonInput.dispatchEvent(new Event("change", { bubbles: true }));
    }
  }, [currLocation.lat, currLocation.lon]);

  const resetLocation = () => {
    setCurrLocation(initialLocation);
    setInputValue({
      display_name: initialLocation.display_name,
    });
  };

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
        setCurrLocation({
          lat: String(center.lat),
          lon: String(center.lng),
          place_id: null,
          display_name: `${newLat}, ${newLon}`,
          zoom: map.getZoom(),
        });
        setInputValue({ display_name: `${newLat}, ${newLon}` });
      } else if (isNewZoom) {
        setCurrLocation({
          ...currLocation,
          zoom: map.getZoom(),
        });
      }
    },
    [currLocation]
  );

  const handleAddressSelected = (address) => {
    setInputValue({ display_name: address.display_name });
    setCurrLocation({ ...address, zoom: 16 });
  };

  const handleOnInput = (text) => {
    setInputValue({ display_name: text });
  };

  return (
    <div className={isModal ? "d-flex flex-column h-100" : ""}>
      <div className="text-muted small mb-2">
        Can't find your shul? Search city or street, then drag map
      </div>
      <div
        className={`w-100 position-relative ${!isValid && "is-invalid"} ${
          isModal ? "flex-grow-1" : "d-inline-block"
        }`}
        style={{ minHeight: isModal ? "0" : "250px" }}
      >
        <AddressMap
          lat={currLocation.lat}
          lon={currLocation.lon}
          zoom={currLocation.zoom}
          onMoveEnd={handleMapMoveEnd}
          isModal={isModal}
        />
        <div
          className="position-absolute w-100 p-2 pb-0"
          style={{
            zIndex: 1021, // Over leaflet attribution, sticky headers, etc.
            pointerEvents: "none",
          }}
        >
          <div style={{ pointerEvents: "auto" }}>
            <AddressTypeAhead
              inputValue={inputValue}
              onInput={handleOnInput}
              onAddressSelected={handleAddressSelected}
              isValid={isValid}
            />
          </div>
          <div className="d-flex justify-content-between mt-2">
            <Button
              className="shadow-sm"
              variant="light"
              size="sm"
              disabled={currLocation == initialLocation}
              onClick={resetLocation}
              style={{ pointerEvents: "auto" }}
            >
              <i className="fa-solid fa-rotate-left me-1"></i>
              Reset
            </Button>
            {!isModal && onExpand && (
              <Button
                variant="light"
                size="sm"
                className="shadow-sm"
                onClick={onExpand}
                style={{ pointerEvents: "auto" }}
              >
                <i className="fa-solid fa-expand me-1"></i>
                Expand
              </Button>
            )}
          </div>
        </div>
        <input
          type="hidden"
          name="latitude"
          id="id_latitude"
          value={`${currLocation?.lat || ""}`}
        ></input>
        <input
          type="hidden"
          name="longitude"
          id="id_longitude"
          value={`${currLocation?.lon || ""}`}
        ></input>
        <input
          type="hidden"
          name="place_id"
          id="id_place_id"
          value={`${currLocation?.place_id || ""}`}
        ></input>
      </div>
      {!isModal && (
        <span className="invalid-feedback">
          <strong>Please select a valid address.</strong>
        </span>
      )}
    </div>
  );
};
