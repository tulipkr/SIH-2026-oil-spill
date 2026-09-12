import numpy as np


def _coord_name(da, candidates):
    for name in candidates:
        if name in da.coords:
            return name
    raise KeyError(f"None of coordinate names {candidates} found")


def _normalise_lon(lon):
    return ((float(lon) + 180.0) % 360.0) - 180.0


def _nearest_valid(da, lat, lon, max_radius_cells=2):
    lat_name = _coord_name(da, ["latitude", "lat"])
    lon_name = _coord_name(da, ["longitude", "lon"])
    lats = np.asarray(da[lat_name].values, dtype=float)
    lons = np.asarray(da[lon_name].values, dtype=float)
    target_lon = _normalise_lon(lon)
    i0 = int(np.argmin(np.abs(lats - float(lat))))
    j0 = int(np.argmin(np.abs(np.asarray([_normalise_lon(x) for x in lons]) - target_lon)))
    best = None
    for radius in range(max_radius_cells + 1):
        for i in range(max(0, i0-radius), min(len(lats), i0+radius+1)):
            for j in range(max(0, j0-radius), min(len(lons), j0+radius+1)):
                value = float(da.isel({lat_name: i, lon_name: j}).values)
                if np.isfinite(value):
                    d2 = (lats[i]-float(lat))**2 + (_normalise_lon(lons[j])-target_lon)**2
                    if best is None or d2 < best[0]:
                        best = (d2, value)
        if best is not None:
            return best[1]
    raise ValueError("No finite environmental value within bounded nearest-neighbor radius")


def _interpolate(da, lat, lon, max_radius_cells=2):
    if da.ndim != 2:
        raise ValueError("Expected a 2-D environmental field after time selection")
    lat_name = _coord_name(da, ["latitude", "lat"])
    lon_name = _coord_name(da, ["longitude", "lon"])
    da = da.sortby(lat_name).sortby(lon_name)
    lat_f = float(lat); lon_f = _normalise_lon(lon)
    lats = np.asarray(da[lat_name].values, dtype=float)
    lons = np.asarray([_normalise_lon(x) for x in da[lon_name].values], dtype=float)
    if lat_f < lats.min() or lat_f > lats.max() or lon_f < lons.min() or lon_f > lons.max():
        return _nearest_valid(da, lat_f, lon_f, max_radius_cells), True
    work = da.assign_coords({lon_name: lons})
    try:
        value = float(work.interp({lat_name: lat_f, lon_name: lon_f}, method="linear").values)
        if np.isfinite(value):
            return value, False
    except Exception:
        pass
    return _nearest_valid(da, lat_f, lon_f, max_radius_cells), True


def bilinear_or_nearest_valid(data, *args, max_radius_cells=2):
    """Support the original API: (dataset, variable, lat, lon) -> (value, used_nearest).
    Also supports a 2-D DataArray: (dataarray, lat, lon) -> (value, used_nearest).
    """
    if hasattr(data, "data_vars"):
        if len(args) < 3:
            raise TypeError("Dataset API requires variable, lat, lon")
        variable, lat, lon = args[:3]
        da = data[variable]
    else:
        if len(args) < 2:
            raise TypeError("DataArray API requires lat, lon")
        lat, lon = args[:2]
        da = data
    return _interpolate(da, lat, lon, max_radius_cells)


def select_time_slice(da, when, max_tolerance_hours=None):
    if "time" not in da.coords:
        raise KeyError("Environmental field has no time coordinate")
    target = np.datetime64(when.replace(tzinfo=None) if getattr(when, "tzinfo", None) else when)
    times = np.asarray(da["time"].values)
    if times.size == 0:
        raise ValueError("Environmental dataset has no time values")
    idx = int(np.argmin(np.abs(times - target)))
    delta_hours = abs(float((times[idx] - target) / np.timedelta64(1, "h")))
    if max_tolerance_hours is not None and delta_hours > float(max_tolerance_hours):
        raise ValueError(f"Nearest environmental time is {delta_hours:.2f} h away; maximum allowed is {max_tolerance_hours} h")
    return da.isel(time=idx)
