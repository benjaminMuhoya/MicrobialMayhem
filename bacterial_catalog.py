"""Build and query a bacterial fighter catalog from local MIBiG JSON records."""
from __future__ import annotations

import json
import random
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from catalog_storage import load_catalog_database
from gui_helpers import pluralize
from taxonomy_filter import classify_organism
from trait_inference import TraitEvidence, infer_traits

REPO_ROOT = Path(__file__).resolve().parent
MIBIG_DIR = REPO_ROOT / "mibig_json"
OFFLINE_CATALOG_PATH = REPO_ROOT / "data" / "catalog" / "microbial_mayhem_catalog.sqlite3"
BUILD_COMMAND = "python3 scripts/build_bacdive_catalog.py"
CATALOG_STATS = {"included_records": 0, "excluded_records": 0, "excluded_reasons": {}, "playable_entries": 0}


@dataclass(frozen=True)
class MibigRecord:
    accession: str
    organism_name: str
    cluster: dict


@dataclass
class BacteriumCatalogEntry:
    catalog_id: str
    full_name: str
    display_name: str
    genus: str
    species: str
    strain: str
    accessions: list[str] = field(default_factory=list)
    biosyn_classes: list[str] = field(default_factory=list)
    products: list[str] = field(default_factory=list)
    compound_classes: list[str] = field(default_factory=list)
    activities: list[str] = field(default_factory=list)
    traits: list[TraitEvidence] = field(default_factory=list)
    record_count: int = 0
    description: str = ""
    taxonomy_group: str = "Bacteria"
    taxonomy_evidence: str = ""
    colony_appearance: str = "No curated morphology information available."
    curious_fact: str = ""
    source: str = "MIBiG"
    bacdive_id: str = ""
    ncbi_tax_id: str = ""
    gram_stain: str = "Unknown"
    cell_shape: str = "Unknown"
    motility: str = "Unknown"
    oxygen_requirements: str = "Unknown"
    temperature_range: str = "Unknown"
    ph_range: str = "Unknown"
    salinity_range: str = "Unknown"
    metabolism: str = "Unknown"
    isolation_habitat: str = "Unknown"
    host: str = "Unknown"
    biosafety: str = "Unknown"
    bgc_match_confidence: str = "unmatched"

    def has_trait(self, trait: str) -> bool:
        return any(e.trait == trait for e in self.traits)

    def trait_summary(self) -> str:
        names = []
        for evidence in self.traits:
            if evidence.trait not in names:
                names.append(evidence.trait)
        return ", ".join(names[:4]) if names else "traits unknown"

    def to_dict(self) -> dict:
        return {
            "catalog_id": self.catalog_id,
            "full_name": self.full_name,
            "display_name": self.display_name,
            "genus": self.genus,
            "species": self.species,
            "strain": self.strain,
            "accessions": self.accessions,
            "biosyn_classes": self.biosyn_classes,
            "products": self.products,
            "compound_classes": self.compound_classes,
            "activities": self.activities,
            "traits": [e.__dict__ for e in self.traits],
            "record_count": self.record_count,
            "description": self.description,
            "taxonomy_group": self.taxonomy_group,
            "taxonomy_evidence": self.taxonomy_evidence,
            "colony_appearance": self.colony_appearance,
            "curious_fact": self.curious_fact,
            "source": self.source,
            "bacdive_id": self.bacdive_id,
            "ncbi_tax_id": self.ncbi_tax_id,
            "gram_stain": self.gram_stain,
            "cell_shape": self.cell_shape,
            "motility": self.motility,
            "oxygen_requirements": self.oxygen_requirements,
            "temperature_range": self.temperature_range,
            "ph_range": self.ph_range,
            "salinity_range": self.salinity_range,
            "metabolism": self.metabolism,
            "isolation_habitat": self.isolation_habitat,
            "host": self.host,
            "biosafety": self.biosafety,
            "bgc_match_confidence": self.bgc_match_confidence,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BacteriumCatalogEntry":
        data = dict(data)
        data["traits"] = [TraitEvidence(**trait) for trait in data.get("traits", [])]
        allowed = cls.__dataclass_fields__
        return cls(**{key: value for key, value in data.items() if key in allowed})


def load_mibig_records(mibig_dir: Path = MIBIG_DIR) -> list[MibigRecord]:
    records: list[MibigRecord] = []
    for path in sorted(mibig_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text())
            cluster = data.get("cluster") or {}
            accession = str(cluster.get("mibig_accession") or path.stem)
            organism = str(cluster.get("organism_name") or "").strip()
            if organism:
                records.append(MibigRecord(accession, organism, cluster))
        except (OSError, json.JSONDecodeError, AttributeError):
            continue
    return records


def is_probable_bacterium(name: str) -> bool:
    return classify_organism(name).is_bacterial


def organism_key(name: str) -> str:
    # One catalog row per exact organism/strain when available; duplicate MIBiG
    # clusters for the same organism are merged under this normalized key.
    return re.sub(r"\s+", " ", name.strip()).casefold()


def parse_name(name: str) -> tuple[str, str, str, str]:
    parts = name.split()
    genus = parts[0] if parts else "Unknown"
    species = parts[1] if len(parts) > 1 else "sp."
    strain = " ".join(parts[2:]) if len(parts) > 2 else ""
    display = f"{genus[0]}. {species}" if genus and species != "sp." else name
    if strain:
        display = f"{display} {strain}"
    return display, genus, species, strain


def _unique(values: list[str], limit: int | None = None) -> list[str]:
    out = []
    for value in values:
        value = str(value).strip()
        if value and value not in out:
            out.append(value)
        if limit and len(out) >= limit:
            break
    return out


def build_catalog(records: list[MibigRecord] | None = None) -> list[BacteriumCatalogEntry]:
    grouped: dict[str, list[MibigRecord]] = {}
    CATALOG_STATS["included_records"] = 0
    CATALOG_STATS["excluded_records"] = 0
    CATALOG_STATS["excluded_reasons"] = {}
    CATALOG_STATS["playable_entries"] = 0
    for record in records or load_mibig_records():
        decision = classify_organism(record.organism_name, record.cluster.get("ncbi_tax_id"))
        if decision.is_bacterial:
            CATALOG_STATS["included_records"] += 1
            grouped.setdefault(organism_key(record.organism_name), []).append(record)
        else:
            CATALOG_STATS["excluded_records"] += 1
            CATALOG_STATS["excluded_reasons"][decision.reason] = CATALOG_STATS["excluded_reasons"].get(decision.reason, 0) + 1

    catalog: list[BacteriumCatalogEntry] = []
    for key, group in grouped.items():
        full_name = group[0].organism_name
        display, genus, species, strain = parse_name(full_name)
        biosyn, products, moieties, acts, traits = [], [], [], [], []
        for record in group:
            cluster = record.cluster
            biosyn.extend(cluster.get("biosyn_class") or [])
            traits.extend(infer_traits(record.accession, cluster))
            for compound in cluster.get("compounds") or []:
                products.append(compound.get("compound", ""))
                moieties.extend(m.get("moiety", "") for m in compound.get("chem_moieties") or [])
                acts.extend(a.get("activity", "") for a in compound.get("chem_acts") or [])
        accessions = _unique([r.accession for r in group])
        entry = BacteriumCatalogEntry(
            catalog_id=key,
            full_name=full_name,
            display_name=display,
            genus=genus,
            species=species,
            strain=strain,
            accessions=accessions,
            biosyn_classes=_unique(biosyn),
            products=_unique(products),
            compound_classes=_unique(moieties),
            activities=_unique(acts),
            traits=_unique_traits(traits),
            record_count=len(group),
            taxonomy_group="Bacteria",
            taxonomy_evidence=classify_organism(full_name, group[0].cluster.get("ncbi_tax_id")).reason,
        )
        entry.curious_fact = curious_fact(entry)
        entry.description = describe_entry(entry)
        catalog.append(entry)
    sorted_catalog = sorted(catalog, key=lambda e: e.full_name.casefold())
    CATALOG_STATS["playable_entries"] = len(sorted_catalog)
    return sorted_catalog


def _unique_traits(traits: list[TraitEvidence]) -> list[TraitEvidence]:
    seen, out = set(), []
    for trait in traits:
        key = (trait.trait, trait.evidence_level, trait.accession, trait.field, trait.explanation)
        if key not in seen:
            seen.add(key); out.append(trait)
    return out


def describe_entry(entry: BacteriumCatalogEntry) -> str:
    bits = [f"MIBiG records associate this organism with {pluralize(len(entry.accessions), 'known MIBiG record')}."]
    if entry.products:
        bits.append(f"Known products include {', '.join(entry.products[:4])}.")
    if entry.biosyn_classes:
        bits.append(f"Cluster classes include {', '.join(entry.biosyn_classes[:4])}.")
    if entry.activities:
        bits.append(f"Reported activities include {', '.join(entry.activities[:4])}.")
    if entry.traits:
        bits.append(f"Gameplay traits assigned from database evidence: {entry.trait_summary()}.")
    else:
        bits.append("No direct evidence was available for environmental adaptation traits in these MIBiG fields.")
    return " ".join(bits)


def bgc_summary(entry: BacteriumCatalogEntry) -> str:
    return f"Biosynthetic gene clusters: {pluralize(len(entry.accessions), 'known MIBiG record')} ({pluralize(len(entry.accessions), 'BGC')})."


def curious_fact(entry: BacteriumCatalogEntry) -> str:
    if entry.products and entry.activities:
        return f"MIBiG associates this organism with production of {entry.products[0]}, reported as {entry.activities[0]}."
    if entry.products:
        return f"MIBiG associates this organism with production of {entry.products[0]}."
    return f"MIBiG currently links this organism to {pluralize(len(entry.accessions), 'biosynthetic gene-cluster record')}."


def catalog_stats() -> dict:
    return {
        "included_records": CATALOG_STATS["included_records"],
        "excluded_records": CATALOG_STATS["excluded_records"],
        "excluded_reasons": dict(CATALOG_STATS["excluded_reasons"]),
        "playable_entries": CATALOG_STATS["playable_entries"],
    }


@lru_cache(maxsize=1)
def get_catalog() -> tuple[BacteriumCatalogEntry, ...]:
    if not OFFLINE_CATALOG_PATH.exists():
        raise FileNotFoundError(
            f"Offline game catalog not found: {OFFLINE_CATALOG_PATH}. "
            f"Run `{BUILD_COMMAND}` before launching Microbial Mayhem."
        )
    entries, _metadata = load_catalog_database(OFFLINE_CATALOG_PATH)
    return tuple(BacteriumCatalogEntry.from_dict(entry) for entry in entries)


def search_catalog(query: str, catalog: list[BacteriumCatalogEntry] | tuple[BacteriumCatalogEntry, ...] | None = None) -> list[BacteriumCatalogEntry]:
    q = query.strip().casefold()
    items = list(catalog or get_catalog())
    if not q:
        return items
    return [e for e in items if q in e.full_name.casefold() or q in e.display_name.casefold() or q in e.strain.casefold() or q in e.genus.casefold()]


def sample_catalog(count: int = 10, seed: int | None = None, catalog: list[BacteriumCatalogEntry] | tuple[BacteriumCatalogEntry, ...] | None = None) -> list[BacteriumCatalogEntry]:
    items = list(catalog or get_catalog())
    rng = random.Random(seed)
    if len(items) <= count:
        return items.copy()
    return rng.sample(items, count)


def choose_opponent(player_id: str, seed: int | None = None, catalog: list[BacteriumCatalogEntry] | tuple[BacteriumCatalogEntry, ...] | None = None) -> BacteriumCatalogEntry:
    candidates = [e for e in list(catalog or get_catalog()) if e.catalog_id != player_id]
    if not candidates:
        raise ValueError("No opponent candidates available")
    return random.Random(seed).choice(candidates)
