#!/usr/bin/env python3
"""Build a BacDive-primary offline catalog for Microbial Mayhem.

The game loads only data/catalog/microbial_mayhem_catalog.json at runtime.
This script downloads BacDive strain records when network access is available,
caches raw responses, extracts BacDive phenotype fields, then enriches matching
strains with local MIBiG BGC information.
"""
from __future__ import annotations

import argparse
import csv
import json
import time
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from bacterial_catalog import BacteriumCatalogEntry, describe_entry, load_mibig_records, parse_name
from taxonomy_filter import BACTERIAL_GENERA
from trait_inference import infer_traits

API_ROOT = "https://api.bacdive.dsmz.de/v2"
DATA_DIR = REPO_ROOT / "data"
RAW_DIR = DATA_DIR / "bacdive" / "raw"
BACDIVE_RECORDS = DATA_DIR / "bacdive" / "bacdive_records.json"
CATALOG_DIR = DATA_DIR / "catalog"
CATALOG_PATH = CATALOG_DIR / "microbial_mayhem_catalog.json"
REPORT_PATH = CATALOG_DIR / "catalog_build_report.csv"
UNKNOWN = "Unknown"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a BacDive-primary Microbial Mayhem catalog.")
    parser.add_argument("--refresh", action="store_true", help="Redownload records even if cached raw responses exist.")
    parser.add_argument("--limit", type=int, help="Optional maximum BacDive IDs to fetch for a small development build.")
    parser.add_argument("--genera", nargs="*", default=sorted(BACTERIAL_GENERA), help="Bacterial genera to query from BacDive taxonomy endpoint.")
    parser.add_argument("--bacdive-json", type=Path, help="Use a local BacDive JSON export instead of downloading.")
    parser.add_argument("--sleep", type=float, default=0.05, help="Delay between API requests.")
    return parser.parse_args()


def ensure_dirs() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    CATALOG_DIR.mkdir(parents=True, exist_ok=True)


def fetch_json(url: str, retries: int = 3) -> dict | list:
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            if attempt == retries - 1:
                raise
            time.sleep(1 + attempt)
    raise RuntimeError(f"Failed to fetch {url}")


def collect_ids_for_genus(genus: str, refresh: bool, pause: float) -> list[int]:
    cache_path = RAW_DIR / f"taxon_{genus}.json"
    if cache_path.exists() and not refresh:
        return json.loads(cache_path.read_text()).get("results", [])
    ids: list[int] = []
    url = f"{API_ROOT}/taxon/{genus}"
    pages = []
    while url:
        page = fetch_json(url)
        pages.append(page)
        ids.extend(page.get("results", []))
        url = page.get("next")
        time.sleep(pause)
    cache_path.write_text(json.dumps({"genus": genus, "results": ids, "pages": pages}, indent=2))
    return ids


def fetch_bacdive_records(ids: list[int], refresh: bool, pause: float) -> list[dict]:
    records: list[dict] = []
    for start in range(0, len(ids), 100):
        chunk = ids[start:start + 100]
        cache_path = RAW_DIR / f"fetch_{chunk[0]}_{chunk[-1]}.json"
        if cache_path.exists() and not refresh:
            payload = json.loads(cache_path.read_text())
        else:
            payload = fetch_json(f"{API_ROOT}/fetch/{';'.join(map(str, chunk))}")
            cache_path.write_text(json.dumps(payload, indent=2))
            time.sleep(pause)
        if isinstance(payload, dict):
            records.extend(payload.values() if all(str(k).isdigit() for k in payload) else payload.get("results", []))
        elif isinstance(payload, list):
            records.extend(payload)
    return records


def all_values(obj, wanted: tuple[str, ...]) -> list[str]:
    found: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            key_norm = key.lower().replace("_", " ")
            if any(w in key_norm for w in wanted):
                if isinstance(value, (str, int, float)):
                    found.append(str(value))
                elif isinstance(value, list):
                    found.extend(str(v) for v in value if isinstance(v, (str, int, float)))
            found.extend(all_values(value, wanted))
    elif isinstance(obj, list):
        for item in obj:
            found.extend(all_values(item, wanted))
    return [v for v in found if v and v.lower() not in {"none", "null"}]


