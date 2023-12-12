import React, { useState, useEffect } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  useMapEvents,
  ZoomControl,
} from "react-leaflet";
import MarkerClusterGroup from "react-leaflet-cluster";
import { ShulPopup } from "./ShulPopup";
import "../css/map.css";

export const ShulsMap = ({ shuls }) => {
  // Based on https://stackoverflow.com/a/67825424
  const [markersDoneLoading, setMarkersDoneLoading] = React.useState(false);
  const markerRefs = React.useRef({});

  useEffect(() => {
    let params = new URLSearchParams(document.location.search.substring(1));
    let id = params.get("selectedPin");
    if (id && markersDoneLoading) {
      const markerToOpen = markerRefs.current[id];
      if (markerToOpen) markerToOpen.openPopup();
    }
  }, [markersDoneLoading]);

  const copiedShuls = shuls
    .map((shul) => {
      const copy1 = { ...shul };
      const copy2 = { ...shul };
      copy1.longitude = (parseFloat(shul.longitude) + 360).toString();
      copy2.longitude = (parseFloat(shul.longitude) - 360).toString();
      copy1.id = `+${shul.id}`;
      copy2.id = `-${shul.id}`;
      return [shul, copy1, copy2];
    })
    .flat();

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

  const latLonShuls = copiedShuls.filter(
    (shul) => shul.latitude && shul.longitude
  );
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
      <MarkerClusterGroup chunkedLoading showCoverageOnHover={false}>
        {latLonShuls.map((shul, index) => (
          <Marker
            key={index}
            position={[shul.latitude, shul.longitude]}
            ref={(m) => {
              markerRefs.current[shul.id] = m;
              if (index === shuls.length - 1 && !markersDoneLoading) {
                setMarkersDoneLoading(true);
              }
            }}
          >
            <ShulPopup shul={shul} />
          </Marker>
        ))}
      </MarkerClusterGroup>
      <ZoomControl position="bottomleft" />
    </MapContainer>
  );
};
