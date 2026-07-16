#!/usr/bin/env python3
"""Build a versioned lightweight web roster from developer-retained catalog data."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "data" / "catalog" / "microbial_mayhem_catalog.json"
OUTPUT = ROOT / "web" / "public" / "data"
CONTENT_VERSION = "2026.07.1"
SCHEMA_VERSION = 2


def clean(value) -> str:
    return re.sub(r"</?I>", "", str(value or ""), flags=re.I).strip()


def known(value) -> bool:
    return clean(value).casefold() not in {"", "unknown", "no", "none", "not specified", "no data"}


def compact_fighter(item: dict) -> dict:
    traits = [{
        "trait": clean(value.get("trait")), "evidenceLevel": clean(value.get("evidence_level")),
        "field": clean(value.get("field")), "explanation": clean(value.get("explanation")),
    } for value in item.get("traits", []) if value.get("trait")]
    name = clean(item.get("full_name"))
    return {
        "catalogId": clean(item.get("catalog_id")), "fullName": name,
        "displayName": clean(item.get("display_name")) or name,
        "searchKey": " ".join(filter(None, [name, clean(item.get("strain")), clean(item.get("genus"))])).casefold(),
        "strain": clean(item.get("strain")), "accessions": item.get("accessions", []),
        "products": [clean(v) for v in item.get("products", []) if clean(v)],
        "activities": [clean(v) for v in item.get("activities", []) if clean(v)], "traits": traits,
        "description": clean(item.get("description")), "curiousFact": clean(item.get("curious_fact")),
        "habitat": clean(item.get("isolation_habitat")), "colonyAppearance": clean(item.get("colony_appearance")),
        "cellShape": clean(item.get("cell_shape")) or "Unknown", "motility": clean(item.get("motility")) or "Unknown",
        "provenance": {"source": clean(item.get("source")), "bacdiveId": clean(item.get("bacdive_id")), "contentVersion": CONTENT_VERSION},
    }


def quality(item: dict) -> tuple:
    phenotype = sum(known(item.get(field)) for field in ("cell_shape", "motility", "isolation_habitat"))
    enrichment = sum(bool(item.get(field)) for field in ("accessions", "products", "activities", "traits"))
    return phenotype, enrichment, len(clean(item.get("description")))


def select_core(items: list[dict], limit: int) -> list[dict]:
    by_genus: dict[str, list[dict]] = defaultdict(list)
    for item in items:
        if item.get("catalog_id") and item.get("full_name"):
            by_genus[clean(item.get("genus")) or "Unknown"].append(item)
    for values in by_genus.values():
        values.sort(key=quality, reverse=True)
    chosen = []
    while len(chosen) < limit:
        progressed = False
        for genus in sorted(by_genus):
            if by_genus[genus]: chosen.append(by_genus[genus].pop(0)); progressed = True
            if len(chosen) >= limit: break
        if not progressed: break
    return chosen


def write_json(path: Path, payload) -> dict:
    body = (json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n").encode()
    path.write_bytes(body)
    return {"path": path.name, "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE); parser.add_argument("--limit", type=int, default=384); args = parser.parse_args()
    raw = json.loads(args.source.read_text()); items = raw.get("fighters", raw) if isinstance(raw, dict) else raw
    selected = [compact_fighter(item) for item in select_core(items, args.limit)]
    OUTPUT.mkdir(parents=True, exist_ok=True)
    core = write_json(OUTPUT / "fighters-core.v2.json", {"schemaVersion": SCHEMA_VERSION, "contentVersion": CONTENT_VERSION, "fighters": selected})
    index = write_json(OUTPUT / "search-index.v2.json", [{"catalogId": f["catalogId"], "fullName": f["fullName"], "strain": f["strain"], "searchKey": f["searchKey"]} for f in selected])
    manifest = {"schemaVersion": SCHEMA_VERSION, "contentVersion": CONTENT_VERSION, "builtAt": datetime.now(timezone.utc).isoformat(), "fighterCount": len(selected), "sourcePolicy": "Developer-retained BacDive primary catalog with MIBiG enrichment; raw inputs excluded.", "files": [core, index], "compatibility": {"minimumClient": "0.1.0", "stableIdField": "catalogId"}}
    write_json(OUTPUT / "manifest.v2.json", manifest)
    print(f"Wrote {len(selected)}-fighter web roster to {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__": main()
