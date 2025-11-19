import random
from typing import Tuple


def get_mock_gps(center: Tuple[float, float] = (48.8584, 2.2945), radius_m: float = 5000) -> Tuple[float, float]:
    """Return a mock GPS coordinate near a given center (lat, lon).

    Default center is the Eiffel Tower. radius_m controls spread in meters.
    This is a simple uniform perturbation in metres converted to degrees (approx).
    """
    lat, lon = center
    # 1 deg latitude ~= 111km. 1 deg longitude ~= cos(lat)*111km
    meters_per_deg_lat = 111_000
    meters_per_deg_lon = abs(111_000 * (0.0 + __import__('math').cos(__import__('math').radians(lat))))

    # random offset within radius
    angle = random.random() * 2 * __import__('math').pi
    r = random.random() ** 0.5 * radius_m
    dy = r * __import__('math').sin(angle)
    dx = r * __import__('math').cos(angle)

    new_lat = lat + dy / meters_per_deg_lat
    new_lon = lon + dx / meters_per_deg_lon
    return new_lat, new_lon


def haversine_distance(lat1, lon1, lat2, lon2):
    """Return distance in meters between two lat/lon pairs."""
    import math

    R = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c
