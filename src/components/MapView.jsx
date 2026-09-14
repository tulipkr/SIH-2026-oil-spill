
import React, { useState } from "react";

import {
  MapContainer,
  TileLayer,
  ZoomControl,
  GeoJSON,
  Circle,
  CircleMarker,
  Popup
} from "react-leaflet";

import DriftLayer from "./DriftLayer";
import AISTrackLayer from "./AISTrackLayer";

import "leaflet/dist/leaflet.css";

function MapView({ runResult }) {

  // -----------------------------
  // MAP LAYER CONTROLS
  // -----------------------------

  const [showSpill, setShowSpill] = useState(true);
  const [showDrift, setShowDrift] = useState(true);
  const [showAIS, setShowAIS] = useState(true);
  const [showSource, setShowSource] = useState(true);

  // -----------------------------
  // GET DATA FROM JSON
  // -----------------------------

  const spillGeoJSON =
    runResult?.results?.spill_geometry_geojson;

  const sourceEstimate =
    runResult?.results?.source_estimate;

  // IMPORTANT:
  // Your JSON stores source coordinates here:
  //
  // source_estimate
  //     -> source_region
  //         -> geometry
  //             -> coordinates
  //
  // Coordinates are [longitude, latitude]

  const sourcePoint =
    sourceEstimate?.source_region?.geometry?.coordinates;

  const uncertaintyRadius =
    sourceEstimate?.uncertainty_radius_km;

  // -----------------------------
  // DEBUG INFORMATION
  // -----------------------------

  console.log("SOURCE ESTIMATE:", sourceEstimate);
  console.log("SOURCE POINT:", sourcePoint);

  // -----------------------------
  // CONVERT GEOJSON COORDINATES
  // -----------------------------

  // GeoJSON = [longitude, latitude]
  // Leaflet = [latitude, longitude]

  let sourcePosition = null;

  if (
    Array.isArray(sourcePoint) &&
    sourcePoint.length >= 2 &&
    typeof sourcePoint[0] === "number" &&
    typeof sourcePoint[1] === "number"
  ) {
    sourcePosition = [
      sourcePoint[1],
      sourcePoint[0]
    ];
  }

  return (
    <div
      style={{
        position: "relative",
        width: "100%",
        height: "100%",
        minHeight: "600px"
      }}
    >

      {/* ============================== */}
      {/* MAP */}
      {/* ============================== */}

      <MapContainer
        center={[13.24, 80.32]}
        zoom={10}
        scrollWheelZoom={true}
        zoomControl={false}
        style={{
          width: "100%",
          height: "100%"
        }}
      >

        {/* ============================== */}
        {/* BASE MAP */}
        {/* ============================== */}

        <TileLayer
          attribution="&copy; OpenStreetMap contributors"
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <ZoomControl position="bottomright" />

        {/* ============================== */}
        {/* OIL SPILL */}
        {/* ============================== */}

        {showSpill &&
          spillGeoJSON &&
          spillGeoJSON.type === "FeatureCollection" &&
          Array.isArray(spillGeoJSON.features) && (
            <GeoJSON
              data={spillGeoJSON}
              style={{
                color: "#ff3333",
                weight: 3,
                fillColor: "#ff8c00",
                fillOpacity: 0.45
              }}
              onEachFeature={(feature, layer) => {

                const properties =
                  feature?.properties || {};

                const regionId =
                  properties.region_id ||
                  "Not available";

                const area =
                  properties.area_km2 ??
                  "Not available";

                const status =
                  properties.status ||
                  "Not available";

                layer.bindPopup(`
                  <div>
                    <h3>Oil Spill Region</h3>

                    <p>
                      <strong>Region ID:</strong>
                      ${regionId}
                    </p>

                    <p>
                      <strong>Area:</strong>
                      ${area} km²
                    </p>

                    <p>
                      <strong>Status:</strong>
                      ${status}
                    </p>
                  </div>
                `);
              }}
            />
          )}

        {/* ============================== */}
        {/* DRIFT TRAJECTORY */}
        {/* ============================== */}

        {showDrift && (
          <DriftLayer
            runResult={runResult}
          />
        )}

        {/* ============================== */}
        {/* AIS TRACKS */}
        {/* ============================== */}

        {showAIS && (
          <AISTrackLayer
            runResult={runResult}
          />
        )}

        {/* ============================== */}
        {/* ESTIMATED SOURCE */}
        {/* ============================== */}

        {showSource && sourcePosition && (
          <>
            {/* ========================== */}
            {/* UNCERTAINTY CIRCLE */}
            {/* ========================== */}

            {uncertaintyRadius !== null &&
              uncertaintyRadius !== undefined && (
                <Circle
                  center={sourcePosition}
                  radius={uncertaintyRadius * 1000}
                  pathOptions={{
                    color: "#ff3333",
                    fillColor: "#ff3333",
                    fillOpacity: 0.15,
                    weight: 3
                  }}
                >
                  <Popup>
                    <div>

                      <h3>
                        Source Uncertainty
                      </h3>

                      <p>
                        <strong>
                          Radius:
                        </strong>{" "}
                        {uncertaintyRadius} km
                      </p>

                    </div>
                  </Popup>
                </Circle>
              )}

            {/* ========================== */}
            {/* SOURCE RED DOT */}
            {/* ========================== */}

            <CircleMarker
              center={sourcePosition}
              radius={12}
              pathOptions={{
                color: "#ffffff",
                fillColor: "#ff0000",
                fillOpacity: 1,
                weight: 4
              }}
            >
              <Popup>
                <div>

                  <h3>
                    Estimated Spill Source
                  </h3>

                  <p>
                    <strong>
                      Longitude:
                    </strong>{" "}
                    {sourcePoint[0]}
                  </p>

                  <p>
                    <strong>
                      Latitude:
                    </strong>{" "}
                    {sourcePoint[1]}
                  </p>

                  <p>
                    <strong>
                      Backtracking:
                    </strong>{" "}
                    {sourceEstimate?.backtracking_valid === true
                      ? "Valid"
                      : sourceEstimate?.backtracking_valid === false
                      ? "Invalid"
                      : "Not available"}
                  </p>

                  <p>
                    <strong>
                      High uncertainty:
                    </strong>{" "}
                    {sourceEstimate?.uncertainty_high === true
                      ? "Yes"
                      : sourceEstimate?.uncertainty_high === false
                      ? "No"
                      : "Not available"}
                  </p>

                  <p>
                    <strong>
                      Physically implausible:
                    </strong>{" "}
                    {sourceEstimate?.physically_implausible === true
                      ? "Yes"
                      : sourceEstimate?.physically_implausible === false
                      ? "No"
                      : "Not available"}
                  </p>

                  <p>
                    <strong>
                      Uncertainty radius:
                    </strong>{" "}
                    {uncertaintyRadius ?? "Not available"} km
                  </p>

                </div>
              </Popup>
            </CircleMarker>
          </>
        )}

      </MapContainer>

      {/* ============================== */}
      {/* MAP LAYER CONTROL */}
      {/* ============================== */}

      <div
        style={{
          position: "absolute",
          top: "15px",
          right: "15px",
          zIndex: 1000,
          backgroundColor: "rgba(10, 10, 10, 0.95)",
          color: "white",
          padding: "14px",
          borderRadius: "10px",
          border: "1px solid #333333",
          minWidth: "175px",
          boxShadow: "0 4px 15px rgba(0,0,0,0.4)"
        }}
      >

        <div
          style={{
            fontSize: "14px",
            fontWeight: "700",
            marginBottom: "10px"
          }}
        >
          Map Layers
        </div>

        <LayerCheckbox
          label="Oil Spill"
          checked={showSpill}
          setChecked={setShowSpill}
          color="#ff8c00"
        />

        <LayerCheckbox
          label="Drift / Backtracking"
          checked={showDrift}
          setChecked={setShowDrift}
          color="#2563eb"
        />

        <LayerCheckbox
          label="AIS Tracks"
          checked={showAIS}
          setChecked={setShowAIS}
          color="#8b5cf6"
        />

        <LayerCheckbox
          label="Estimated Source"
          checked={showSource}
          setChecked={setShowSource}
          color="#ff0000"
        />

      </div>

      {/* ============================== */}
      {/* LEGEND */}
      {/* ============================== */}

      <div
        style={{
          position: "absolute",
          bottom: "20px",
          left: "15px",
          zIndex: 1000,
          backgroundColor: "rgba(10, 10, 10, 0.95)",
          color: "white",
          padding: "13px",
          borderRadius: "10px",
          border: "1px solid #333333",
          minWidth: "200px",
          boxShadow: "0 4px 15px rgba(0,0,0,0.4)"
        }}
      >

        <div
          style={{
            fontSize: "14px",
            fontWeight: "700",
            marginBottom: "10px"
          }}
        >
          Legend
        </div>

        <LegendItem
          color="#ff8c00"
          label="Detected Oil Spill"
        />

        <LegendItem
          color="#2563eb"
          label="Drift / Backtracking"
        />

        <LegendItem
          color="#8b5cf6"
          label="AIS Vessel Track"
        />

        <LegendItem
          color="#ff0000"
          label="Estimated Source"
          circle={true}
        />

        <LegendItem
          color="#ff3333"
          label="Source Uncertainty"
          circle={true}
        />

      </div>

    </div>
  );
}

/* ================================= */
/* LAYER CHECKBOX */
/* ================================= */

function LayerCheckbox({
  label,
  checked,
  setChecked,
  color
}) {
  return (
    <label
      style={{
        display: "flex",
        alignItems: "center",
        gap: "8px",
        marginBottom: "8px",
        cursor: "pointer",
        fontSize: "12px"
      }}
    >

      <input
        type="checkbox"
        checked={checked}
        onChange={(event) => {
          setChecked(event.target.checked);
        }}
      />

      <span
        style={{
          width: "10px",
          height: "10px",
          borderRadius: "50%",
          backgroundColor: color,
          display: "inline-block"
        }}
      />

      {label}

    </label>
  );
}

/* ================================= */
/* LEGEND ITEM */
/* ================================= */

function LegendItem({
  color,
  label,
  circle = false
}) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: "9px",
        marginBottom: "8px",
        fontSize: "11px",
        color: "#d1d5db"
      }}
    >

      <span
        style={{
          width: circle ? "12px" : "20px",
          height: circle ? "12px" : "4px",
          borderRadius: circle ? "50%" : "3px",
          backgroundColor: color,
          display: "inline-block"
        }}
      />

      {label}

    </div>
  );
}

export default MapView;


