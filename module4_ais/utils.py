from datetime import datetime

def validate_source_estimate(source_estimate):
    """
    Validates Shazmeen's source_estimate.json against the agreed schema.
    Returns a dict: {"valid": bool, "short_circuit": bool, "reason": str or None}
    Raises ValueError only for structurally malformed input (missing/bad fields).
    """
    required_fields = [
        "region_id",
        "backtracking_valid",
        "no_oil_detected",
        "probable_source_region",
        "probable_source_time_window"
    ]
    for field in required_fields:
        if field not in source_estimate:
            raise ValueError(f"Missing required field: {field}")
        
    region = source_estimate["probable_source_region"]
    latitude = region.get("latitude")
    longitude = region.get("longitude")

    if latitude is None or longitude is None:
        raise ValueError("probable_source_region missing latitude/longitude")
    if not -90 <= latitude <= 90:
        raise ValueError("Invalid latitude")
    if not -180 <= longitude <= 180:
        raise ValueError("Invalid longitude")

    time_window = source_estimate["probable_source_time_window"]
    start_str = time_window.get("start")
    end_str = time_window.get("end")

    if not start_str or not end_str:
        raise ValueError("probable_source_time_window missing start/end")

    try:
        start = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
        end = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError("probable_source_time_window has invalid ISO8601 timestamps")

    if start >= end:
        raise ValueError("probable_source_time_window: start must be before end")

    if source_estimate["backtracking_valid"] is False:
        return {"valid": True, "short_circuit": True, "reason": "backtracking_valid is false"}

    if source_estimate["no_oil_detected"] is True:
        return {"valid": True, "short_circuit": True, "reason": "no_oil_detected is true"}

    return {"valid": True, "short_circuit": False, "reason": None}