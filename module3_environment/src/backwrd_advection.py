from datetime import timedelta
import logging
import math
from pyproj import Geod

GEOD = Geod(ellps="WGS84")
LOG = logging.getLogger("module3")


def step_backward(lat, lon, u_ms, v_ms, dt_hours):
    speed = math.hypot(float(u_ms), float(v_ms))
    if speed == 0.0:
        return float(lat), float(lon)
    distance_m = speed * float(dt_hours) * 3600.0
    azimuth = math.degrees(math.atan2(float(u_ms), float(v_ms)))
    lon2, lat2, _ = GEOD.fwd(float(lon), float(lat), azimuth + 180.0, distance_m)
    return float(lat2), float(lon2)


def backward_trajectory(start_lat, start_lon, acquisition_time, backward_window_hours, time_step_hours, velocity_at):
    points = [{"timestamp": acquisition_time.isoformat().replace("+00:00", "Z"), "lat": float(start_lat), "lon": float(start_lon)}]
    lat, lon = float(start_lat), float(start_lon)
    steps = int(backward_window_hours / time_step_hours)
    for n in range(1, steps + 1):
        # using position(t-dt) = position(t) - velocity(t)*dt.
        velocity_time = acquisition_time - timedelta(hours=(n - 1) * time_step_hours)
        u, v = velocity_at(velocity_time, lat, lon)
        lat, lon = step_backward(lat, lon, u, v, time_step_hours)
        point_time = acquisition_time - timedelta(hours=n * time_step_hours)
        LOG.info("advection step: from=%s to=%s lat=%.6f lon=%.6f u=%.4f m/s v=%.4f m/s", velocity_time, point_time, lat, lon, u, v)
        points.append({"timestamp": point_time.isoformat().replace("+00:00", "Z"), "lat": lat, "lon": lon})
    return points
