import logging
import pandas as pd

from spatial_filter import filter_by_bbox
from temporal_filter import filter_by_time

logger = logging.getLogger(__name__)


def filter_ais(df, search_window):
    """
    Apply spatial AND temporal filtering.

    A record must satisfy both conditions to remain
    in the final filtered AIS dataset.
    """

    spatial_df = filter_by_bbox(
        df,
        search_window["bbox"]
    )

    filtered_df = filter_by_time(
        spatial_df,
        search_window["time_window"]
    )

    logger.info(
        f"Combined AIS filter: {len(df)} → {len(filtered_df)} records"
    )

    return filtered_df


if __name__ == "__main__":
    from search_window import calculate_search_window, load_config

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

    filtered = filter_ais(
        ais_df,
        search_window
    )

    print("Combined spatial + temporal filtering completed.")
    print("Original records:", len(ais_df))
    print("Final filtered records:", len(filtered))