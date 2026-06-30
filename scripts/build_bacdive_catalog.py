#!/usr/bin/env python3
"""Build a BacDive-primary offline catalog for Microbial Mayhem.

The game loads only data/catalog/microbial_mayhem_catalog.sqlite3 at runtime.
This script downloads BacDive strain records when network access is available,
caches raw responses, extracts BacDive phenotype fields, then enriches matching
strains with local MIBiG BGC information.
"""
from __future__ import annotations

import argparse
import csv
import http.client
import json
import random
import time
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from bacterial_catalog import BacteriumCatalogEntry, describe_entry, load_mibig_records, parse_name
from catalog_deduplication import deduplicate_fighters
from catalog_storage import write_catalog_database
from taxonomy_filter import BACTERIAL_GENERA
from trait_inference import infer_traits

API_ROOT = "https://api.bacdive.dsmz.de/v2"
DATA_DIR = REPO_ROOT / "data"
RAW_DIR = DATA_DIR / "bacdive" / "raw"
BACDIVE_RECORDS = DATA_DIR / "bacdive" / "bacdive_records.json"
CATALOG_DIR = DATA_DIR / "catalog"
CATALOG_PATH = CATALOG_DIR / "microbial_mayhem_catalog.sqlite3"
REPORT_PATH = CATALOG_DIR / "catalog_build_report.csv"
UNKNOWN = "Unknown"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a BacDive-primary Microbial Mayhem catalog.")
    parser.add_argument("--refresh", action="store_true", help="Redownload records even if cached raw responses exist.")
    parser.add_argument("--limit", type=int, help="Optional maximum BacDive IDs to fetch for a small development build.")
    parser.add_argument("--genera", nargs="*", default=sorted(BACTERIAL_GENERA), help="Bacterial genera to query from BacDive taxonomy endpoint.")
    parser.add_argument("--bacdive-json", type=Path, help="Use a local BacDive JSON export instead of downloading.")
    parser.add_argument("--sleep", type=float, default=0.05, help="Delay between API requests.")
    parser.add_argument("--timeout", type=float, default=10.0, help="Per-request timeout in seconds.")
    parser.add_argument("--retries", type=int, default=12, help="Attempts per request before leaving it for the next resumable run.")
    parser.add_argument("--strict", action="store_true", help="Stop at the first BacDive request failure instead of continuing with other genera.")
    return parser.parse_args()


def ensure_dirs() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    CATALOG_DIR.mkdir(parents=True, exist_ok=True)


def fetch_json(url: str, timeout: float, retries: int = 3) -> dict | list:
    request = urllib.request.Request(url, headers={"User-Agent": "MicrobialMayhem/1.0 catalog builder"})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except (
            urllib.error.URLError,
            TimeoutError,
            ConnectionError,
            http.client.HTTPException,
            json.JSONDecodeError,
        ) as exc:
            if attempt == retries - 1:
                raise
            delay = min(30.0, 1.5 * (2 ** attempt)) + random.uniform(0, 0.5)
            print(
                f"  transient download error ({type(exc).__name__}); "
                f"retrying in {delay:.1f}s [{attempt + 2}/{retries}]",
                flush=True,
            )
            time.sleep(delay)
    raise RuntimeError(f"Failed to fetch {url}")


def payload_records(payload: dict | list) -> list[dict]:
    """Return detail records from either BacDive response representation."""
    if isinstance(payload, list):
        return [record for record in payload if isinstance(record, dict)]
    if not isinstance(payload, dict):
        return []
    results = payload.get("results", payload)
    if isinstance(results, dict):
        return [record for record in results.values() if isinstance(record, dict)]
    if isinstance(results, list):
        return [record for record in results if isinstance(record, dict)]
    return []


def payload_ids(payload: dict | list) -> set[int]:
    """Extract returned BacDive IDs without relying on record field spelling."""
    if isinstance(payload, dict) and isinstance(payload.get("results"), dict):
        return {int(value) for value in payload["results"] if str(value).isdigit()}
    found: set[int] = set()
    for record in payload_records(payload):
        general = record.get("General", {})
        value = general.get("BacDive-ID", record.get("BacDive-ID")) if isinstance(general, dict) else record.get("BacDive-ID")
        if str(value).isdigit():
            found.add(int(value))
    return found


def write_json_atomic(path: Path, payload: dict | list) -> None:
    """Avoid treating a process-interrupted cache write as a valid download."""
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2))
    temporary.replace(path)


def collect_ids_for_genus(genus: str, refresh: bool, pause: float, timeout: float) -> list[int]:
    cache_path = RAW_DIR / f"taxon_{genus}.json"
    if cache_path.exists() and not refresh:
        ids = json.loads(cache_path.read_text()).get("results", [])
        print(f"  cached {genus}: {len(ids)} BacDive IDs", flush=True)
        return ids
    ids: list[int] = []
    url = f"{API_ROOT}/taxon/{genus}"
    pages = []
    while url:
        page = fetch_json(url, timeout=timeout)
        pages.append(page)
        ids.extend(page.get("results", []))
        url = page.get("next")
        time.sleep(pause)
    cache_path.write_text(json.dumps({"genus": genus, "results": ids, "pages": pages}, indent=2))
    print(f"  downloaded {genus}: {len(ids)} BacDive IDs", flush=True)
    return ids


