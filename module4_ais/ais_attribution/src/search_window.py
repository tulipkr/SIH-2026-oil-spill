from datetime import datetime, timedelta
import math
import yaml


def load_config(config_path="config/config.yaml"):
    with open(config_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def calculate_search_window(source_estimate, config):
    region = source_estimate["probable_source_region"]
    latitude = region["latitude"]
    longitude = region["longitude"]

    margin_km = config["search_margin_km"]
    time_margin_hours = config["search_time_margin_hours"]

    lat_margin = margin_km / 111.0
    lon_margin = margin_km / (111.0 * math.cos(math.radians(latitude)))

    min_latitude = latitude - lat_margin
    max_latitude = latitude + lat_margin
    min_longitude = longitude - lon_margin
    max_longitude = longitude + lon_margin

    time_window = source_estimate["probable_source_time_window"]
    window_start = datetime.fromisoformat(time_window["start"].replace("Z", "+00:00"))
    window_end = datetime.fromisoformat(time_window["end"].replace("Z", "+00:00"))

    start_time = window_start - timedelta(hours=time_margin_hours)
    end_time = window_end + timedelta(hours=time_margin_hours)

    return {
        "bbox": {
            "min_latitude": min_latitude,
            "max_latitude": max_latitude,
            "min_longitude": min_longitude,
            "max_longitude": max_longitude
        },
        "time_window": {
            "start": start_time.isoformat(),
            "end": end_time.isoformat()
        }
    }