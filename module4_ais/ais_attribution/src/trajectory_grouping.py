import logging
import pandas as pd

from search_window import calculate_search_window, load_config
from spatial_filter import filter_by_bbox
from temporal_filter import filter_by_time


def group_by_mmsi(df):
    """
    Group AIS records by MMSI.
    Each MMSI represents one vessel.
    """

    grouped = {
        mmsi: vessel_df.copy()
        for mmsi, vessel_df in df.groupby("MMSI")
    }

    logging.info(
        f"MMSI grouping: {len(df)} records → "
        f"{len(grouped)} unique vessels"
    )

    return grouped


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    source_estimate = {
        "region_id": 1,
        "backtracking_valid": True,
        "no_oil_detected": False,
        "probable_source_region": {
            "latitude": 13.0827,
            "longitude": 80.2707
        },
        "probable_source_time_window": {
            "start": "2025-01-01T00:00:00Z",
            "end": "2025-01-01T04:00:00Z"
        }
    }

    config = load_config("config/config.yaml")

    search_window = calculate_search_window(
        source_estimate,
        config
    )

    ais_df = pd.read_csv(
        "data/processed/normalized_ais.csv"
    )

    spatially_filtered = filter_by_bbox(
        ais_df,
        search_window["bbox"]
    )

    filtered = filter_by_time(
        spatially_filtered,
        search_window["time_window"]
    )

    grouped = group_by_mmsi(filtered)

    print("MMSI grouping completed.")
    print("Filtered records:", len(filtered))
    print("Unique vessels:", len(grouped))

    print("\nRecords per vessel:")

    for mmsi, vessel_df in grouped.items():
        print(
            f"MMSI {mmsi}: {len(vessel_df)} records"
        )