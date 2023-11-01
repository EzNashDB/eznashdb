import React, { useState } from "react";
import { MapContainer, TileLayer, Marker, useMapEvents } from "react-leaflet";
import MarkerClusterGroup from "react-leaflet-cluster";
import { ShulPopup } from "./ShulPopup";
import "../css/map.css";

export const ShulsMap = ({ shuls }) => {
  const updateURLParam = (key, value) => {
    const url = new URL(window.location.href);
    url.searchParams.set(key, value);
    const newURL = url.toString();
    history.pushState({}, document.title, newURL);
  };
  const MapEvents = () => {
    useMapEvents({
      dragend: (e) => {
        const center = e.target.getCenter();
        updateURLParam("lat", center.lat);
        updateURLParam("lon", center.lng);
      },
      zoomend: (e) => {
        updateURLParam("zoom", e.target.getZoom());
      },
    });
    return null;
  };

  const latLonShuls = shuls.filter((shul) => shul.latitude && shul.longitude);
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
    >
      <MapEvents />
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <MarkerClusterGroup chunkedLoading showCoverageOnHover={false}>
        {latLonShuls.map((shul, index) => (
          <Marker key={index} position={[shul.latitude, shul.longitude]}>
            <ShulPopup shul={shul} />
          </Marker>
        ))}
      </MarkerClusterGroup>
    </MapContainer>
  );
};
