from typing import List, Dict, Optional
import numpy as np
import os

from vision.clip_model import ClipModel
from geo.poi_images import fetch_and_cache_poi_image
from geo.poi_retrieval import get_nearby_pois
from geo_localization import haversine_distance


class MatchEngine:
    def __init__(self, device="cpu", alpha=0.9, max_radius_km=5.0):
        self.clip = ClipModel(device=device)
        self.alpha = alpha
        self.beta = 1.0 - alpha
        self.max_radius_km = max_radius_km

        self.ref_image_embeddings = None
        self.ref_text_embeddings = None
        self.refs = []

    def prepare_references(self, pois: List[Dict]):
        # Filter POIs to only those with valid images
        pois_with_images = [p for p in pois if p.get("image_path") is not None]
        
        if not pois_with_images:
            print("Warning: No POIs with images found!")
            self.ref_text_embeddings = None
            self.ref_image_embeddings = None
            self.refs = []
            return
        
        print(f"Processing {len(pois_with_images)} POIs with images (out of {len(pois)} total)")
        
        # Build text descriptions
        texts = []
        images = []
        for p in pois_with_images:
            name = p.get("name", "unknown place")
            tags = p.get("tags", {})
            poi_type = tags.get("historic") or tags.get("tourism") or "point of interest"
            texts.append(f"{name}, {poi_type} in France")
            images.append(str(p["image_path"]))

        # Encode text and images
        print(f"Encoding text for {len(texts)} POIs...")
        text_emb = self.clip.encode_texts(texts)
        
        print(f"Encoding images for {len(images)} POIs...")
        image_emb = self.clip.encode_images(images)

        # Normalize
        text_emb = text_emb / (np.linalg.norm(text_emb, axis=1, keepdims=True) + 1e-8)
        image_emb = image_emb / (np.linalg.norm(image_emb, axis=1, keepdims=True) + 1e-8)
        
        self.ref_text_embeddings = text_emb
        self.ref_image_embeddings = image_emb
        self.refs = pois_with_images

    def match_frame(self, frame):
        import torch

        if self.ref_text_embeddings is None or len(self.refs) == 0:
            return None

        # Encode image ONCE
        img_emb = self.clip.encode_images([frame])[0]
        img_emb = img_emb / (np.linalg.norm(img_emb) + 1e-8)

        # Convert to torch
        img_t = torch.tensor(img_emb).unsqueeze(0)
        ref_txt_t = torch.tensor(self.ref_text_embeddings)
        ref_img_t = torch.tensor(self.ref_image_embeddings)

        # Cosine similarity with all POIs
        sims_txt = torch.nn.functional.cosine_similarity(img_t, ref_txt_t).tolist()
        sims_image = torch.nn.functional.cosine_similarity(img_t, ref_img_t).tolist()
        
        # Combined similarity score
        sims = [self.alpha * s_image + self.beta * s_text 
                for s_text, s_image in zip(sims_txt, sims_image)]
        
        # Return best match
        best_idx = int(np.argmax(sims))
        return {
            "poi": self.refs[best_idx],
            "similarity": sims[best_idx]
        }