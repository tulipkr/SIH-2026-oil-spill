import React from "react";
import { GeoJSON } from "react-leaflet";

function DriftLayer({ runResult }) {
  const sourceEstimate =
    runResult?.results?.source_estimate;

  const driftGeoJSON =
    sourceEstimate?.drift_trajectory_geojson;

  // If drift data is not available, don't crash the map
  if (!driftGeoJSON) {
    return null;
  }

  // Check that the data is valid GeoJSON
  if (
    driftGeoJSON.type !== "FeatureCollection" ||
    !Array.isArray(driftGeoJSON.features)
  ) {
    return null;
  }

  return (
    <GeoJSON
      data={driftGeoJSON}
      style={{
        color: "blue",
        weight: 4,
        opacity: 0.9
      }}
      onEachFeature={(feature, layer) => {
        const properties =
          feature?.properties || {};

        const popupContent = `
          <div>
            <h3>Drift Trajectory</h3>

            <p>
              <strong>Status:</strong>
              ${properties.status || "Not available"}
            </p>

            <p>
              <strong>Type:</strong>
              ${properties.type || "Not available"}
            </p>
          </div>
        `;

        layer.bindPopup(popupContent);
      }}
    />
  );
}

export default DriftLayer;