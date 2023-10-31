import React, { useState } from "react";
import { Popup } from "react-leaflet";
import { Card, ListGroup, Badge } from "react-bootstrap";

export const ShulPopup = ({ shul }) => {
  const boolToIcon = (bool) => {
    if (bool === true) {
      return <i className="fa-solid fa-check"></i>;
    } else if (bool === false) {
      return <i className="fa-solid fa-xmark"></i>;
    } else {
      return "--";
    }
  };

  const scoreToStars = (score) => {
    if (score === "") {
      return "--";
    }
    const EMPTY_STAR = <i className="fa-regular fa-star"></i>;
    const FILLED_STAR = <i className="fa-solid fa-star"></i>;
    const stars = [];
    for (let i = 1; i <= 5; i++) {
      const star = i <= score ? FILLED_STAR : EMPTY_STAR;
      stars.push(<span key={i}>{star}</span>);
    }
    return <span className="text-nowrap text-warning">{stars}</span>;
  };
  const ROOM_LAYOUT_TYPES = {
    "Same height": {
      icon: "fa-solid fa-arrows-left-right",
      fields: {
        is_same_height_side: "Side",
        is_same_height_back: "Back",
      },
    },
    Elevated: {
      icon: "fa-solid fa-caret-up",
      fields: {
        is_elevated_side: "Side",
        is_elevated_back: "Back",
      },
    },
    Balcony: {
      icon: "fa-solid fa-stairs",
      fields: {
        is_balcony: "",
      },
    },
    "No women's section": {
      icon: "fa-solid fa-xmark",
      fields: {
        is_only_men: "",
      },
    },
    "Mixed seating": {
      icon: "fa-solid fa-children",
      fields: {
        is_mixed_seating: "",
      },
    },
  };

  const getRoomLayoutBadge = (room, layoutType) => {
    const layoutTypeData = ROOM_LAYOUT_TYPES[layoutType];
    const icon = <i className={`me-1 ${layoutTypeData.icon}`}></i>;
    const subLabels = [];
    let roomHasLayoutType = false;
    for (const field in layoutTypeData.fields) {
      if (room[field]) {
        roomHasLayoutType = true;
        subLabels.push(layoutTypeData.fields[field]);
      }
    }
    return (
      roomHasLayoutType && (
        <Badge
          bg="light"
          className="border text-dark ms-1 mt-1"
          key={layoutType}
        >
          {icon}
          <span className="fw-bold">{layoutType}</span>
          {subLabels && <span className="ms-1 fw-normal">{subLabels}</span>}
        </Badge>
      )
    );
  };

  const getRoomLayoutBadges = (room) => {
    const badges = [];
    for (const layoutType in ROOM_LAYOUT_TYPES) {
      const badge = getRoomLayoutBadge(room, layoutType);
      if (badge) {
        badges.push(badge);
      }
    }
    return badges.length > 0 ? (
      badges
    ) : (
      <Badge bg="light" className="border text-dark ms-1 mt-1">
        <div className="w-15px d-inline-block text-center">--</div>
        Room layout not saved
      </Badge>
    );
  };

  return (
    <Popup>
      <Card>
        <Card.Header className="fw-bold p-1 pe-4 d-flex align-items-center">
          <a
            className="btn btn-xs text-primary link-primary py-0 me-1"
            href={`/shuls/${shul.id}/update`}
          >
            <i className="fa-solid fa-pen-to-square"></i>
          </a>
          {shul.name}
        </Card.Header>
        <Card.Body className="p-2 pt-1">
          <div className="small text-truncate">
            <span className="me-1">
              <i className="fa-solid fa-location-dot"></i>
            </span>
            {shul.address}
          </div>
          <hr className="my-1" />
          <div className="d-flex justify-content-between small">
            <span className="me-1">
              Childcare: {boolToIcon(shul.has_childcare)}
            </span>
            <span className="me-1">
              Kaddish: {boolToIcon(shul.can_say_kaddish)}
            </span>
            <span>
              Female Leadership: {boolToIcon(shul.has_female_leadership)}
            </span>
          </div>
          <ListGroup variant="flush">
            {shul.rooms.map((room) => (
              <ListGroup.Item key={room.id} className="p-0 border-0">
                <hr className="my-1" />
                <div>
                  <div className="d-inline-block me-1">{room.name}</div>
                  <div className="d-inline-block float-end">
                    <span>
                      <Badge bg="light" className="border text-dark me-1">
                        <i className="fa-solid fa-up-right-and-down-left-from-center me-1"></i>
                        {room.relative_size || "--"}
                      </Badge>
                    </span>
                    <span>
                      <Badge bg="light" className="border text-dark me-1">
                        <i className="fa-solid fa-wheelchair me-1"></i>
                        {boolToIcon(room.is_wheelchair_accessible)}
                      </Badge>
                    </span>
                    <span>
                      <Badge bg="light" className="border text-dark">
                        <i className="fa-solid fa-volume-high me-1"></i> /{" "}
                        <i className="fa-solid fa-eye me-1"></i>
                        {scoreToStars(room.see_hear_score)}
                      </Badge>
                    </span>
                  </div>
                  <div className="d-inline-block float-end text-end w-100">
                    {getRoomLayoutBadges(room)}
                  </div>
                </div>
              </ListGroup.Item>
            ))}
          </ListGroup>
        </Card.Body>
      </Card>
    </Popup>
  );
};
