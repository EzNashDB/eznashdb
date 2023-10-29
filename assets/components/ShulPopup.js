import React, { useState } from "react";
import { Popup } from "react-leaflet";
import { Card, ListGroup } from "react-bootstrap";

export const ShulPopup = ({ shul }) => {
  const boolToIcon = (bool) => {
    console.log(bool);
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
        <Card.Header className="p-2">{shul.fields.name}</Card.Header>
        <Card.Body className="p-2 pb-1">
          <div className="small">
            <span className="me-1">
              <i class="fa-solid fa-location-dot"></i>
            </span>
            {shul.fields.address}
          </div>
          <hr className="my-1" />
          <div className="d-flex justify-content-between">
            <span>Childcare: {boolToIcon(shul.fields.has_childcare)}</span>
            <span>Kaddish: {boolToIcon(shul.fields.can_say_kaddish)}</span>
            <span>
              Female Leadership: {boolToIcon(shul.fields.has_female_leadership)}
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
