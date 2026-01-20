import React, { useState, useRef } from "react";
import { Modal } from "react-bootstrap";
import { AddressInput } from "./AddressInput";

export const AddressInputWithModal = ({
  display_name,
  lat,
  lon,
  place_id,
  zoom,
  initialIsValid,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [placeholderHeight, setPlaceholderHeight] = useState(null);
  const inlineRef = useRef(null);

  // Lift state to parent so it persists across remounts
  const hasCoordsInProps = !!String(lat) && !!String(lon);
  const initialLocation = useRef({
    display_name,
    lat,
    lon,
    place_id,
    zoom: zoom || (hasCoordsInProps ? 16 : 1),
  }).current;

  const [currLocation, setCurrLocation] = useState(initialLocation);
  const [inputValue, setInputValue] = useState({ display_name });

  const handleExpand = () => {
    if (inlineRef.current) {
      setPlaceholderHeight(inlineRef.current.offsetHeight);
    }
    setIsExpanded(true);
  };

  return (
    <>
      {/* Inline version with placeholder to prevent page jump */}
      {isExpanded ? (
        <div style={{ height: placeholderHeight }}></div>
      ) : (
        <div ref={inlineRef}>
          <AddressInput
            initialLocation={initialLocation}
            currLocation={currLocation}
            setCurrLocation={setCurrLocation}
            inputValue={inputValue}
            setInputValue={setInputValue}
            initialIsValid={initialIsValid}
            onExpand={handleExpand}
          />
        </div>
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
        <Modal.Footer className="justify-content-end">
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => setIsExpanded(false)}
          >
            Done Editing
          </button>
        </Modal.Footer>
      </Modal>
    </>
  );
};
