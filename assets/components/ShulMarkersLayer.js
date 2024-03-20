import React, { useState, useRef, useEffect } from "react";
import { Marker } from "react-leaflet";
import Badge from "react-bootstrap/Badge";
import MarkerClusterGroup from "react-leaflet-cluster";
import { ShulPopup } from "./ShulPopup";
import "../css/map.css";

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

  const getShulsFoundLabel = () => {
    const shulCount = shuls.length;
    const shulsStr = shulCount === 1 ? "shul" : "shuls";
    return `${shulCount} ${shulsStr} found`;
  };

  return (
    <>
      <div className="position-absolute start-0 top-0 z-1001">
        <div className="mx-1 fw-normal fs-5 opacity-75">
          <Badge bg="dark">{getShulsFoundLabel()}</Badge>
        </div>
      </div>
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
    </>
  );
};
