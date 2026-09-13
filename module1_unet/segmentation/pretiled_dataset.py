"""
pretiled_dataset.py — Drop-in replacement for SARSegmentationDataset once
prepare_tiles.py has been run.

Every __getitem__ here is two torch.load() calls off local disk. No GDAL,
no rasterio, no repeated file opens, no NotGeoreferencedWarning spam. This
is the thing that should actually sit inside your DataLoader for training
runs going forward — SARSegmentationDataset (dataset.py) remains correct and
useful for the one-time prepare_tiles.py pass and for real inference, it's
just the wrong tool to call 10,000+ times per epoch against remote/GDAL
storage.

Returns the exact same tuple shape as SARSegmentationDataset.__getitem__
(image, mask, scene_id) so train.py's training loop needs no changes beyond
swapping which Dataset class gets constructed.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch.utils.data import Dataset
from src.dataset import NormalizationConfig, apply_normalization


class PreTiledDataset(Dataset):
    def __init__(self, entries: list[dict[str, Any]], norm_cfg: NormalizationConfig, require_mask: bool = True):
        if require_mask:
            entries = [e for e in entries if "mask_path" in e]
        if not entries:
            raise ValueError(
                f"No usable entries (require_mask={require_mask})"
            )

        self.entries = entries
        self.require_mask = require_mask
        self.norm_cfg = norm_cfg

    def __len__(self) -> int:
        return len(self.entries)

    def __getitem__(self, idx: int):
        entry = self.entries[idx]

        image_path = entry.get("image_path", entry.get("patch_path"))
        image = torch.load(image_path)
        image=torch.from_numpy(apply_normalization(image.numpy(), self.norm_cfg))

        if self.require_mask:
            mask = torch.load(entry["mask_path"])
            return image, mask, entry["scene_id"]

        return image, entry["scene_id"], {}
