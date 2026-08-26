"""
Great-circle distance via the haversine formula, stdlib math only. This is
deliberately not PostGIS/pgvector — at this project's report volume an
O(n) candidate scan with a Python-side distance check is simple, correct,
and dependency-free. Revisit with a spatial index if report volume grows
large enough for this to become a bottleneck.
"""
import math

EARTH_RADIUS_METERS = 6_371_000.0


def haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS_METERS * c
