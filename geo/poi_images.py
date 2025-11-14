import os
from typing import Dict

import requests
from PIL import Image, ImageDraw, ImageFont


def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def fetch_and_cache_poi_image(poi: Dict, dest_dir: str) -> str:
    """Given a POI dict with at least a 'name' key, try to fetch a representative image and
    save it to dest_dir. Returns the local file path.

    Strategy:
    - Try Wikipedia REST summary for a thumbnail
    - If found, download the thumbnail
    - Otherwise, create a small placeholder image with the name
    """
    _ensure_dir(dest_dir)
    safe_name = poi["name"].replace("/", "_")
    out_path = os.path.join(dest_dir, f"{safe_name}.jpg")
    if os.path.exists(out_path):
        return out_path

    # Try Wikipedia summary endpoint
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(poi['name'])}"
        r = requests.get(url, timeout=6)
        if r.status_code == 200:
            data = r.json()
            thumb = data.get("thumbnail", {})
            thumb_url = thumb.get("source")
            if thumb_url:
                rr = requests.get(thumb_url, timeout=6)
                if rr.status_code == 200:
                    with open(out_path, "wb") as f:
                        f.write(rr.content)
                    return out_path
    except Exception:
        pass

    # Placeholder image
    try:
        img = Image.new("RGB", (640, 360), color=(80, 80, 80))
        d = ImageDraw.Draw(img)
        try:
            font = ImageFont.load_default()
        except Exception:
            font = None
        txt = poi["name"][:60]
        d.text((10, 160), txt, fill=(255, 255, 255), font=font)
        img.save(out_path, format="JPEG")
        return out_path
    except Exception:
        # Last resort: return path even if not created
        return out_path
