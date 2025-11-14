import json
import os
from typing import Dict, Optional

import requests

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
LOCAL_MONUMENTS = os.path.join(DATA_DIR, "monuments.json")


def _load_local(monument_name: str) -> Optional[Dict]:
    if not os.path.exists(LOCAL_MONUMENTS):
        return None
    with open(LOCAL_MONUMENTS, "r", encoding="utf8") as f:
        db = json.load(f)
    return db.get(monument_name)


def fetch_info(monument_name: str) -> Dict:
    """Fetch a short description for a monument.

    1) Try local JSON database `data/monuments.json`.
    2) If not found, query Wikipedia REST API.
    Returns a dict with at least 'name' and 'description' keys.
    """
    local = _load_local(monument_name)
    if local:
        return {"name": monument_name, "description": local.get("description", "")}

    # Fallback: Wikipedia REST summary
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(monument_name)}"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            return {"name": data.get("title", monument_name), "description": data.get("extract", "")}
    except Exception:
        pass

    return {"name": monument_name, "description": "No description available."}
