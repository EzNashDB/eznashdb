import React, { useState } from "react";
import { Popup } from "react-leaflet";
import { Card, ListGroup } from "react-bootstrap";

export const ShulPopup = ({ shul }) => {
  return (
    <Popup>
      <Card style={{ width: "18rem" }}>
        <Card.Header className="p-2">{shul.fields.name}</Card.Header>
        <Card.Body className="p-2">{shul.fields.address}</Card.Body>
        <ListGroup variant="flush">
          <ListGroup.Item>Room 1</ListGroup.Item>
          <ListGroup.Item>Room 2</ListGroup.Item>
        </ListGroup>
      </Card>
    </Popup>
  );
};
