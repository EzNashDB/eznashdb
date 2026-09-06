import React from "react";
import { Modal, Button } from "react-bootstrap";

export const LimitedResultsModal = ({ show, onHide }) => {
  return (
    <Modal show={show} onHide={onHide} centered>
      <Modal.Header closeButton>
        <Modal.Title>
          {gettext("Why are some results unavailable?")}
        </Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <p>
          {gettext(
            "We usually show address search results from Google Maps and OpenStreetMap, but to keep costs low, we limit how many searches use Google each day."
          )}
        </p>
        <p>
          {gettext("Right now, you're only seeing results from OpenStreetMap.")}
        </p>
        <p className="mb-0">
          {gettext(
            "If your shul doesn't appear in the results, try searching for the city or street, then drag the map to the right location."
          )}
        </p>
      </Modal.Body>
      <Modal.Footer>
        <Button variant="primary" onClick={onHide}>
          {gettext("Got it")}
        </Button>
      </Modal.Footer>
    </Modal>
  );
};
