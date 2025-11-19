import os
from typing import Dict, Optional

import requests
from PIL import Image, ImageDraw, ImageFont
import urllib.parse

def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def fetch_and_cache_poi_image(poi: Dict, dest_dir: str) -> Optional[str]:
    """Given a POI dict with at least 'name' key and optionally 'wikidata' in tags, 
    try to fetch a representative image and save it to dest_dir. 
    Returns the local file path or None if no image could be fetched.

    Strategy:
    1. Try Wikidata API for the P18 (image) property.
    2. Fallback to Wikipedia summary endpoint (search by name).
    3. Generate placeholder image if all else fails.
    """
    
    # Ensure destination directory exists
    _ensure_dir(dest_dir)
    
    # Check if wikidata ID exists
    wikidata_id = poi.get('tags', {}).get('wikidata')
    
    # 1. Setup path and cache check
    if wikidata_id:
        safe_qid = wikidata_id.replace("/", "_")
        out_path = os.path.join(dest_dir, f"{safe_qid}.jpg")
    else:
        # Use name as fallback for filename
        safe_name = poi.get('name', 'unknown').replace("/", "_").replace(" ", "_")
        out_path = os.path.join(dest_dir, f"{safe_name}.jpg")
    
    if os.path.exists(out_path):
        print(f"Using cached image: {out_path}")
        return out_path

    # --- STRATEGY 1: Fetch via Wikidata QID (P18 property) ---
    if wikidata_id:
        try:
            print(f"Attempting Wikidata fetch for {wikidata_id}...")
            # Use EntityData API which provides complete entity information
            wikidata_api_url = f"https://www.wikidata.org/wiki/Special:EntityData/{wikidata_id}.json"
            
            headers = {"User-Agent": "MonumentRecognizer/1.0"}
            r = requests.get(wikidata_api_url, timeout=10, headers=headers)
            
            if r.status_code == 200:
                data = r.json()
                
                # Navigate to the entity's claims
                entity = data.get("entities", {}).get(wikidata_id, {})
                claims = entity.get("claims", {})
                
                # Look for P18 (image) property
                p18_claims = claims.get("P18", [])
                
                if p18_claims and len(p18_claims) > 0:
                    # Extract the filename from the first image claim
                    mainsnak = p18_claims[0].get("mainsnak", {})
                    datavalue = mainsnak.get("datavalue", {})
                    filename = datavalue.get("value")
                    
                    if filename:
                        print(f"Found image on Wikidata: {filename}")

                        # Construct the URL to download from Wikimedia Commons
                        # Special:FilePath provides direct access to the file
                        filename_encoded = urllib.parse.quote(filename.replace(" ", "_"))
                        commons_file_url = f"https://commons.wikimedia.org/wiki/Special:FilePath/{filename_encoded}?width=800"
                        
                        print(f"Fetching from Commons: {commons_file_url}")
                        rr = requests.get(commons_file_url, timeout=10, allow_redirects=True, headers=headers)
                        
                        if rr.status_code == 200 and len(rr.content) > 0:
                            with open(out_path, "wb") as f:
                                f.write(rr.content)
                            print(f"✓ Successfully saved Wikidata image to {out_path}")
                            return out_path
                        else:
                            print(f"✗ Commons returned status {rr.status_code}, content length: {len(rr.content)}")
                    else:
                        print("✗ No filename found in datavalue")
                else:
                    print(f"✗ No P18 (image) claims found for {wikidata_id}")
            else:
                print(f"✗ Wikidata API returned status {r.status_code}")
                
        except Exception as e:
            print(f"✗ Wikidata fetch failed for {wikidata_id}: {e}")
            import traceback
            traceback.print_exc()

    # --- STRATEGY 2: Fallback to Wikipedia Summary ---
    poi_name = poi.get('name')
    if poi_name:
        try:
            print(f"Attempting Wikipedia fetch for '{poi_name}'...")
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(poi_name)}"
            r = requests.get(url, timeout=6)
            if r.status_code == 200:
                data = r.json()
                thumb = data.get("thumbnail", {})
                thumb_url = thumb.get("source")
                if thumb_url:
                    print(f"Found Wikipedia thumbnail: {thumb_url}")
                    rr = requests.get(thumb_url, timeout=6)
                    if rr.status_code == 200:
                        with open(out_path, "wb") as f:
                            f.write(rr.content)
                        print(f"Successfully saved Wikipedia image to {out_path}")
                        return out_path
        except Exception as e:
            print(f"Wikipedia summary fetch failed for {poi_name}: {e}")

    # No image found
    print(f"No image found for {poi.get('name', 'Unknown POI')}")
    return None