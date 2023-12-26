import React, { useCallback, useEffect } from "react";

import {
  MapContainer,
  TileLayer,
  useMapEvents,
  ZoomControl,
} from "react-leaflet";
import { useMap } from "react-leaflet/hooks";

export const AddressMap = ({ lat, lon, zoom, onMoveEnd, isDisabled }) => {
  const MapEvents = useCallback(() => {
    useMapEvents({
      dragend: onMoveEnd,
      zoomend: onMoveEnd,
    });
    return null;
  }, [onMoveEnd]);

  const ChangeMapState = ({ center, zoom, dragging }) => {
    const map = useMap();

    useEffect(() => {
      const oldCenter = map.getCenter();
      const [newLat, newLng] = center;
      const isNewCenter = newLat !== oldCenter.lat || newLng !== oldCenter.lng;
      const isNewZoom = zoom !== map.getZoom();
      if (isNewCenter || isNewZoom) {
        map.setView(center, zoom);
      }
    }, [map, center, zoom]);

    useEffect(() => {
      const oldDragging = map.options.dragging;
      if (oldDragging !== dragging) {
        dragging
          ? (() => {
              map.dragging.enable();
              map.scrollWheelZoom.enable();
            })()
          : (() => {
              map.dragging.disable();
              map.scrollWheelZoom.disable();
            })();
      }
    });

    return null;
  };

  return (
    <div>
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
          center={[lat, lon]}
          zoom={zoom}
          minZoom={1}
          zoomControl={false}
          scrollWheelZoom={!isDisabled}
          dragging={!isDisabled}
          worldCopyJump={true}
          className="position-relative rounded"
          style={{ height: "100%" }}
        >
          <ChangeMapState
            center={[lat, lon]}
            zoom={zoom}
            dragging={!isDisabled}
          />
          <MapEvents />
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {!isDisabled && <ZoomControl position="bottomleft" />}
        </MapContainer>
      </div>
    </div>
  );
};
