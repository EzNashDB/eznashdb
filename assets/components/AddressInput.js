import React, { useCallback, useState } from "react";
import { Button } from "react-bootstrap";
import { AddressMap } from "./AddressMap";
import { AddressTypeAhead } from "./AddressTypeAhead";

export const AddressInput = ({ display_name, lat, lon, place_id }) => {
  const hasCoordsInProps = !!parseFloat(lat) && !!parseFloat(lon);
  const [zoom, setZoom] = useState(hasCoordsInProps ? 16 : 1);
  const [selectedLoc, setSelectedLoc] = useState({
    display_name,
    lat: lat || 0,
    lon: lon || 0,
    place_id,
  });
  const [inputValue, setInputValue] = useState({ display_name });

  const handleMapMoveEnd = useCallback(
    (e) => {
      const map = e.target;
      const center = map.getCenter();
      if (
        center.lat.toString() !== selectedLoc.lat.toString() ||
        center.lng.toString() !== selectedLoc.lon.toString()
      ) {
        setSelectedLoc({
          lat: center.lat,
          lon: center.lng,
          place_id: null,
          display_name: `${center.lat}, ${center.lng}`,
        });
        setInputValue({ display_name: `${center.lat}, ${center.lng}` });
        setOptions([]);
      }
      setZoom(map.getZoom());
    },
    [selectedLoc]
  );

  const handleAddressSelected = (address) => {
    setZoom(16);
    setInputValue({ display_name: address.display_name });
    setSelectedLoc(address);
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
        <AddressTypeAhead
          inputValue={inputValue}
          onInput={handleOnInput}
          onAddressSelected={handleAddressSelected}
        />
        <div className="pt-1">
          <Button size="sm" variant="light" disabled className="me-1 shadow-sm">
            <i className="fa-solid fa-angle-left"></i>
          </Button>
          <Button size="sm" variant="light" disabled className="shadow-sm">
            <i className="fa-solid fa-angle-right"></i>
          </Button>
        </div>
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
      <AddressMap
        lat={selectedLoc.lat}
        lon={selectedLoc.lon}
        zoom={zoom}
        onMoveEnd={handleMapMoveEnd}
      />
    </div>
  );
};
