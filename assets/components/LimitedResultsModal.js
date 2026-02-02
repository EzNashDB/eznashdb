import React from "react";
import { Modal, Button } from "react-bootstrap";

export const LimitedResultsModal = ({ show, onHide }) => {
  return (
    <Modal show={show} onHide={onHide} centered>
      <Modal.Header closeButton>
        <Modal.Title>Why are some results unavailable?</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <p>
          We use Google Maps to help find addresses, but to keep our costs low,
          we limit how many searches use Google each day.
        </p>
        <p>
          Right now, you're seeing results from OpenStreetMap, a
          community-maintained map.
        </p>
        <p className="mb-0">
          If your shul doesn't appear in the results, try searching for the city
          or street, then drag the map to the right location.
        </p>
      </Modal.Body>
      <Modal.Footer>
        <Button variant="primary" onClick={onHide}>
          Got it
        </Button>
      </Modal.Footer>
    </Modal>
  );
};