def first_value(record: dict, *keys: str) -> str:
    values = all_values(record, tuple(k.lower() for k in keys))
    return values[0] if values else UNKNOWN


def scientific_name(record: dict) -> str:
    for keys in [("full scientific name",), ("species",), ("taxon name",), ("name",)]:
        value = first_value(record, *keys)
        if value != UNKNOWN and len(value.split()) >= 2:
            return value
    return f"BacDive strain {first_value(record, 'bacdive id', 'id')}"


def bacdive_id(record: dict) -> str:
    return first_value(record, "bacdive id", "bacdive_id", "id")


def ncbi_tax_id(record: dict) -> str:
    return first_value(record, "ncbi tax id", "ncbi taxon id", "tax id")


def strain_text(record: dict) -> str:
    return first_value(record, "strain number", "culture collection", "designation", "strain")


def concise(values: list[str], max_items: int = 4) -> str:
    unique = []
    for value in values:
        if value not in unique:
            unique.append(value)
    return "; ".join(unique[:max_items]) if unique else UNKNOWN


def build_mibig_indexes() -> tuple[dict[str, list], dict[str, list], dict[str, list]]:
    by_tax: dict[str, list] = defaultdict(list)
    by_name: dict[str, list] = defaultdict(list)
    by_species: dict[str, list] = defaultdict(list)
    for record in load_mibig_records():
        cluster = record.cluster
        name = record.organism_name
        tax = str(cluster.get("ncbi_tax_id") or "")
        if tax:
            by_tax[tax].append(record)
        by_name[name.casefold()].append(record)
        species = " ".join(name.split()[:2]).casefold()
        if species:
            by_species[species].append(record)
    return by_tax, by_name, by_species


def mibig_matches(name: str, tax_id: str, indexes) -> tuple[list, str]:
    by_tax, by_name, by_species = indexes
    if tax_id and tax_id in by_tax:
        return by_tax[tax_id], "exact_ncbi_tax_id"
    if name.casefold() in by_name:
        return by_name[name.casefold()], "exact_scientific_name"
    species = " ".join(name.split()[:2]).casefold()
    if species in by_species:
        return by_species[species], "species_fallback"
    return [], "unmatched"


def entry_from_bacdive(record: dict, indexes) -> BacteriumCatalogEntry:
    name = scientific_name(record)
    display, genus, species, parsed_strain = parse_name(name)
    strain = strain_text(record) if strain_text(record) != UNKNOWN else parsed_strain
    tax_id = ncbi_tax_id(record)
    matches, confidence = mibig_matches(name, tax_id, indexes)
    accessions, biosyn, products, moieties, activities, traits = [], [], [], [], [], []
    for match in matches:
        accessions.append(match.accession)
        cluster = match.cluster
        biosyn.extend(cluster.get("biosyn_class") or [])
        traits.extend(infer_traits(match.accession, cluster))
        for compound in cluster.get("compounds") or []:
            products.append(compound.get("compound", ""))
            activities.extend(a.get("activity", "") for a in compound.get("chem_acts") or [])
            moieties.extend(m.get("moiety", "") for m in compound.get("chem_moieties") or [])
    def uniq(vals):
        out=[]
        for v in vals:
            v=str(v).strip()
            if v and v not in out:
                out.append(v)
        return out
    entry = BacteriumCatalogEntry(
        catalog_id=f"bacdive:{bacdive_id(record)}",
        full_name=name,
        display_name=display,
        genus=genus,
        species=species,
        strain=strain,
        accessions=uniq(accessions),
        biosyn_classes=uniq(biosyn),
        products=uniq(products),
        compound_classes=uniq(moieties),
        activities=uniq(activities),
        traits=traits,
        record_count=len(matches),
        taxonomy_group="Bacteria/Archaea from BacDive",
        taxonomy_evidence="BacDive taxonomy endpoint/detail record",
        source="BacDive",
        bacdive_id=bacdive_id(record),
        ncbi_tax_id=tax_id,
        gram_stain=first_value(record, "gram stain"),
        cell_shape=first_value(record, "cell shape", "shape"),
        motility=first_value(record, "motility", "flagella"),
        oxygen_requirements=first_value(record, "oxygen tolerance", "oxygen requirement", "oxygen"),
        temperature_range=concise(all_values(record, ("temperature", "growth temperature"))),
        ph_range=concise(all_values(record, ("ph", "pH"))),
        salinity_range=concise(all_values(record, ("salinity", "salt", "nacl"))),
        metabolism=concise(all_values(record, ("metabolism", "metabolite", "energy source"))),
        isolation_habitat=concise(all_values(record, ("isolation", "habitat", "sample"))),
        host=first_value(record, "host"),
        biosafety=concise(all_values(record, ("pathogenicity", "biosafety", "risk group", "virulence"))),
        colony_appearance=first_value(record, "colony morphology", "colony appearance", "colony"),
        bgc_match_confidence=confidence,
    )
    entry.curious_fact = bacdive_fun_fact(entry)
    entry.description = bacdive_description(entry)
    return entry


