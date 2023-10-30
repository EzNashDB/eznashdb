import React, { useState } from "react";
import { Popup } from "react-leaflet";
import { Card, ListGroup } from "react-bootstrap";

export const ShulPopup = ({ shul }) => {
  const boolToIcon = (bool) => {
    if (bool === true) {
      return <i class="fa-solid fa-check"></i>;
    } else if (bool === false) {
      return <i class="fa-solid fa-xmark"></i>;
    } else {
      return "--";
    }
  };
  return (
    <Popup>
      <Card>
        <Card.Header className="p-2">
          <a
            className="btn btn-xs text-primary link-primary py-0 me-1"
            href={`/shuls/${shul.id}/update`}
          >
            <i class="fa-solid fa-pen-to-square"></i>
          </a>
          {shul.name}
        </Card.Header>
        <Card.Body className="p-2 pb-1">
          <div className="small">
            <span className="me-1">
              <i class="fa-solid fa-location-dot"></i>
            </span>
            {shul.address}
          </div>
          <hr className="my-1" />
          <div className="d-flex justify-content-between">
            <span>Childcare: {boolToIcon(shul.has_childcare)}</span>
            <span>Kaddish: {boolToIcon(shul.can_say_kaddish)}</span>
            <span>
              Female Leadership: {boolToIcon(shul.has_female_leadership)}
            </span>
          </div>
        </Card.Body>
        <ListGroup variant="flush">
          <ListGroup.Item>Room 1</ListGroup.Item>
          <ListGroup.Item>Room 2</ListGroup.Item>
        </ListGroup>
      </Card>
    </Popup>
  );
};
