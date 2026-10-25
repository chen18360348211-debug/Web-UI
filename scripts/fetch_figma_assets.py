"""Download original Figma MCP assets referenced by saved design contexts.

Only URLs and file sizes are inspected. Asset contents are never read or edited.
Run with --context-dir if the saved Figma context directory changes.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import re
import shutil
import subprocess
from urllib.parse import urlparse


DEFAULT_CONTEXT_DIR = Path(
    "C:/Users/60922/.codex/visualizations/2026/10/23/"
    "01a16694-20ec-78d2-b0b1-f7ed35a17715"
)
PROJECT_DIR = Path(__file__).resolve().parents[1]
PREFIX_PATTERN = re.compile(r'const\s+assetPathPrefix\s*=\s*["\']([^"\']+)["\']')
ASSET_PATTERN = re.compile(
    r'const\s+\w+\s*=\s*`\$\{assetPathPrefix\}(/[A-Za-z0-9._/-]+)`'
)


def collect_assets(context_dir: Path) -> tuple[dict[str, str], int]:
    manifest: dict[str, str] = {}
    context_paths = sorted(context_dir.glob("figma-*.txt"))
    if not context_paths:
        raise ValueError(f"No figma-*.txt contexts found in {context_dir}")
    for context_path in context_paths:
        context = context_path.read_text(encoding="utf-8-sig")
        prefix_match = PREFIX_PATTERN.search(context)
        suffixes = ASSET_PATTERN.findall(context)
        if suffixes and not prefix_match:
            raise ValueError(f"Asset prefix missing in {context_path}")
        if not prefix_match:
            continue
        prefix = prefix_match.group(1).rstrip("/")
        asset_group = Path(urlparse(prefix).path).name
        for suffix in suffixes:
            url = prefix + suffix
            filename = Path(urlparse(url).path).name
            if not filename or filename in {".", ".."}:
                raise ValueError(f"Invalid asset URL in {context_path}: {url}")
            manifest[url] = f"assets/figma/{asset_group}/{filename}"
    return manifest, len(context_paths)


def download_asset(curl: str, url: str, relative_path: str, dist_dir: Path) -> str:
    destination = dist_dir / relative_path
    if destination.is_file() and destination.stat().st_size > 0:
        return "skipped"
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = destination.with_name(destination.name + ".download")
    result = subprocess.run(
        [curl, "-L", "--fail", "--silent", "--show-error", "--retry", "3",
         "--retry-delay", "1", "--connect-timeout", "30", "--max-time", "180",
         "--output", str(temporary_path), url],
        text=True, capture_output=True,
    )
    if result.returncode:
        temporary_path.unlink(missing_ok=True)
        raise RuntimeError(f"Download failed for {url}: {result.stderr.strip()}")
    if not temporary_path.is_file() or temporary_path.stat().st_size == 0:
        temporary_path.unlink(missing_ok=True)
        raise RuntimeError(f"Download was empty: {url}")
    temporary_path.replace(destination)
    return "downloaded"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--context-dir", type=Path, default=DEFAULT_CONTEXT_DIR)
    parser.add_argument("--dist-dir", type=Path, default=PROJECT_DIR / "dist")
    parser.add_argument("--manifest", type=Path, default=PROJECT_DIR / "scripts/asset-map.json")
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    curl = shutil.which("curl.exe") or shutil.which("curl")
    if not curl:
        parser.error("curl.exe or curl is required")
    manifest, context_count = collect_assets(args.context_dir)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    counts = {"downloaded": 0, "skipped": 0}
    errors = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        futures = {
            executor.submit(download_asset, curl, url, path, args.dist_dir): url
            for url, path in manifest.items()
        }
        for future in as_completed(futures):
            try:
                counts[future.result()] += 1
            except Exception as exc:
                errors.append(str(exc))
    print(json.dumps({"contexts": context_count, "assets": len(manifest), **counts,
                      "errors": errors, "manifest": str(args.manifest)}, ensure_ascii=False))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
