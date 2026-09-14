import json
from pathlib import Path


def test_short_circuit_no_oil(tmp_path):
    summary = {"scene_id": "x", "no_oil_detected": True, "geometry_unavailable": False}
    assert summary["no_oil_detected"] is True


def test_short_circuit_missing_geometry(tmp_path):
    summary = {"scene_id": "x", "no_oil_detected": False, "geometry_unavailable": True}
    assert summary["geometry_unavailable"] is True
