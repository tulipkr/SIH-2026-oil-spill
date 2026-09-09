import os
import sys
import json
from pathlib import Path
import numpy as np
import rasterio
from rasterio.windows import Window
from rasterio.mask import mask as rio_mask
import geopandas as gpd
from scipy.ndimage import uniform_filter

def lee_filter(img, size=5):
    """5x5 window Lee speckle filter."""
    mean = uniform_filter(img, size)
    mean_sq = uniform_filter(img**2, size)
    var = np.maximum(0, mean_sq - mean**2)
    overall_var = np.var(img)
    weight = var / (var + overall_var + 1e-8)
    return mean + weight * (img - mean)

def run_stage_a(
    vv_path,
    vh_path,
    output_dir,
    scene_id="CHENNAI_DEMO",
    timestamp_utc="2023-12-04T00:30:00Z",
    land_mask_path=None,
    patch_size=256,
    # Tulip's requested configurable parameters:
    apply_speckle=False,          # Off by default per Tulip's text
    db_clip_min=-30.0,            # Configurable clipping min
    db_clip_max=0.0,              # Configurable clipping max
    apply_normalization=True      # Configurable [0, 1] normalization
):
    out_root = Path(output_dir)
    patches_dir = out_root / "preprocessed_patches"
    patches_dir.mkdir(parents=True, exist_ok=True)
    manifest = []

    # Validate inputs exist
    if not os.path.exists(vv_path) or not os.path.exists(vh_path):
        raise FileNotFoundError("Missing VV or VH band input file.")

    # Load land mask if provided
    land_gdf = None
    if land_mask_path and os.path.exists(land_mask_path):
        land_gdf = gpd.read_file(land_mask_path)

    with rasterio.open(vv_path) as src_vv, rasterio.open(vh_path) as src_vh:
        if src_vv.crs is None or src_vv.transform is None:
            raise ValueError("CRS or Affine Transform missing from source imagery.")

        # Ensure land mask matches raster CRS if present
        if land_gdf is not None and land_gdf.crs != src_vv.crs:
            land_gdf = land_gdf.to_crs(src_vv.crs)

        H, W = src_vv.height, src_vv.width
        profile = src_vv.profile.copy()
        profile.update(
            count=2,
            dtype=rasterio.float32,
            width=patch_size,
            height=patch_size,
            nodata=None
        )

        tile_idx = 0
        eps = 1e-6

        # Step through non-overlapping windows
        for row in range(0, H - patch_size + 1, patch_size):
            for col in range(0, W - patch_size + 1, patch_size):
                win = Window(col, row, patch_size, patch_size)
                tile_transform = rasterio.windows.transform(win, src_vv.transform)

                vv = src_vv.read(1, window=win).astype(np.float32)
                vh = src_vh.read(1, window=win).astype(np.float32)

                # Skip NaN/empty patches
                if np.isnan(vv).all() or np.isnan(vh).all():
                    continue

                # 1. Speckle Filtering (configurable, off by default)
                if apply_speckle:
                    vv = lee_filter(vv, size=5)
                    vh = lee_filter(vh, size=5)

                # 2. Convert to decibels (dB): 10 * log10(sigma0 + eps)
                vv_db = 10.0 * np.log10(np.maximum(vv, eps))
                vh_db = 10.0 * np.log10(np.maximum(vh, eps))

                # 3. Configurable clipping
                if db_clip_min is not None and db_clip_max is not None:
                    vv_clipped = np.clip(vv_db, db_clip_min, db_clip_max)
                    vh_clipped = np.clip(vh_db, db_clip_min, db_clip_max)
                else:
                    vv_clipped = vv_db
                    vh_clipped = vh_db

                # 4. Configurable [0, 1] min-max normalization
                if apply_normalization and db_clip_min is not None and db_clip_max is not None:
                    denom = db_clip_max - db_clip_min
                    vv_final = (vv_clipped - db_clip_min) / denom
                    vh_final = (vh_clipped - db_clip_min) / denom
                else:
                    vv_final = vv_clipped
                    vh_final = vh_clipped

                # 5. Write 2-band Float32 GeoTIFF patch
                profile.update(transform=tile_transform)
                patch_name = f"{scene_id}_{tile_idx:04d}.tif"
                patch_file = patches_dir / patch_name

                with rasterio.open(patch_file, "w", **profile) as dst:
                    dst.write(vv_final, 1)
                    dst.write(vh_final, 2)

                # 6. Append entry matching Tulip's schema (§9)
                manifest.append({
                    "scene_id": scene_id,
                    "patch_path": str(patch_file).replace("\\", "/"),
                    "acquisition_timestamp_utc": timestamp_utc,
                    "crs": src_vv.crs.to_string(),
                    "transform": list(tile_transform)[:6],
                    "bands": ["VV", "VH"]
                })
                tile_idx += 1

    # Write manifest.json
    manifest_path = out_root / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"Stage A complete! Generated {tile_idx} patches in {patches_dir}")
    print(f"Manifest written to {manifest_path}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python preprocess_pipeline.py <vv.tif> <vh.tif> <output_dir>")
        sys.exit(1)
    run_stage_a(sys.argv[1], sys.argv[2], sys.argv[3])