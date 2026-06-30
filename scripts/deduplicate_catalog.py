#!/usr/bin/env python3
"""Remove duplicate fighter identities from the persisted game catalog."""
from __future__ import annotations

import json
import csv
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from catalog_deduplication import deduplicate_fighters

CATALOG_PATH = REPO_ROOT / "data" / "catalog" / "microbial_mayhem_catalog.json"
REPORT_PATH = REPO_ROOT / "data" / "catalog" / "catalog_build_report.csv"


def main() -> None:
    catalog = json.loads(CATALOG_PATH.read_text())
    original = catalog.get("fighters", [])
    fighters, removed = deduplicate_fighters(original)
    catalog["fighters"] = fighters
    metadata = catalog.setdefault("metadata", {})
    metadata["playable_fighter_count"] = len(fighters)
    metadata["duplicate_fighters_removed"] = int(metadata.get("duplicate_fighters_removed", 0)) + removed
    confidence_fields = {
        "mibig_exact_ncbi_matches": "exact_ncbi_tax_id",
        "mibig_exact_name_matches": "exact_scientific_name",
        "mibig_species_fallback_matches": "species_fallback",
        "mibig_unmatched": "unmatched",
    }
    for metadata_key, confidence in confidence_fields.items():
        metadata[metadata_key] = sum(fighter.get("bgc_match_confidence") == confidence for fighter in fighters)
    temporary = CATALOG_PATH.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(catalog, indent=2, sort_keys=True))
    temporary.replace(CATALOG_PATH)
    with REPORT_PATH.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["key", "value"])
        writer.writeheader()
        writer.writerows({"key": key, "value": value} for key, value in metadata.items())
    print(f"Removed {removed} duplicate fighters; {len(fighters)} unique fighters remain.")


if __name__ == "__main__":
    main()