def bacdive_fun_fact(entry: BacteriumCatalogEntry) -> str:
    if entry.isolation_habitat != UNKNOWN:
        return f"BacDive reports isolation/habitat information: {entry.isolation_habitat}."
    if entry.products:
        return f"MIBiG links this BacDive strain/species to {entry.products[0]}."
    return "BacDive phenotype fields are available for offline play."


def bacdive_description(entry: BacteriumCatalogEntry) -> str:
    return (
        f"BacDive strain {entry.bacdive_id}: {entry.full_name}. "
        f"Gram stain: {entry.gram_stain}; shape: {entry.cell_shape}; motility: {entry.motility}; "
        f"oxygen: {entry.oxygen_requirements}. BGC match: {entry.bgc_match_confidence}."
    )


def load_or_download_bacdive(args: argparse.Namespace) -> list[dict]:
    if args.bacdive_json:
        records = json.loads(args.bacdive_json.read_text())
        if isinstance(records, list):
            return records
        return records.get("records", [])
    all_ids: list[int] = []
    for genus in args.genera:
        all_ids.extend(collect_ids_for_genus(genus, args.refresh, args.sleep))
        if args.limit and len(set(all_ids)) >= args.limit:
            break
    ids = sorted(set(all_ids))[: args.limit]
    return fetch_bacdive_records(ids, args.refresh, args.sleep)


def write_report(rows: list[dict]) -> None:
    with REPORT_PATH.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["key", "value"])
        writer.writeheader(); writer.writerows(rows)


def main() -> None:
    args = parse_args()
    RAW_DIR.mkdir(parents=True, exist_ok=True); CATALOG_DIR.mkdir(parents=True, exist_ok=True)
    records = load_or_download_bacdive(args)
    BACDIVE_RECORDS.write_text(json.dumps({"records": records}, indent=2))
    indexes = build_mibig_indexes()
    fighters = [entry_from_bacdive(record, indexes) for record in records]
    fighters = [fighter for fighter in fighters if fighter.full_name and fighter.bacdive_id]
    metadata = {
        "built_at": datetime.now(timezone.utc).isoformat(),
        "source": "BacDive primary; MIBiG BGC enrichment only",
        "bacdive_record_count": len(records),
        "playable_fighter_count": len(fighters),
        "mibig_exact_ncbi_matches": sum(1 for f in fighters if f.bgc_match_confidence == "exact_ncbi_tax_id"),
        "mibig_exact_name_matches": sum(1 for f in fighters if f.bgc_match_confidence == "exact_scientific_name"),
        "mibig_species_fallback_matches": sum(1 for f in fighters if f.bgc_match_confidence == "species_fallback"),
        "mibig_unmatched": sum(1 for f in fighters if f.bgc_match_confidence == "unmatched"),
    }
    CATALOG_PATH.write_text(json.dumps({"metadata": metadata, "fighters": [f.to_dict() for f in fighters]}, indent=2, sort_keys=True))
    write_report([{"key": k, "value": v} for k, v in metadata.items()])
    print(f"Wrote {CATALOG_PATH.relative_to(REPO_ROOT)} with {len(fighters)} BacDive-derived fighters.")


if __name__ == "__main__":
    main()
