import React, { useState, useRef } from "react";
import { Modal } from "react-bootstrap";
import { AddressInput } from "./AddressInput";

export const AddressInputWithModal = ({
  display_name,
  lat,
  lon,
  place_id,
  initialIsValid,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  // Lift state to parent so it persists across remounts
  const hasCoordsInProps = !!String(lat) && !!String(lon);
  const initialLocation = useRef({
    display_name,
    lat,
    lon,
    place_id,
    zoom: hasCoordsInProps ? 16 : 1,
  }).current;

  const [currLocation, setCurrLocation] = useState(initialLocation);
  const [inputValue, setInputValue] = useState({ display_name });

  return (
    <>
      {/* Inline version with placeholder to prevent page jump */}
      {isExpanded ? (
        // Placeholder matching exact structure of inline version
        <div>
          <div className="text-muted small mb-2">
            Try: "Young Israel, Teaneck" or street address
          </div>
          <div
            className="w-100 position-relative d-inline-block"
            style={{ minHeight: "250px" }}
          ></div>
          <span className="invalid-feedback">
            <strong>Please select a valid address.</strong>
          </span>
        </div>
      ) : (
        <AddressInput
          initialLocation={initialLocation}
          currLocation={currLocation}
          setCurrLocation={setCurrLocation}
          inputValue={inputValue}
          setInputValue={setInputValue}
          initialIsValid={initialIsValid}
          onExpand={() => setIsExpanded(true)}
        />
      )}

      {/* Modal version - always render for animations */}
      <Modal
        show={isExpanded}
        onHide={() => setIsExpanded(false)}
        size="lg"
        fullscreen="md-down"
      >
        <Modal.Header closeButton>
          <Modal.Title>Select Location</Modal.Title>
        </Modal.Header>
        <Modal.Body style={{ height: "70vh", maxHeight: "800px" }}>
          {isExpanded && (
            <AddressInput
              initialLocation={initialLocation}
              currLocation={currLocation}
              setCurrLocation={setCurrLocation}
              inputValue={inputValue}
              setInputValue={setInputValue}
              initialIsValid={initialIsValid}
              isModal={true}
            />
          )}
        </Modal.Body>
      </Modal>
    </>
  );
};
