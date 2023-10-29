import React, { useState } from "react";
import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";
import MarkerClusterGroup from "react-leaflet-cluster";
import { ShulPopup } from "./ShulPopup";

export const ShulsMap = (shuls) => {
  shuls.shuls.forEach((shul) => {
    console.log(shul);
  });
  const latLonShuls = shuls.shuls.filter(
    (shul) => shul.fields.latitude && shul.fields.longitude
  );

  return (
    <MapContainer
      center={[20, 10]}
      zoom={2}
      scrollWheelZoom={true}
      style={{ height: "100%" }}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <MarkerClusterGroup chunkedLoading showCoverageOnHover={false}>
        {latLonShuls.map((shul, index) => (
          <Marker
            key={index}
            position={[shul.fields.latitude, shul.fields.longitude]}
          >
            <ShulPopup shul={shul} />
          </Marker>
        ))}
      </MarkerClusterGroup>
    </MapContainer>
  );
};
