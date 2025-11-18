import math
import time 
import random
import overpy
from typing import List, Dict, Tuple
from vision.clip_model import ClipModel

import requests
from geo.poi_images import fetch_and_cache_poi_image 

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

    # Retry parameters
    max_retries = 3
    delay_seconds = 2

    for attempt in range(max_retries):
        print(f"Attempt {attempt + 1}/{max_retries}: Querying OSM Overpass for POIs within {radius_m} m of ({lat},{lon})")
        
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
                print(p)
                key = p["name"]
                d = _haversine(lat, lon, p["lat"], p["lon"]) if p.get("lat") else float("inf")
                print(f"Distance: {d} meters")
                if key not in unique or d < unique[key]["__dist"]:
                    p["__dist"] = d
                    unique[key] = p
            
            out = list(unique.values())
            print(f"Found {len(out)} unique POIs")
            
            out.sort(key=lambda x: x.get("__dist", float("inf")))
            out = out[:max_results]
            print(f"After limiting to {max_results}: {len(out)} POIs")
            
            # Fetch images for each POI
            for j in range(len(out)):
                try:
                    image = fetch_and_cache_poi_image(out[j], 'data/references/')
                    out[j]['image_path'] = image
                    print(f"Image for {out[j]['name']}: {out[j]['image_path']}")
                except Exception as e:
                    print(f"Failed to fetch image for {out[j]['name']}: {e}")
                    out[j]['image_path'] = None
            
            # Check if we got any POIs
            if len(out) == 0:
                if attempt < max_retries - 1:
                    print(f"No POIs found, retrying after {delay_seconds} seconds...")
                    time.sleep(delay_seconds)
                    continue  # Try again
                else:
                    print("No POIs found after all retries")
                    raise Exception("No POIs found from Overpass")
            else:
                # Success! Return the POIs
                print(f"Successfully retrieved {len(out)} POIs")
                return out

        except overpy.exception.OverpassTooManyRequests:
            print(f"Overpass rate limit hit, waiting {delay_seconds} seconds...")
            if attempt < max_retries - 1:
                time.sleep(delay_seconds)
                continue
            else:
                print("Rate limit persists, falling back to Wikipedia search")
                
        except Exception as e:
            print(f"Overpass query failed: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying after {delay_seconds} seconds...")
                time.sleep(delay_seconds)
                continue

    # If we get here, all Overpass attempts failed - fallback to Wikipedia
    print("All Overpass attempts failed, falling back to Wikipedia search...")
    try:
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query", 
            "list": "search", 
            "srsearch": f"monument near {lat} {lon}", 
            "format": "json", 
            "srlimit": max_results
        }
        r = requests.get(url, params=params, timeout=5)
        data = r.json()
        results = []
        for item in data.get("query", {}).get("search", []):
            title = item.get("title")
            results.append({
                "name": title, 
                "lat": None, 
                "lon": None, 
                "tags": {},
                "image_path": None
            })
        print(f"Wikipedia fallback returned {len(results)} results")
        return results
    except Exception as e:
        print(f"Wikipedia fallback also failed: {e}")
        return []


if __name__ == "__main__":
    pois = get_nearby_pois(44.53286, 1.88986)
    print(f"\nFound {len(pois)} POIs")
    for p in pois:
        print(f"- {p['name']} at ({p['lat']}, {p['lon']})") 
        print(p)