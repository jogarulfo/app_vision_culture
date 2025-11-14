from typing import List, Dict, Optional
import numpy as np
import os

from vision.clip_model import ClipModel
from geo.poi_images import fetch_and_cache_poi_image
from geo.poi_retrieval import get_nearby_pois
from geo_localization import haversine_distance


class MatchEngine:
    def __init__(self, device="cpu", alpha=0.7, beta=0.3, max_radius_km=5.0):
        self.clip = ClipModel(device=device)
        self.alpha = alpha
        self.beta = beta
        self.max_radius_km = max_radius_km

        self.ref_image_embeddings = None
        self.ref_text_embeddings = None
        self.refs = []

    def prepare_references(self, pois: List[Dict]):
        # Build text descriptions
        texts = []
        for p in pois:
            name = p.get("name", "unknown place")
            poi_type = p.get("historic") or p.get("tourism") or "point of interest"
            texts.append(f"{name}, {poi_type} in France")

        # Encode text only (OSM provides no images)
        print(f"Encoding text for {len(texts)} POIs...")
        text_emb = self.clip.encode_texts(texts)

        # Normalize
        text_emb = text_emb / (np.linalg.norm(text_emb, axis=1, keepdims=True) + 1e-8)

        self.ref_text_embeddings = text_emb
        self.refs = pois

    def match_frame(self, frame):
        import torch

        if self.ref_text_embeddings is None:
            return None

        # Encode image ONCE
        img_emb = self.clip.encode_images([frame])[0]
        img_emb = img_emb / (np.linalg.norm(img_emb) + 1e-8)

        # Convert to torch
        img_t = torch.tensor(img_emb).unsqueeze(0)
        ref_t = torch.tensor(self.ref_text_embeddings)

        # Cosine similarity with all POIs
        sims = torch.nn.functional.cosine_similarity(img_t, ref_t).tolist()

        # Return best match
        best_idx = int(np.argmax(sims))
        return {
            "poi": self.refs[best_idx],
            "similarity": sims[best_idx]
        }
