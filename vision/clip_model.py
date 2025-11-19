from typing import List, Union
import os
from PIL import Image
import numpy as np
import open_clip
import torch


class ClipModel:
    """Light wrapper that tries to load an OpenCLIP model or falls back to
    SentenceTransformer-based model if available.

    Methods:
      - encode_images(list_of_paths_or_pil_or_ndarray) -> np.ndarray (N, D)
      - encode_texts(list_of_str) -> np.ndarray (N, D)
    """

    def __init__(self, device: str = "cpu"):
        self.device = device
        self.model = None
        self.preprocess = None
        self.backend = None

        # Try open_clip
        try:
            import open_clip
            import torch
            self.backend = "open_clip"
            model, _, preprocess = open_clip.create_model_and_transforms("ViT-B-32", pretrained="openai")
            model.eval()
            if device != "cpu":
                model.to(device)
            self.model = model
            self.preprocess = preprocess
            print(f"Using OpenCLIP backend on device {device}")
        except Exception:
            # Fallback to sentence-transformers if available
            try:
                from sentence_transformers import SentenceTransformer

                # some installations provide a CLIP-like model name
                self.backend = "sentence_transformers"
                self.model = SentenceTransformer("clip-ViT-B-32")
            except Exception:
                self.backend = None

    def encode_images(self, items: List[Union[str, Image.Image, np.ndarray]]) -> np.ndarray:
        imgs = []
        pil_list = []
        for it in items:
            if isinstance(it, str):
                pil = Image.open(it).convert("RGB")
            elif isinstance(it, np.ndarray):
                pil = Image.fromarray(it[..., ::-1]) if it.dtype == "uint8" else Image.fromarray(it)
            else:
                pil = it.convert("RGB")
            pil_list.append(pil)
        if self.backend == "open_clip":
            import torch
            import open_clip
            tensors = [self.preprocess(p) for p in pil_list]
            batch = torch.stack(tensors).to(self.device)
            with torch.no_grad():
                emb = self.model.encode_image(batch)
                emb = emb.cpu().numpy()
            return emb

        if self.backend == "sentence_transformers":
            try:
                # SentenceTransformer can accept PIL images for some models
                emb = self.model.encode(pil_list, convert_to_numpy=True)
                return emb
            except Exception:
                # fallback to encoding file names as text (worse but graceful)
                names = [getattr(it, "filename", str(i)) for i, it in enumerate(items)]
                return self.encode_texts(names)

        # No model available: return zero vectors
        return np.zeros((len(pil_list), 512), dtype=float)

    def encode_texts(self, texts: List[str]) -> np.ndarray:
        if self.backend == "open_clip":
            import torch
            tokenizer = open_clip.tokenize(texts).to(self.device)
            with torch.no_grad():
                emb = self.model.encode_text(tokenizer)
                emb = emb.cpu().numpy()
            return emb
        if self.backend == "sentence_transformers":
            return self.model.encode(texts, convert_to_numpy=True)
        # fallback
        import numpy as np

        return np.zeros((len(texts), 512), dtype=float)
