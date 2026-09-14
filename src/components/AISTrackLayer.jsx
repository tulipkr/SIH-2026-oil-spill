import React from "react";
import { GeoJSON } from "react-leaflet";

function AISTrackLayer({ runResult }) {
  const aisTracks =
    runResult?.results?.normalized_ais_tracks;

  // If AIS data is not available
  if (!aisTracks) {
    return null;
  }

  // Check that the data is valid GeoJSON
  if (
    aisTracks.type !== "FeatureCollection" ||
    !Array.isArray(aisTracks.features)
  ) {
    return null;
  }

  // Render maximum 25 tracks
  const tracksToRender = aisTracks.features.slice(0, 25);

  const filteredTracks = {
    type: "FeatureCollection",
    features: tracksToRender
  };

  return (
    <GeoJSON
      data={filteredTracks}
      style={{
        color: "purple",
        weight: 5,
        opacity: 0.9
      }}
      onEachFeature={(feature, layer) => {
        const properties =
          feature?.properties || {};

        const popupContent = `
          <div>
            <h3>AIS Vessel Track</h3>

            <p>
              <strong>Vessel:</strong>
              ${properties.vessel_name || "Not available"}
            </p>

            <p>
              <strong>Candidate Rank:</strong>
              ${properties.candidate_rank || "Not available"}
            </p>

            <p>
              <strong>MMSI:</strong>
              ${properties.mmsi || "Not available"}
            </p>
          </div>
        `;

        layer.bindPopup(popupContent);
      }}
    />
  );
}

export default AISTrackLayer;