def fetch_bacdive_records(
    ids: list[int], refresh: bool, pause: float, timeout: float, retries: int = 12
) -> list[dict]:
    records: list[dict] = []
    failed_ids: list[int] = []
    chunk_size = 20

    for start in range(0, len(ids), chunk_size):
        chunk = ids[start:start + chunk_size]
        cache_path = RAW_DIR / f"fetch_{chunk[0]}_{chunk[-1]}.json"
        payload = None
        if cache_path.exists() and not refresh:
            try:
                cached_payload = json.loads(cache_path.read_text())
                if set(chunk).issubset(payload_ids(cached_payload)):
                    payload = cached_payload
                    print(f"  cached detail records {start + 1}-{start + len(chunk)} of {len(ids)}", flush=True)
                else:
                    print(f"  incomplete cache for records {start + 1}-{start + len(chunk)}; downloading again", flush=True)
            except (OSError, json.JSONDecodeError):
                print(f"  unreadable cache for records {start + 1}-{start + len(chunk)}; downloading again", flush=True)

        if payload is None:
            print(
                f"  downloading detail records {start + 1}-"
                f"{start + len(chunk)} of {len(ids)}",
                flush=True,
            )

            chunk_failed_ids = list(chunk)
            try:
                payload = fetch_json(
                    f"{API_ROOT}/fetch/{';'.join(map(str, chunk))}",
                    timeout=timeout,
                    retries=retries,
                )
                missing = set(chunk) - payload_ids(payload)
                if missing:
                    chunk_failed_ids = sorted(missing)
                    raise RuntimeError(f"BacDive response omitted {len(missing)} requested ID(s): {sorted(missing)}")
                write_json_atomic(cache_path, payload)
                time.sleep(pause)

            except (
                urllib.error.URLError,
                TimeoutError,
                ConnectionError,
                http.client.HTTPException,
                json.JSONDecodeError,
                RuntimeError,
            ) as exc:
                print(
                    f"  warning: failed detail records "
                    f"{start + 1}-{start + len(chunk)}: {exc}",
                    flush=True,
                )
                failed_ids.extend(chunk_failed_ids)
                continue
        records.extend(payload_records(payload))

    if failed_ids:
        failure_path = RAW_DIR / "failed_detail_ids.json"
        write_json_atomic(failure_path, {"ids": failed_ids, "count": len(failed_ids)})
        failure_label = failure_path.relative_to(REPO_ROOT) if failure_path.is_relative_to(REPO_ROOT) else failure_path
        raise RuntimeError(
            f"BacDive download is incomplete: {len(failed_ids)} of {len(ids)} detail records "
            f"still need downloading. Progress is safely cached; rerun the same command to resume. "
            f"Missing IDs were written to {failure_label}."
        )

    failure_path = RAW_DIR / "failed_detail_ids.json"
    failure_path.unlink(missing_ok=True)
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
    failures: list[tuple[str, Any]] = []
    print(f"Collecting BacDive IDs for {len(args.genera)} genera...", flush=True)
    for index, genus in enumerate(args.genera, start=1):
        print(f"[{index}/{len(args.genera)}] Querying BacDive taxonomy for {genus}", flush=True)
        try:
            all_ids.extend(collect_ids_for_genus(genus, args.refresh, args.sleep, args.timeout))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, RuntimeError) as exc:
            failures.append((genus, exc))
            print(f"  warning: BacDive request failed for {genus}: {exc}", flush=True)
            if args.strict:
                raise
        if args.limit and len(set(all_ids)) >= args.limit:
            break
    ids = sorted(set(all_ids))[: args.limit] if args.limit else sorted(set(all_ids))
    if not ids:
        examples = "; ".join(f"{genus}: {exc}" for genus, exc in failures[:3])
        raise RuntimeError(
            "No BacDive IDs were downloaded. Check network access to "
            "https://api.bacdive.dsmz.de, try a smaller command such as "
            "`python3 scripts/build_bacdive_catalog.py --genera Bacillus --limit 25`, "
            "or provide a local export with `--bacdive-json`. "
            f"Recent failures: {examples or 'none'}"
        )
    print(f"Fetching {len(ids)} BacDive detail records...", flush=True)
    return fetch_bacdive_records(ids, args.refresh, args.sleep, args.timeout, args.retries)


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
    fighter_dicts, duplicates_removed = deduplicate_fighters([fighter.to_dict() for fighter in fighters])
    metadata = {
        "built_at": datetime.now(timezone.utc).isoformat(),
        "source": "BacDive primary; MIBiG BGC enrichment only",
        "bacdive_record_count": len(records),
        "playable_fighter_count": len(fighter_dicts),
        "duplicate_fighters_removed": duplicates_removed,
        "mibig_exact_ncbi_matches": sum(1 for f in fighter_dicts if f.get("bgc_match_confidence") == "exact_ncbi_tax_id"),
        "mibig_exact_name_matches": sum(1 for f in fighter_dicts if f.get("bgc_match_confidence") == "exact_scientific_name"),
        "mibig_species_fallback_matches": sum(1 for f in fighter_dicts if f.get("bgc_match_confidence") == "species_fallback"),
        "mibig_unmatched": sum(1 for f in fighter_dicts if f.get("bgc_match_confidence") == "unmatched"),
    }
    metadata = write_catalog_database(CATALOG_PATH, fighter_dicts, metadata)
    write_report([{"key": k, "value": v} for k, v in metadata.items()])
    print(f"Wrote {CATALOG_PATH.relative_to(REPO_ROOT)} with {len(fighter_dicts)} unique BacDive-derived fighters.")


if __name__ == "__main__":
    main()
