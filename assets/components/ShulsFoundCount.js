import React, { useRef, useEffect } from "react";
import Badge from "react-bootstrap/Badge";

export const ShulsFoundCount = ({ shulCount }) => {
  // Based on https://stackoverflow.com/a/57013052
  const divRef = useRef(null);

  useEffect(() => {
    L.DomEvent.disableClickPropagation(divRef.current);
  });

  const shulsFoundLabel = (() => {
    const shulsStr = shulCount === 1 ? "shul" : "shuls";
    return `${shulCount} ${shulsStr} found`;
  })();

  return (
    <div
      ref={divRef}
      style={{ cursor: "initial" }}
      className="mx-1 fw-normal fs-5 opacity-75"
    >
      <Badge bg="dark">{shulsFoundLabel}</Badge>
    </div>
  );
};
