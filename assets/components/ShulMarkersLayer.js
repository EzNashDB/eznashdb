import React, { useState, useRef, useEffect } from "react";
import { Marker } from "react-leaflet";
import MarkerClusterGroup from "react-leaflet-cluster";
import { ShulPopup } from "./ShulPopup";
import "../css/map.css";
import { ShulsFoundCount } from "./ShulsFoundCount";
import Control from "react-leaflet-custom-control";

export const ShulMarkersLayer = () => {
  // Based on https://stackoverflow.com/a/67825424
  const [shuls, setShuls] = useState(window.shuls || []);
  const [markersDoneLoading, setMarkersDoneLoading] = useState(false);
  const markerRefs = useRef({});

  document.addEventListener("shulsDataLoaded", (e) => {
    setShuls(window.shuls);
  });

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

  const latLonShuls = copiedShuls.filter(
    (shul) => shul.latitude && shul.longitude
  );

  return (
    <>
      <Control prepend position="topright">
        <ShulsFoundCount shulCount={shuls.length} />
      </Control>
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
            <ShulPopup shul={shul} markerRef={markerRefs.current[shul.id]} />
          </Marker>
        ))}
      </MarkerClusterGroup>
    </>
  );
};
