import os
import sys
import json
from pathlib import Path
import numpy as np
import rasterio
from rasterio.windows import Window
from scipy.ndimage import uniform_filter

def lee_filter(img, size=5):
    """5x5 window Lee speckle filter."""
    mean = uniform_filter(img, size)
    mean_sq = uniform_filter(img**2, size)
    var = np.maximum(0, mean_sq - mean**2)
    overall_var = np.var(img)
    weight = var / (var + overall_var + 1e-8)
    return mean + weight * (img - mean)

def is_already_db(sample_array):
    """
    Detects if the input raster band is already in decibels (dB).
    Linear Sigma0 is strictly positive (0.0 to ~1.0).
    dB values are predominantly negative (e.g., -5.0 to -35.0 dB).
    """
    valid_pixels = sample_array[np.isfinite(sample_array)]
    if len(valid_pixels) == 0:
        return False
    # If the 5th percentile or minimum is negative, it's already in dB
    return bool(np.percentile(valid_pixels, 5) < 0.0)

def run_stage_a(
    vv_path,
    vh_path,
    output_dir,
    scene_id="S1_SCENE",
    timestamp_utc="2026-01-14T00:00:00Z",
    patch_size=256,
    # Configurable flags per Tulip's latest update:
    apply_speckle=False,
    apply_db_clipping=False,       # Kept OFF by default per Tulip's training setup
    db_clip_min=-30.0,
    db_clip_max=0.0,
    apply_normalization=False     # Kept OFF by default (raw dB preserved)
):
    out_root = Path(output_dir)
    patches_dir = out_root / "preprocessed_patches"
    patches_dir.mkdir(parents=True, exist_ok=True)
    manifest = []

    if not os.path.exists(vv_path) or not os.path.exists(vh_path):
        raise FileNotFoundError(f"Missing input files: {vv_path} or {vh_path}")

    with rasterio.open(vv_path) as src_vv, rasterio.open(vh_path) as src_vh:
        if src_vv.crs is None or src_vv.transform is None:
            raise ValueError("CRS or Affine Transform missing from source imagery.")

        # Read small sample to detect if input is linear or already dB
        sample_win = Window(0, 0, min(512, src_vv.width), min(512, src_vv.height))
        sample_vv = src_vv.read(1, window=sample_win).astype(np.float32)
        input_is_db = is_already_db(sample_vv)
        
        if input_is_db:
            print(">> Detected input imagery is ALREADY in dB. Skipping 10*log10 conversion.")
        else:
            print(">> Detected LINEAR Sigma0 input. Applying 10*log10 conversion to dB.")

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

        # Step through non-overlapping 256x256 windows
        for row in range(0, H - patch_size + 1, patch_size):
            for col in range(0, W - patch_size + 1, patch_size):
                win = Window(col, row, patch_size, patch_size)
                tile_transform = rasterio.windows.transform(win, src_vv.transform)

                vv = src_vv.read(1, window=win).astype(np.float32)
                vh = src_vh.read(1, window=win).astype(np.float32)

                # Skip completely empty/NaN tiles
                if np.isnan(vv).all() or np.isnan(vh).all():
                    continue

                # 1. Speckle Filtering (configurable)
                if apply_speckle:
                    vv = lee_filter(vv, size=5)
                    vh = lee_filter(vh, size=5)

                # 2. Conversion to dB (avoiding double log if already dB)
                if not input_is_db:
                    vv = 10.0 * np.log10(np.maximum(vv, eps))
                    vh = 10.0 * np.log10(np.maximum(vh, eps))

                # 3. dB Clipping (configurable, default False)
                if apply_db_clipping and db_clip_min is not None and db_clip_max is not None:
                    vv = np.clip(vv, db_clip_min, db_clip_max)
                    vh = np.clip(vh, db_clip_min, db_clip_max)

                # 4. [0, 1] Normalization (configurable, default False)
                if apply_normalization and db_clip_min is not None and db_clip_max is not None:
                    denom = db_clip_max - db_clip_min
                    vv = (vv - db_clip_min) / denom
                    vh = (vh - db_clip_min) / denom

                # 5. Write 2-band Float32 GeoTIFF patch (VV=band 1, VH=band 2)
                profile.update(transform=tile_transform)
                patch_name = f"{scene_id}_{tile_idx:04d}.tif"
                patch_file = patches_dir / patch_name

                with rasterio.open(patch_file, "w", **profile) as dst:
                    dst.write(vv, 1)
                    dst.write(vh, 2)

                # 6. Append to manifest matching schema
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
