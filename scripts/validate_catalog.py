#!/usr/bin/env python3
"""Validate the maintained KernelSU-compatible catalog and detail files."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]


def require_url(value: str, label: str) -> None:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"{label} is not an absolute URL: {value!r}")


def main() -> None:
    catalog = json.loads((ROOT / "modules.json").read_text(encoding="utf-8"))
    if not isinstance(catalog, list) or not catalog:
        raise ValueError("modules.json must be a non-empty array")
    seen = set()
    for item in catalog:
        module_id = item.get("moduleId", "")
        if not module_id or module_id in seen:
            raise ValueError(f"invalid or duplicate moduleId: {module_id!r}")
        seen.add(module_id)
        latest = item.get("latestRelease") or {}
        require_url(latest.get("downloadUrl", ""), f"{module_id}.latestRelease.downloadUrl")
        detail_path = ROOT / "module" / f"{module_id}.json"
        detail = json.loads(detail_path.read_text(encoding="utf-8"))
        if detail.get("moduleId") != module_id:
            raise ValueError(f"detail id mismatch: {module_id}")
        if not detail.get("homepageUrl") or not detail.get("sourceUrl"):
            raise ValueError(f"{module_id} must define homepageUrl and sourceUrl")
        for key in ("url", "homepageUrl", "sourceUrl"):
            if detail.get(key):
                require_url(detail[key], f"{module_id}.{key}")
        if not isinstance(detail.get("releases"), list):
            raise ValueError(f"{module_id}.releases must be an array")
        for release in detail["releases"]:
            for asset in release.get("releaseAssets", []):
                require_url(asset.get("downloadUrl", ""), f"{module_id}.asset")
    print(f"validated {len(catalog)} module(s)")


if __name__ == "__main__":
    main()
