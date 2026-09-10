from typing import Dict, Any

def run_ais_ranking(scene_id: str) -> Dict[str, Any]:
    """Simulates Sara's AIS candidate vessel ranking stage."""
    return {
        "status": "success",
        "candidate_ranking": {
            "region_id": "BAY_OF_BENGAL_N",
            "ais_source": "Spire_Maritime_API",
            "disclaimer": "DISCLAIMER: Probabilistic vessel attribution only. Not legal proof of liability.",
            "ranked_candidates": [
                {
                    "mmsi": 419001234,
                    "vessel_name": "TANKER ALPHA",
                    "score": 0.88,
                    "rank": 1,
                    "distance_at_time_km": 1.2
                },
                {
                    "mmsi": 419005678,
                    "vessel_name": "CARGO BETA",
                    "score": 0.35,
                    "rank": 2,
                    "distance_at_time_km": 8.7
                }
            ]
        },
        "normalized_ais_tracks": {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[80.10, 13.00], [80.12, 13.02], [80.15, 13.05]]
                    },
                    "properties": {"mmsi": 419001234, "vessel_name": "TANKER ALPHA"}
                }
            ]
        }
    }