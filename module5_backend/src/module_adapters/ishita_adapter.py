from typing import Dict, Any

def run_sar_preprocessing(scene_id: str) -> Dict[str, Any]:
    """Simulates Ishita's preprocessing stage."""
    return {
        "status": "success",
        "scene_id": scene_id,
        "preprocessed_image_path": f"outputs/runs/sample/{scene_id}_preprocessed.tif",
        "acquisition_timestamp_utc": "2026-09-09T10:00:00Z",
        "bounds": [80.1, 13.0, 80.3, 13.2]
    }

def run_geometry_extraction(scene_id: str) -> Dict[str, Any]:
    """Simulates Ishita's geometry extraction stage."""
    return {
        "status": "success",
        "no_oil_detected": False,
        "spill_geometry_geojson": {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[80.15, 13.05], [80.20, 13.05], [80.20, 13.10], [80.15, 13.10], [80.15, 13.05]]]
                    },
                    "properties": {"spill_id": "spill_001", "area_sq_km": 12.4}
                }
            ]
        },
        "spill_summary": {
            "scene_id": scene_id,
            "total_spills_detected": 1,
            "total_area_sq_km": 12.4
        }
    }