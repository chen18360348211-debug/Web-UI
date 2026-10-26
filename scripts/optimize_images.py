"""Create deterministic, responsive WebP derivatives without changing source assets.

Run with the project's Python runtime (Pillow with WebP support is required).
The JSON manifest uses paths relative to dist so the page can be hosted under
a GitHub Pages project path. Identical PNG files share the same derivatives.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path

from PIL import Image, features


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DIST = PROJECT_ROOT / "dist"
ASSETS = DIST / "assets"
OUTPUT = ASSETS / "optimized"
MANIFEST = OUTPUT / "image-manifest.json"
LOSSLESS_NAMES = {"551-3475.png", "541-2117.png", "65260.png"}
TEXT_SCENE_NAMES = {"package-full.png", "package-thumbnail.png", "55950.png", "b848f.png"}


def encoding_plan(path: Path, size: tuple[int, int]) -> tuple[list[int], int, bool, str]:
    width, height = size
    if path.name in LOSSLESS_NAMES or max(size) <= 256:
        return [width], 100, True, "pixel-ui"
    if width == height:
        widths = sorted({min(width, value) for value in (400, 800, width)})
        return widths, 92, False, "product"
    # Retain a full-resolution candidate up to 3840 pixels for high-DPI screens.
    largest = min(width, 3840)
    widths = sorted({min(largest, value) for value in (960, 1920, largest)})
    quality = 95 if path.name in TEXT_SCENE_NAMES else 90
    return widths, quality, False, "text-scene" if quality == 95 else "scene"


def encode_group(group: tuple[str, list[Path]], force: bool) -> tuple[str, dict]:
    digest, paths = group
    first = paths[0]
    with Image.open(first) as original:
        original.load()
        image = original.convert("RGBA" if "A" in original.getbands() else "RGB")
    widths, quality, lossless, category = encoding_plan(first, image.size)
    # PNG alpha is encoded losslessly by WebP, including for lossy RGB imagery.
    alpha = image.getchannel("A") if image.mode == "RGBA" else None
    has_transparency = alpha is not None and alpha.getextrema()[0] < 255
    if image.mode == "RGBA" and not has_transparency:
        image = image.convert("RGB")
    variants = []
    for width in widths:
        height = max(1, round(image.height * width / image.width))
        resized = image if width == image.width else image.resize((width, height), Image.Resampling.LANCZOS)
        destination = OUTPUT / f"{first.stem}-{digest[:12]}-{width}.webp"
        if force or not destination.exists():
            temporary = destination.with_suffix(".webp.tmp")
            resized.save(temporary, format="WEBP", quality=quality, lossless=lossless, method=6, exact=True)
            temporary.replace(destination)
        with Image.open(destination) as encoded:
            if encoded.size != (width, height):
                raise ValueError(f"Incorrect output dimensions: {destination}")
            if has_transparency:
                if "A" not in encoded.getbands():
                    raise ValueError(f"Alpha channel missing: {destination}")
                # Verify transparency is unchanged after compression.
                if encoded.getchannel("A").tobytes() != resized.getchannel("A").tobytes():
                    raise ValueError(f"Alpha channel changed: {destination}")
        variants.append({
            "path": destination.relative_to(DIST).as_posix(),
            "width": width,
            "height": height,
            "bytes": destination.stat().st_size,
        })
    default_width = 800 if category == "product" else 1920
    default = next((item for item in variants if item["width"] >= min(image.width, default_width)), variants[-1])
    return digest, {
        "width": image.width,
        "height": image.height,
        "alpha": has_transparency,
        "category": category,
        "quality": quality,
        "lossless": lossless,
        "default": default["path"],
        "srcset": ", ".join(f'{item["path"]} {item["width"]}w' for item in variants),
        "variants": variants,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Regenerate existing WebP derivatives")
    parser.add_argument("--workers", type=int, default=3)
    args = parser.parse_args()
    if not features.check("webp"):
        raise SystemExit("Pillow was built without WebP support")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    groups: dict[str, list[Path]] = {}
    files = sorted(ASSETS.rglob("*.png"))
    for path in files:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        groups.setdefault(digest, []).append(path)
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        encoded = dict(executor.map(lambda group: encode_group(group, args.force), groups.items()))
    images = {}
    for digest, paths in groups.items():
        for path in paths:
            images[path.relative_to(DIST).as_posix()] = {
                "original": path.relative_to(DIST).as_posix(),
                "originalBytes": path.stat().st_size,
                "sha256": digest,
                **encoded[digest],
            }
    summary = {
        "originalFiles": len(files),
        "uniqueImages": len(groups),
        "originalBytes": sum(path.stat().st_size for path in files),
        "uniqueOriginalBytes": sum(paths[0].stat().st_size for paths in groups.values()),
        "allDerivativeBytes": sum(item["bytes"] for entry in encoded.values() for item in entry["variants"]),
        "uniqueDefaultBytes": sum(next(item["bytes"] for item in entry["variants"] if item["path"] == entry["default"]) for entry in encoded.values()),
    }
    MANIFEST.write_text(json.dumps({"version": 1, "format": "webp", "summary": summary, "images": images}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"Manifest: {MANIFEST.relative_to(PROJECT_ROOT).as_posix()}")


if __name__ == "__main__":
    main()
