import math
from typing import List, Dict, Tuple

import requests


def _haversine(lat1, lon1, lat2, lon2):
    # meters
    R = 6371000.0
    import math

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def get_nearby_pois(lat: float, lon: float, radius_km: float = 5.0, max_results: int = 100) -> List[Dict]:
    """Try to retrieve POIs from OpenStreetMap Overpass API near (lat, lon).

    If Overpass is unreachable or `overpy` is not available, this function falls back to a
    minimal remote Wikipedia search (via the REST summary) and returns approximate results.
    The returned POIs are dictionaries with keys: name, lat, lon, tags.
    """
    radius_m = int(radius_km * 1000)
    print(f"Querying OSM Overpass for POIs within {radius_m} m of ({lat},{lon})")
    # Build Overpass query (simple): look for nodes/ways with some common tags
    query = f"""
    (node(around:{radius_m},{lat},{lon})[historic];
    node(around:{radius_m},{lat},{lon})[tourism];
    node(around:{radius_m},{lat},{lon})[amenity];
    way(around:{radius_m},{lat},{lon})[historic];
    relation(around:{radius_m},{lat},{lon})[historic];
    );
    out center meta;"""

    try:
        import overpy

        api = overpy.Overpass()
        res = api.query(query)
        pois = []
        # nodes
        for n in res.nodes:
            name = n.tags.get("name")
            if not name:
                continue
            pois.append({"name": name, "lat": float(n.lat), "lon": float(n.lon), "tags": dict(n.tags)})
        # ways (use center)
        for w in res.ways:
            name = w.tags.get("name")
            if not name:
                continue
            latc = getattr(w, "center_lat", None)
            lonc = getattr(w, "center_lon", None)
            if latc is None or lonc is None:
                # skip if no center provided
                continue
            pois.append({"name": name, "lat": float(latc), "lon": float(lonc), "tags": dict(w.tags)})
        # relations
        for r in res.relations:
            name = r.tags.get("name")
            if not name:
                continue
            latc = getattr(r, "center_lat", None)
            lonc = getattr(r, "center_lon", None)
            if latc is None or lonc is None:
                continue
            pois.append({"name": name, "lat": float(latc), "lon": float(lonc), "tags": dict(r.tags)})

        # de-duplicate by name, keep closest
        unique = {}
        for p in pois:
            key = p["name"]
            d = _haversine(lat, lon, p["lat"], p["lon"]) if p.get("lat") else float("inf")
            if key not in unique or d < unique[key]["__dist"]:
                p["__dist"] = d
                unique[key] = p

        out = list(unique.values())
        out.sort(key=lambda x: x.get("__dist", float("inf")))
        return out[:max_results]

    except Exception:
        # Fallback simple remote search using Wikipedia search API
        try:
            url = "https://en.wikipedia.org/w/api.php"
            params = {"action": "query", "list": "search", "srsearch": "monument near %f %f" % (lat, lon), "format": "json", "srlimit": max_results}
            r = requests.get(url, params=params, timeout=5)
            data = r.json()
            results = []
            for item in data.get("query", {}).get("search", []):
                title = item.get("title")
                # no coords available — set None
                results.append({"name": title, "lat": None, "lon": None, "tags": {}})
            return results
        except Exception:
            return []


if __name__ == "__main__":
    pois = get_nearby_pois(44.53286, 1.88986)
    print(f"Found {len(pois)} POIs")
    for p in pois:
        print(f"- {p['name']} at ({p['lat']}, {p['lon']})") 
        print(p)