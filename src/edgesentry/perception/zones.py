"""Polygon zone awareness (v1 logic, self-contained — no NPU needed).

Loads named polygons from config/zones.json and tags each detection with the
zone its foot-point falls inside. Implemented with a standard ray-casting
point-in-polygon test so it has zero heavy dependencies and is unit-testable.
"""
from __future__ import annotations

import json
from pathlib import Path

from edgesentry.config import Config
from edgesentry.perception import Detection


def point_in_polygon(point: tuple[int, int], polygon: list[list[int]]) -> bool:
    """Ray-casting point-in-polygon test."""
    x, y = point
    inside = False
    n = len(polygon)
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        intersects = ((yi > y) != (yj > y)) and (
            x < (xj - xi) * (y - yi) / (yj - yi + 1e-9) + xi
        )
        if intersects:
            inside = not inside
        j = i
    return inside


class ZoneMap:
    def __init__(self, cfg: Config) -> None:
        data = json.loads(Path(cfg.perception.zones_file).read_text())
        self.zones = [(z["name"], z["polygon"]) for z in data["zones"]]

    def zone_for(self, point: tuple[int, int]) -> str | None:
        for name, polygon in self.zones:
            if point_in_polygon(point, polygon):
                return name
        return None

    def annotate(self, detections: list[Detection]) -> list[Detection]:
        for det in detections:
            det.zone = self.zone_for(det.foot_point)
        return detections
