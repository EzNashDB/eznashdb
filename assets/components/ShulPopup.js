import React from "react";
import { Popup } from "react-leaflet";
import { Card } from "react-bootstrap";

export const ShulPopup = ({ shul, markerRef }) => {
  const boolToYesNo = (bool) => {
    let text = "--";
    if (bool === true) text = "Yes";
    else if (bool === false) text = "No";
    return <span className="small fw-bold">{text}</span>;
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

  const getRoomLayoutDisplay = (room, layoutType) => {
    const layoutTypeData = ROOM_LAYOUT_TYPES[layoutType];
    const icon = (
      <div className="w-15px d-inline-block text-center me-1">
        <i className={`${layoutTypeData.icon}`}></i>
      </div>
    );
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
        <div className="d-flex align-items-top">
          {icon}
          <span>
            <span className="fw-bold">{layoutType}</span>
            {subLabels && (
              <span className="ms-1 fw-normal">{subLabels.join(", ")}</span>
            )}
          </span>
        </div>
      )
    );
  };

  const getRoomLayoutDisplays = (room) => {
    let displays = Object.keys(ROOM_LAYOUT_TYPES)
      .map((layoutType) => getRoomLayoutDisplay(room, layoutType))
      .filter((display) => !!display)
      .map((display, i) => <div key={i}>{display}</div>);
    return displays.length > 0 ? (
      displays
    ) : (
      <div className="d-flex align-items-center">
        <div className="w-15px d-inline-block text-center me-1">--</div>
        No layout info saved
      </div>
    );
  };

  return (
    <Popup id={shul.id} className="shul-popup" closeButton={false}>
      <Card
        style={{
          // push below shul totals badge
          marginTop: "40px",
        }}
      >
        <Card.Header className="fw-bold p-1 d-flex align-items-center">
          <a
            className="btn btn-xs text-primary link-primary py-0 me-1"
            href={`/shuls/${shul.id}/update`}
          >
            <i className="fa-solid fa-pen-to-square"></i>
          </a>
          <span className="flex-grow-1">{shul.name}</span>
          <button
            className="btn btn-sm py-0 px-1"
            onClick={(e) => markerRef.closePopup()}
          >
            <i className="fa-solid fa-xmark"></i>
          </button>
        </Card.Header>
        <Card.Body className="p-2 pt-1">
          <div
            className="striped overflow-auto row w-100 m-auto gx-0 mt-1"
            style={{ maxHeight: "75px" }}
          >
            <div className="col striped">
              {(shul.rooms.length > 0 &&
                shul.rooms.map((room, i) => (
                  <div className="row gx-0 small ps-1" key={i}>
                    <div className="col-12 col-sm-3">{room.name}</div>
                    <div className="col-3 col-sm-2">
                      <div className="row gx-0">
                        <div className="col-6">
                          <div className="d-flex align-items-center">
                            <i className="fa-solid fa-up-right-and-down-left-from-center me-1"></i>
                            <span className="small fw-bold">
                              {room.relative_size || "--"}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="col-4 col-sm-3 text-center">
                      <div className="d-flex align-items-center px-3">
                        <i className="fa-solid fa-eye me-1"></i>
                        <span className="small">
                          {scoreToStars(room.see_hear_score)}
                        </span>
                      </div>
                    </div>
                    <div className="col-5 col-sm-4 small">
                      {getRoomLayoutDisplays(room)}
                    </div>
                  </div>
                ))) || <span className="text-muted small">No rooms saved</span>}
            </div>
          </div>
        </Card.Body>
      </Card>
    </Popup>
  );
};
