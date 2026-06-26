#!/usr/bin/env python3
"""Build the offline Microbial Mayhem game catalog.

This build step intentionally performs all expensive/local data processing before
normal gameplay. Gameplay loads only data/catalog/microbial_mayhem_catalog.json.

BacDive integration is cache-first: if a BacDive export is already present under
`data/bacdive/raw/` or provided via `--bacdive-json`, it is copied and recorded.
The script does not require network access or credentials to build the MIBiG-
backed playable catalog.
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from bacterial_catalog import build_catalog, catalog_stats, load_mibig_records

DATA_DIR = REPO_ROOT / "data"
BACDIVE_RAW_DIR = DATA_DIR / "bacdive" / "raw"
BACDIVE_RECORDS = DATA_DIR / "bacdive" / "bacdive_records.json"
CATALOG_DIR = DATA_DIR / "catalog"
CATALOG_PATH = CATALOG_DIR / "microbial_mayhem_catalog.json"
REPORT_PATH = CATALOG_DIR / "catalog_build_report.csv"
MIBIG_DATA_DIR = DATA_DIR / "mibig"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Microbial Mayhem's offline bacterial catalog.")
    parser.add_argument("--refresh", action="store_true", help="Rebuild outputs and overwrite cached aggregate files.")
    parser.add_argument("--bacdive-json", type=Path, help="Optional local BacDive JSON export to cache and merge metadata from in future builds.")
    return parser.parse_args()


def ensure_dirs() -> None:
    for path in (BACDIVE_RAW_DIR, CATALOG_DIR, MIBIG_DATA_DIR):
        path.mkdir(parents=True, exist_ok=True)


def prepare_bacdive_cache(args: argparse.Namespace) -> tuple[list, str]:
    if args.bacdive_json:
        raw_target = BACDIVE_RAW_DIR / args.bacdive_json.name
        if args.refresh or not raw_target.exists():
            shutil.copy2(args.bacdive_json, raw_target)
        if args.refresh or not BACDIVE_RECORDS.exists():
            shutil.copy2(args.bacdive_json, BACDIVE_RECORDS)
    if BACDIVE_RECORDS.exists() and not args.refresh:
        try:
            return json.loads(BACDIVE_RECORDS.read_text()), "cached BacDive records"
        except json.JSONDecodeError:
            return [], "BacDive cache exists but could not be parsed"
    if not BACDIVE_RECORDS.exists() or args.refresh:
        empty_payload = {"records": [], "note": "No BacDive API credentials/export supplied; MIBiG-only catalog built offline."}
        BACDIVE_RECORDS.write_text(json.dumps(empty_payload, indent=2))
        (BACDIVE_RAW_DIR / "bacdive_unavailable.json").write_text(json.dumps(empty_payload, indent=2))
    return [], "no BacDive API credentials/export supplied; MIBiG-only catalog built offline"


def write_report(rows: list[dict]) -> None:
    fieldnames = ["key", "value"]
    with REPORT_PATH.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    ensure_dirs()
    bacdive_records, bacdive_status = prepare_bacdive_cache(args)
    mibig_records = load_mibig_records()
    catalog = build_catalog(mibig_records)
    stats = catalog_stats()
    built_at = datetime.now(timezone.utc).isoformat()
    payload = {
        "metadata": {
            "built_at": built_at,
            "build_command": "python3 scripts/build_bacterial_catalog.py",
            "refresh_command": "python3 scripts/build_bacterial_catalog.py --refresh",
            "mibig_source": "local mibig_json/*.json bundled with repository",
            "mibig_record_count": len(mibig_records),
            "bacdive_status": bacdive_status,
            "bacdive_cached_record_count": len(bacdive_records) if isinstance(bacdive_records, list) else len(bacdive_records.get("records", [])) if isinstance(bacdive_records, dict) else 0,
            "playable_fighter_count": len(catalog),
            "excluded_record_count": stats.get("excluded_records", 0),
            "excluded_reasons": stats.get("excluded_reasons", {}),
        },
        "fighters": [entry.to_dict() for entry in catalog],
    }
    CATALOG_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True))
    write_report([
        {"key": "built_at", "value": built_at},
        {"key": "mibig_record_count", "value": len(mibig_records)},
        {"key": "playable_fighter_count", "value": len(catalog)},
        {"key": "excluded_record_count", "value": stats.get("excluded_records", 0)},
        {"key": "bacdive_status", "value": bacdive_status},
        {"key": "bacdive_cached_record_count", "value": payload["metadata"]["bacdive_cached_record_count"]},
    ])
    print(f"Wrote {CATALOG_PATH.relative_to(REPO_ROOT)} with {len(catalog)} fighters.")
    print(f"Wrote {REPORT_PATH.relative_to(REPO_ROOT)}.")


if __name__ == "__main__":
    main()
