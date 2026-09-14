from datetime import datetime, timezone
from src.backward_advection import step_backward, backward_trajectory


def test_advection_step_zero_velocity():
    assert step_backward(13.0, 80.0, 0.0, 0.0, 1) == (13.0, 80.0)


def test_advection_uses_geodesic_step():
    lat, lon = step_backward(13.0, 80.0, 1.0, 0.0, 1)
    assert lat != 13.0 or lon != 80.0


def test_trajectory_records_steps():
    t = datetime(2026, 1, 1, tzinfo=timezone.utc)
    out = backward_trajectory(13, 80, t, 2, 1, lambda *_: (1, 0))
    assert len(out) == 3
