import json
import pytest
import numpy as np
import rasterio
from affine import Affine
from preprocess_pipeline import run_stage_a

def test_tiling_and_manifest(tmp_path):
    vv_path = tmp_path / "test_vv.tif"
    vh_path = tmp_path / "test_vh.tif"
    out_dir = tmp_path / "output"

    # Create a 512x512 raster (should yield exactly 4 patches of 256x256)
    size = 512
    transform = Affine(0.001, 0, 80.0, 0, -0.001, 13.0)
    data = np.full((size, size), 0.05, dtype=np.float32)

    profile = {
        "driver": "GTiff", "height": size, "width": size, "count": 1,
        "dtype": rasterio.float32, "crs": "EPSG:4326", "transform": transform
    }
    with rasterio.open(vv_path, "w", **profile) as dst:
        dst.write(data, 1)
    with rasterio.open(vh_path, "w", **profile) as dst:
        dst.write(data, 1)

    run_stage_a(str(vv_path), str(vh_path), str(out_dir), patch_size=256)

    manifest_file = out_dir / "manifest.json"
    assert manifest_file.exists()

    with open(manifest_file) as f:
        manifest = json.load(f)

    # 4 non-overlapping patches
    assert len(manifest) == 4

    # Verify per-tile affine transforms are unique (not all pointing to top-left)
    transforms = [tuple(entry["transform"]) for entry in manifest]
    assert len(set(transforms)) == 4

    # Check first patch band count and value normalization bounds [0, 1]
    patch_sample = manifest[0]["patch_path"]
    with rasterio.open(patch_sample) as src:
        assert src.count == 2
        arr = src.read()
        assert arr.min() >= 0.0
        assert arr.max() <= 1.0