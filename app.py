import argparse
import os
import time
from typing import Tuple

import cv2

from camera_stream import CameraStream
from data_fetcher import fetch_info
from geo_localization import get_mock_gps
from overlay import draw_overlay

from geo.poi_retrieval import get_nearby_pois
from vision.match_engine import MatchEngine




def main(src,gps,radius_km=1,max_pois=100,sim_threshold=0.5,sample_fps=500):
    # get mock or device GPS (mock by default)

    print("Retrieving POIs near", gps)
    pois = get_nearby_pois(gps[0], gps[1], radius_km=radius_km, max_results=max_pois)
    print(f"Found {len(pois)} POIs (using radius {radius_km} km)")

    # prepare match engine
    engine = MatchEngine(device="cpu", alpha=0.9, max_radius_km=radius_km)
    image_cache = os.path.join(os.path.dirname(__file__), "data", "references")
    engine.prepare_references(pois)

    last_match = None
    sample_every = max(1, int(1.0 / sample_fps)) if sample_fps > 0 else 30
    counter = 0

    with CameraStream(src=src) as stream:
        for frame in stream.frames():
            counter += 1
            if counter % sample_every == 0:
                match = engine.match_frame(frame)
                print(f"Match: {match}")
                if match and match.get("similarity", 0) >= sim_threshold:
                    info = fetch_info(match["poi"]["name"])
                    display_text = f"{info.get('name')} - {info.get('description')[:200]}"
                elif match:
                    display_text = f"{match.get('name')} (low confidence)"
                else:
                    display_text = "No match"
                last_match = (display_text, match)
            else:
                display_text, match = last_match if last_match else ("No match yet", None)

            out = draw_overlay(frame, display_text, score=match.get("score") if match else None)

            cv2.imshow("AR Monument Recognition", out)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main('data/video_chateau.mp4',(44.5216141, 1.9397062),max_pois=50)
