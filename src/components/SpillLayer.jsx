import React from "react";
import { GeoJSON } from "react-leaflet";

function SpillLayer({ runResult }) {
  const geojson =
    runResult?.results?.spill_geometry_geojson;

  if (!geojson) {
    return null;
  }

  if (
    geojson.type !== "FeatureCollection" ||
    !Array.isArray(geojson.features)
  ) {
    console.warn("Invalid spill GeoJSON. Layer skipped.");
    return null;
  }

  return (
    <GeoJSON
      data={geojson}
      style={{
        weight: 2,
        fillOpacity: 0.45
      }}
      onEachFeature={(feature, layer) => {
        const properties = feature?.properties || {};

        let popup = "<strong>Oil Spill Region</strong>";

        Object.entries(properties).forEach(
          ([key, value]) => {
            popup += `<br><strong>${key}:</strong> ${value}`;
          }
        );

        layer.bindPopup(popup);
      }}
    />
  );
}

export default SpillLayer;