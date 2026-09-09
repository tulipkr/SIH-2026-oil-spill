import json
import pytest
import numpy as np
import rasterio
from affine import Affine
from postprocess_pipeline import run_stage_b

def test_area_computation_and_vectorize(tmp_path):
    mask_path = tmp_path / "test_mask.tif"
    json_path = tmp_path / "test_inference.json"
    out_dir = tmp_path / "output"

    # 10m pixel resolution: 100px x 100px = 1,000,000 m² = 1.0 km²
    transform = Affine(10.0, 0, 0, 0, -10.0, 0)
    mask = np.zeros((200, 200), dtype=np.uint8)
    mask[50:150, 50:150] = 1

    with rasterio.open(
        mask_path, "w", driver="GTiff", height=200, width=200, count=1,
        dtype=rasterio.uint8, crs="EPSG:3857", transform=transform
    ) as dst:
        dst.write(mask, 1)

    meta = {
        "scene_id": "TEST_SCENE",
        "crs": "EPSG:3857",
        "transform": list(transform)[:6],
        "acquisition_timestamp_utc": "2023-12-04T00:30:00Z",
        "mask_path": str(mask_path),
        "no_oil_detected": False,
        "geolocation_incomplete": False
    }
    with open(json_path, "w") as f:
        json.dump(meta, f)

    run_stage_b(str(mask_path), str(json_path), str(out_dir), min_area_km2=0.01)

    with open(out_dir / "spill_summary.json") as f:
        summary = json.load(f)

    assert summary["num_regions"] == 1
    assert pytest.approx(summary["total_area_km2"], rel=1e-2) == 1.0

def test_min_area_filter(tmp_path):
    mask_path = tmp_path / "noise_mask.tif"
    json_path = tmp_path / "test_inference.json"
    out_dir = tmp_path / "output"

    transform = Affine(10.0, 0, 0, 0, -10.0, 0)
    mask = np.zeros((100, 100), dtype=np.uint8)
    mask[10, 10] = 1  # Single pixel = 0.0001 km²

    with rasterio.open(
        mask_path, "w", driver="GTiff", height=100, width=100, count=1,
        dtype=rasterio.uint8, crs="EPSG:3857", transform=transform
    ) as dst:
        dst.write(mask, 1)

    meta = {
        "scene_id": "NOISE_SCENE",
        "crs": "EPSG:3857",
        "transform": list(transform)[:6],
        "acquisition_timestamp_utc": "2023-12-04T00:30:00Z",
        "mask_path": str(mask_path),
        "no_oil_detected": False,
        "geolocation_incomplete": False
    }
    with open(json_path, "w") as f:
        json.dump(meta, f)

    run_stage_b(str(mask_path), str(json_path), str(out_dir), min_area_km2=0.01)
    
    assert not (out_dir / "spill_geometry.geojson").exists()

def test_missing_georeferencing(tmp_path):
    mask_path = tmp_path / "empty.tif"
    json_path = tmp_path / "meta_no_crs.json"
    out_dir = tmp_path / "output"

    meta = {
        "scene_id": "NO_GEO",
        "crs": None,
        "transform": None,
        "acquisition_timestamp_utc": "2023-12-04T00:30:00Z",
        "geolocation_incomplete": True
    }
    with open(json_path, "w") as f:
        json.dump(meta, f)

    run_stage_b(str(mask_path), str(json_path), str(out_dir))

    with open(out_dir / "spill_summary.json") as f:
        summary = json.load(f)

    assert summary["geometry_unavailable"] is True