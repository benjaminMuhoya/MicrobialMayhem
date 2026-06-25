"""Build and query a bacterial fighter catalog from local MIBiG JSON records."""
from __future__ import annotations

import json
import random
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from trait_inference import TraitEvidence, infer_traits

REPO_ROOT = Path(__file__).resolve().parent
MIBIG_DIR = REPO_ROOT / "mibig_json"

# MIBiG records do not include lineage. These exclusions prevent common fungal,
# plant, and animal records from being presented as bacterial fighters. The
# design keeps this list isolated so it can be replaced by a curated taxonomy
# table later.
NON_BACTERIAL_GENERA = {
    "Alternaria", "Aspergillus", "Penicillium", "Fusarium", "Acremonium", "Dendrothele",
    "Lentinula", "Saccharomyces", "Candida", "Trichoderma", "Claviceps", "Epichloe",
    "Arabidopsis", "Oryza", "Zea", "Homo", "Mus", "Rattus", "Drosophila", "Ciona",
}


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

    def has_trait(self, trait: str) -> bool:
        return any(e.trait == trait for e in self.traits)

    def trait_summary(self) -> str:
        names = []
        for evidence in self.traits:
            if evidence.trait not in names:
                names.append(evidence.trait)
        return ", ".join(names[:4]) if names else "traits unknown"


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
    genus = name.split()[0] if name.split() else ""
    return bool(genus) and genus not in NON_BACTERIAL_GENERA


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
    for record in records or load_mibig_records():
        if is_probable_bacterium(record.organism_name):
            grouped.setdefault(organism_key(record.organism_name), []).append(record)

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
        )
        entry.description = describe_entry(entry)
        catalog.append(entry)
    return sorted(catalog, key=lambda e: e.full_name.casefold())


def _unique_traits(traits: list[TraitEvidence]) -> list[TraitEvidence]:
    seen, out = set(), []
    for trait in traits:
        key = (trait.trait, trait.evidence_level, trait.accession, trait.field, trait.explanation)
        if key not in seen:
            seen.add(key); out.append(trait)
    return out


def describe_entry(entry: BacteriumCatalogEntry) -> str:
    bits = [f"MIBiG records associate this organism with {len(entry.accessions)} biosynthetic gene-cluster record(s)."]
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


@lru_cache(maxsize=1)
def get_catalog() -> tuple[BacteriumCatalogEntry, ...]:
    return tuple(build_catalog())


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
