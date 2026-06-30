#!/usr/bin/env python3
"""Migrate the legacy generated JSON catalog to normalized runtime SQLite."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from catalog_storage import write_catalog_database


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=REPO_ROOT / "data" / "catalog" / "microbial_mayhem_catalog.json")
    parser.add_argument("--output", type=Path, default=REPO_ROOT / "data" / "catalog" / "microbial_mayhem_catalog.sqlite3")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = json.loads(args.input.read_text())
    fighters = payload.get("fighters", payload if isinstance(payload, list) else [])
    metadata = payload.get("metadata", {}) if isinstance(payload, dict) else {}
    result = write_catalog_database(args.output, fighters, metadata)
    size_mb = args.output.stat().st_size / (1024 * 1024)
    print(
        f"Wrote {args.output} with {result['playable_fighter_count']} fighters, "
        f"{result['enrichment_profile_count']} shared profiles, {size_mb:.1f} MB."
    )


if __name__ == "__main__":
    main()
