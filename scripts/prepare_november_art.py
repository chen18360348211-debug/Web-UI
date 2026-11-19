"""Archive the November replacement artwork and encode responsive WebP copies.

The supplied originals are copied byte-for-byte. This script only scales and
encodes delivery copies; it does not composite, crop, recolor or edit artwork.
The existing image-manifest.json remains untouched.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import shutil

from PIL import Image, features

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
OUTPUT = DIST / "assets" / "optimized"
UPLOADS = DIST / "assets" / "uploads"
MANIFEST = OUTPUT / "november-art-manifest.json"


def prepare(source: Path, name: str) -> tuple[str, dict]:
    destination = UPLOADS / name
    if source.resolve() != destination.resolve():
        shutil.copyfile(source, destination)
    source_digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if hashlib.sha256(destination.read_bytes()).hexdigest() != source_digest:
        raise ValueError(f"Original copy is not byte-identical: {destination}")
    with Image.open(destination) as original:
        original.load()
        image = original.convert("RGBA" if "A" in original.getbands() else "RGB")
    has_alpha = image.mode == "RGBA" and image.getchannel("A").getextrema()[0] < 255
    if image.mode == "RGBA" and not has_alpha:
        image = image.convert("RGB")
    variants = []
    for width in (960, 1920, 3840):
        width = min(width, image.width)
        height = round(image.height * width / image.width)
        resized = image if width == image.width else image.resize((width, height), Image.Resampling.LANCZOS)
        output = OUTPUT / f"{destination.stem}-{source_digest[:12]}-{width}.webp"
        temporary = output.with_suffix(".webp.tmp")
        resized.save(temporary, format="WEBP", quality=95, method=6, exact=True)
        temporary.replace(output)
        with Image.open(output) as encoded:
            encoded.load()
            if encoded.size != resized.size:
                raise ValueError(f"Output size mismatch: {output}")
            if has_alpha and ("A" not in encoded.getbands() or encoded.getchannel("A").tobytes() != resized.getchannel("A").tobytes()):
                raise ValueError(f"Output transparency mismatch: {output}")
        variants.append({"path": output.relative_to(DIST).as_posix(), "width": width, "height": height, "bytes": output.stat().st_size})
    original_path = destination.relative_to(DIST).as_posix()
    return original_path, {
        "original": original_path,
        "originalBytes": destination.stat().st_size,
        "sha256": source_digest,
        "width": image.width,
        "height": image.height,
        "alpha": has_alpha,
        "category": "text-scene" if name.startswith("hero") else "scene",
        "quality": 95,
        "lossless": False,
        "default": next(v["path"] for v in variants if v["width"] == min(1920, image.width)),
        "srcset": ", ".join(f'{v["path"]} {v["width"]}w' for v in variants),
        "variants": variants,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--banner", type=Path, default=UPLOADS / "hero-20261119.png")
    parser.add_argument("--background", type=Path, default=UPLOADS / "package-background-20261119.jpg")
    args = parser.parse_args()
    if not features.check("webp"):
        raise SystemExit("Pillow lacks WebP support")
    UPLOADS.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    tasks = [(args.banner, "hero-20261119.png"), (args.background, "package-background-20261119.jpg")]
    with ThreadPoolExecutor(max_workers=2) as executor:
        images = dict(executor.map(lambda task: prepare(*task), tasks))
    manifest = {"version": 1, "format": "webp", "images": images}
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
