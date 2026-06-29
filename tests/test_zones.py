"""Tests for the zone polygon logic (no hardware needed)."""
from edgesentry.perception.zones import point_in_polygon, ZoneMap
from edgesentry.perception import Detection


class TestPointInPolygon:
    SQUARE = [[0, 0], [100, 0], [100, 100], [0, 100]]

    def test_inside(self):
        assert point_in_polygon((50, 50), self.SQUARE) is True

    def test_outside(self):
        assert point_in_polygon((150, 50), self.SQUARE) is False

    def test_on_edge_bottom(self):
        # Ray-casting is deterministic on edges; we just care it doesn't crash.
        result = point_in_polygon((50, 100), self.SQUARE)
        assert isinstance(result, bool)

    def test_triangle(self):
        tri = [[0, 0], [200, 0], [100, 200]]
        assert point_in_polygon((100, 50), tri) is True
        assert point_in_polygon((0, 200), tri) is False


class TestZoneMap:
    def test_annotate_assigns_zone(self, cfg, tmp_path):
        import json
        zones_file = tmp_path / "zones.json"
        zones_file.write_text(json.dumps({
            "zones": [{"name": "TestZone", "polygon": [[0, 0], [500, 0], [500, 500], [0, 500]]}]
        }))
        object.__setattr__(cfg.perception, "zones_file", str(zones_file))
        zm = ZoneMap(cfg)
        det = Detection(bbox=(100, 100, 200, 400), confidence=0.8)
        zm.annotate([det])
        assert det.zone == "TestZone"

    def test_annotate_none_when_outside(self, cfg, tmp_path):
        import json
        zones_file = tmp_path / "zones.json"
        zones_file.write_text(json.dumps({
            "zones": [{"name": "Small", "polygon": [[0, 0], [10, 0], [10, 10], [0, 10]]}]
        }))
        object.__setattr__(cfg.perception, "zones_file", str(zones_file))
        zm = ZoneMap(cfg)
        det = Detection(bbox=(500, 500, 600, 600), confidence=0.8)
        zm.annotate([det])
        assert det.zone is None
