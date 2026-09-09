from __future__ import annotations
from pathlib import Path


def fetch_glorys(*, output_path, bbox, start_utc, end_utc, username=None, password=None):
    """Fetch the bounded daily GLORYS12V1 uo/vo window for Module 3."""
    import copernicusmarine

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    copernicusmarine.subset(
        dataset_id="cmems_mod_glo_phy_my_0.083deg_P1D-m",
        variables=["uo", "vo"],
        minimum_longitude=bbox[0],
        maximum_longitude=bbox[2],
        minimum_latitude=bbox[1],
        maximum_latitude=bbox[3],
        start_datetime=start_utc.isoformat(),
        end_datetime=end_utc.isoformat(),
        output_filename=str(output_path),
    )
    return output_path
