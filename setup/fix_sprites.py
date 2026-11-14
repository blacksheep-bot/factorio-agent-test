#!/usr/bin/env python3
"""
GOTCHA fix: `fle sprites` only produces terrain/resource/icon sprites unless the
`basisu` CLI is installed, because entity spritesheets ship as .basis textures. Without
it the renderer draws ore/water/trees but NO entities (drills, belts, furnaces, player).

The HuggingFace dataset (Noddybear/fle_images) already contains pre-transcoded PNGs in
spritemaps/cache/, but keyed by the dataset author's absolute path
("_Users_jackhopkins_PycharmProjects_PaperclipMaximiser_.fle_spritemaps_..."), whereas
FLE looks them up as str(relative_basis_path).replace("/", "_") ->
".fle_spritemaps_...". This script symlinks the cached PNGs under the expected names and
re-runs sprite generation (run from the repo root; no network needed).
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
cache = Path(".fle/spritemaps/cache")
if not cache.is_dir():
    sys.exit("run `fle sprites` first (needs .fle/spritemaps)")

PREFIX = "_Users_jackhopkins_PycharmProjects_PaperclipMaximiser_"
n = 0
for p in cache.glob(PREFIX + "*.png"):
    target = cache / p.name[len(PREFIX):]  # -> .fle_spritemaps___base___graphics_entity_...png
    if not target.exists():
        target.symlink_to(p.name)
        n += 1
print(f"linked {n} cached entity PNGs")

from fle.agents.data.sprites.download import generate_sprites  # noqa: E402

ok = generate_sprites(input_dir=".fle/spritemaps", output_dir=".fle/sprites")
print("generate_sprites:", ok)
