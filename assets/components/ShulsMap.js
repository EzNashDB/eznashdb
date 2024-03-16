import React from "react";
import {
  MapContainer,
  TileLayer,
  useMapEvents,
  ZoomControl,
} from "react-leaflet";
import "../css/map.css";
import { ShulsMarkerClusterGroup } from "./ShulMarkerClusterGroup";

export const ShulsMap = () => {
  const updateURLParams = (params) => {
    const url = new URL(window.location.href);
    for (const key in params) url.searchParams.set(key, params[key]);
    const newURL = url.toString();
    history.replaceState({}, "", newURL);
  };
  const deleteURLParams = (params) => {
    const url = new URL(window.location.href);
    params.forEach((param) => url.searchParams.delete(param));
    const newURL = url.toString();
    history.replaceState({}, "", newURL);
  };
  const updateURLLocationParams = (e) => {
    const center = e.target.getCenter();
    updateURLParams({
      lat: center.lat,
      lon: center.lng,
      zoom: e.target.getZoom(),
    });
  };
  const MapEvents = () => {
    useMapEvents({
      moveend: (e) => updateURLLocationParams(e),
      zoomend: (e) => updateURLLocationParams(e),
      popupopen: (e) => updateURLParams({ selectedPin: e.popup.options.id }),
      popupclose: (e) => deleteURLParams(["selectedPin"]),
    });
    return null;
  };

  const urlParams = new URLSearchParams(window.location.search);
  let startLat = urlParams.get("lat") || 20;
  let startLon = urlParams.get("lon") || 10;
  let startZoom = urlParams.get("zoom") || 2;

  return (
    <MapContainer
      center={[startLat, startLon]}
      zoom={startZoom}
      scrollWheelZoom={true}
      style={{ height: "100%" }}
      worldCopyJump={true}
      minZoom={1}
      zoomControl={false}
    >
      <MapEvents />
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <ShulsMarkerClusterGroup />
      <ZoomControl position="bottomleft" />
    </MapContainer>
  );
};
