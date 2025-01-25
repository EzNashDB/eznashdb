import React, { useCallback, useEffect, useState } from "react";

import {
  MapContainer,
  TileLayer,
  useMapEvents,
  ZoomControl,
} from "react-leaflet";
import { useMap } from "react-leaflet/hooks";
import { GestureHandling } from "leaflet-gesture-handling";
import "leaflet-gesture-handling/dist/leaflet-gesture-handling.css";
import "../vendor/leaflet-history/base.js";
import "../vendor/leaflet-history/base.css";
import Control from "react-leaflet-custom-control";
import { AddressTypeAhead } from "./AddressTypeAhead2.js";

export const AddressMap2 = ({
  display_name,
  lat,
  lon,
  place_id,
  initialIsValid,
}) => {
  const [inputValue, setInputValue] = useState(display_name);
  const hasCoordsInProps = !!String(lat) && !!String(lon);
  const zoom = hasCoordsInProps ? 16 : 1;
  const onMoveEnd = (e) => {
    console.log(e);
  };
  const MapEvents = useCallback(() => {
    useMapEvents({
      dragend: onMoveEnd,
      zoomend: onMoveEnd,
    });
    return null;
  }, [onMoveEnd]);

  const ChangeMapState = ({ center, zoom, dragging }) => {
    const map = useMap();
    window.addressMap = map;

    useEffect(() => {
      const historyControl = new L.HistoryControl({}).addTo(map);
      // const oldCenter = map.getCenter();
      // const [newLat, newLng] = center;
      // const isNewCenter = newLat !== oldCenter.lat || newLng !== oldCenter.lng;
      // const isNewZoom = zoom !== map.getZoom();
      // if (isNewCenter || isNewZoom) {
      // map.setView(center, zoom);
      // }
      return () => {
        // Remove the control if needed
        map.removeControl(historyControl);
      };
    }, [map, center, zoom]);

    return null;
  };

  const gestureControllerCss = `
    .leaflet-container:after {
          font-size: 1.5em;
        }
  `;

  return (
    <div style={{ minHeight: "180px" }} className="position-relative">
      <div className="h-100 d-inline-block w-100 position-absolute">
        <div
          className="position-absolute click-through"
          style={{
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -100%)",
            zIndex: 401, // Above map TileLayer
          }}
        >
          <img src="/static/dist/images/marker-icon-2x.png" height="38"></img>
        </div>
        <style>{gestureControllerCss}</style>
        <MapContainer
          center={[lat, lon]}
          zoom={zoom}
          minZoom={1}
          zoomControl={false}
          scrollWheelZoom={true}
          dragging={true}
          worldCopyJump={true}
          gestureHandling={true}
          className="position-relative rounded h-100"
        >
          <ChangeMapState center={[lat, lon]} zoom={zoom} dragging={true} />
          <MapEvents />
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <ZoomControl position="bottomleft" />
          <Control prepend position="topleft">
            <AddressTypeAhead
              inputValue={inputValue}
              onInput={setInputValue}
              onAddressSelected={(e) => {
                console.log(e);
              }}
              isValid={true}
            />
          </Control>
        </MapContainer>
      </div>
    </div>
  );
};
