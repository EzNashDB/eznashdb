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

  const handleLocateMe = () => {
    if (!navigator.geolocation) {
      alert("Geolocation is not supported by your browser");
      return;
    }
    if (!window.isSecureContext) {
      alert("Location requires a secure connection (HTTPS)");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords;
        setCurrLocation({
          lat: String(latitude),
          lon: String(longitude),
          place_id: null,
          display_name: `${latitude}, ${longitude}`,
          zoom: 14,
        });
        setInputValue({ display_name: `${latitude}, ${longitude}` });
      },
      (error) => {
        let message;
        switch (error.code) {
          case error.PERMISSION_DENIED:
            message =
              "Location access was denied. Check your browser's site settings to enable location.";
            break;
          case error.POSITION_UNAVAILABLE:
            message = "Location information is unavailable. Please try again.";
            break;
          case error.TIMEOUT:
            message = "Location request timed out. Please try again.";
            break;
          default:
            message = "Unable to retrieve your location.";
        }
        alert(message);
      },
      {
        enableHighAccuracy: false,
        timeout: 10000,
        maximumAge: 300000,
      }
    );
  };

  return (
    <div className={isModal ? "d-flex flex-column h-100" : ""}>
      <div className="text-muted small mb-2" style={{ textWrap: "pretty" }}>
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
          <div className="d-flex">
            <div style={{ pointerEvents: "auto" }} className="flex-grow-1">
              <AddressTypeAhead
                inputValue={inputValue}
                onInput={handleOnInput}
                onAddressSelected={handleAddressSelected}
                isValid={isValid}
              />
            </div>
            <div style={{ pointerEvents: "auto" }}>
              {!isModal && onExpand && (
                <Button
                  variant="light"
                  className="shadow-sm ms-2"
                  onClick={onExpand}
                  style={{ pointerEvents: "auto" }}
                >
                  <i className="fa-solid fa-expand"></i>
                </Button>
              )}
            </div>
          </div>
          <div className="d-flex flex-column gap-2 mt-2 w-fit-content">
            {waffle.flag_is_active("locate_me") && (
              <div>
                <Button
                  variant="light"
                  size="sm"
                  className="shadow-sm"
                  onClick={handleLocateMe}
                  style={{ pointerEvents: "auto" }}
                >
                  <i className="fa-solid fa-location-crosshairs me-1"></i>
                  Locate Me
                </Button>
              </div>
            )}
            <div className="w-fit-content" style={{ pointerEvents: "auto" }}>
              <Button
                className="shadow-sm"
                variant="light"
                size="sm"
                onClick={resetLocation}
                disabled={currLocation == initialLocation}
              >
                <i className="fa-solid fa-rotate-left me-1"></i>
                Reset
              </Button>
            </div>
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
