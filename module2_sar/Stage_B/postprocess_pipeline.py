import json
import sys
from pathlib import Path
import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import shapes
from shapely.geometry import shape

def run_stage_b(mask_path, inference_json_path, output_dir, min_area_km2=0.01):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    with open(inference_json_path, "r") as f:
        meta = json.load(f)

    scene_id = meta.get("scene_id", "unknown")
    timestamp = meta.get("acquisition_timestamp_utc")

    # Handle missing georeferencing
    if meta.get("geolocation_incomplete") or not meta.get("crs") or not meta.get("transform"):
        summary = {
            "scene_id": scene_id, "num_regions": 0, "total_area_km2": 0.0,
            "primary_region_centroid": None, "acquisition_timestamp_utc": timestamp,
            "no_oil_detected": meta.get("no_oil_detected", False),
            "geometry_unavailable": True, "geojson_path": None
        }
        with open(out / "spill_summary.json", "w") as f:
            json.dump(summary, f, indent=2)
        print("Missing georeferencing. Aborted cleanly.")
        return

    with rasterio.open(mask_path) as src:
        mask = src.read(1)
        src_crs = src.crs
        src_transform = src.transform

    # Handle empty / no oil masks
    if np.all(mask == 0) or meta.get("no_oil_detected", False):
        geojson_file = out / "spill_geometry.geojson"
        with open(geojson_file, "w") as f:
            json.dump({"type": "FeatureCollection", "features": []}, f, indent=2)

        summary = {
            "scene_id": scene_id, "num_regions": 0, "total_area_km2": 0.0,
            "primary_region_centroid": None, "acquisition_timestamp_utc": timestamp,
            "no_oil_detected": True, "geometry_unavailable": False,
            "geojson_path": str(geojson_file)
        }
        with open(out / "spill_summary.json", "w") as f:
            json.dump(summary, f, indent=2)
        print("No oil detected.")
        return

    # Vectorize mask using raster transform
    extracted = [shape(geom) for geom, val in shapes(mask, mask=(mask > 0), transform=src_transform)]
    if not extracted:
        return

    gdf = gpd.GeoDataFrame({"geometry": extracted}, crs=src_crs)

    # Equal-area reprojection (EPSG:6933) to get km²
    gdf_ea = gdf.to_crs(epsg=6933)
    gdf["area_km2"] = gdf_ea.geometry.area / 1e6

    # Drop noise specks
    gdf = gdf[gdf["area_km2"] >= min_area_km2].copy().reset_index(drop=True)
    if gdf.empty:
        print("Only noise detected (below threshold).")
        return

    # Calculate centroids on the equal-area projection, then reproject points to WGS84
    centroids_wgs84 = gdf_ea.geometry.centroid.to_crs(epsg=4326)
    
    gdf_wgs84 = gdf.to_crs(epsg=4326)
    gdf_wgs84["centroid_lat"] = centroids_wgs84.y
    gdf_wgs84["centroid_lon"] = centroids_wgs84.x
    gdf_wgs84["region_id"] = gdf_wgs84.index + 1
    gdf_wgs84["scene_id"] = scene_id
    gdf_wgs84["acquisition_timestamp_utc"] = timestamp
    gdf_wgs84["mean_confidence"] = meta.get("mean_confidence", None)
    gdf_wgs84["source_mask_path"] = str(mask_path)

    cols = [
        "region_id", "scene_id", "area_km2", "centroid_lat",
        "centroid_lon", "acquisition_timestamp_utc",
        "mean_confidence", "source_mask_path", "geometry"
    ]
    gdf_final = gdf_wgs84[cols]

    geojson_path = out / "spill_geometry.geojson"
    gdf_final.to_file(geojson_path, driver="GeoJSON")

    # Pick the largest spill as the primary one
    primary = gdf_final.loc[gdf_final["area_km2"].idxmax()]
    summary = {
        "scene_id": scene_id,
        "num_regions": int(len(gdf_final)),
        "total_area_km2": float(gdf_final["area_km2"].sum()),
        "primary_region_centroid": [float(primary["centroid_lat"]), float(primary["centroid_lon"])],
        "acquisition_timestamp_utc": timestamp,
        "no_oil_detected": False,
        "geometry_unavailable": False,
        "geojson_path": str(geojson_path)
    }

    with open(out / "spill_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(f"Done! {len(gdf_final)} region(s) exported to {output_dir}")

if __name__ == "__main__":
    run_stage_b(sys.argv[1], sys.argv[2], sys.argv[3])