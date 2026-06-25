"""Cautious trait inference from local MIBiG records."""
from __future__ import annotations

from dataclasses import dataclass

DIRECT = "Direct evidence"
INDIRECT = "Indirect evidence"
NO_EVIDENCE = "No evidence"

ADAPTATION_TRAITS = {
    "Cold": "Cryophile",
    "Hot": "Thermophile",
    "Salty": "Halophile",
    "Alkaline": "Alkaliphile",
    "Acidic": "Acidophile",
    "In the presence of antibiotics": "Drug resistant",
}

KEYWORDS = {
    "Cryophile": ("cold", "cryoprotect", "psychroph", "cryoph"),
    "Thermophile": ("heat", "thermo", "thermal", "hot"),
    "Halophile": ("salt", "salin", "haloph"),
    "Alkaliphile": ("alkali", "alkaline"),
    "Acidophile": ("acid", "acidoph"),
    "Drug resistant": ("resistan", "drug", "antibiotic resistance", "self-resistance"),
}
ANTIMICROBIAL_KEYWORDS = ("antibacterial", "antibiotic", "antimicrobial", "antifungal")
RESISTANCE_KEYWORDS = ("resistan", "self-resistance", "drug resistance", "antibiotic resistance", "immunity", "efflux")


@dataclass(frozen=True)
class TraitEvidence:
    trait: str
    evidence_level: str
    accession: str
    field: str
    explanation: str


def text_contains(text: str, needles: tuple[str, ...]) -> bool:
    haystack = text.lower()
    return any(needle in haystack for needle in needles)


def infer_traits(accession: str, cluster: dict) -> list[TraitEvidence]:
    """Infer only traits supported by explicit MIBiG fields.

    MIBiG is a biosynthetic-gene-cluster database, so most environmental
    adaptations are unknown. This function records evidence only when the words
    appear in organism names, biosynthetic classes, compound names, biological
    activities, targets, moieties, or optional gene annotations.
    """
    evidence: list[TraitEvidence] = []
    searchable_parts: list[tuple[str, str]] = []
    searchable_parts.append(("organism_name", str(cluster.get("organism_name", ""))))
    searchable_parts.append(("biosyn_class", " ".join(map(str, cluster.get("biosyn_class") or []))))
    for compound in cluster.get("compounds") or []:
        searchable_parts.append(("compound", str(compound.get("compound", ""))))
        searchable_parts.append(("chem_moieties", " ".join(str(m.get("moiety", "")) for m in compound.get("chem_moieties") or [])))
        searchable_parts.append(("chem_acts", " ".join(str(a.get("activity", "")) for a in compound.get("chem_acts") or [])))
        searchable_parts.append(("chem_targets", " ".join(str(t.get("target", "")) for t in compound.get("chem_targets") or [])))
    if cluster.get("genes"):
        searchable_parts.append(("genes", str(cluster.get("genes"))))

    for trait, keywords in KEYWORDS.items():
        for field, value in searchable_parts:
            if text_contains(value, keywords):
                level = DIRECT if field in {"organism_name", "genes"} else INDIRECT
                evidence.append(TraitEvidence(trait, level, accession, field, f"MIBiG field '{field}' contains wording consistent with {trait.lower()} evidence."))
                break

    antimicrobial_hits = []
    for compound in cluster.get("compounds") or []:
        name = str(compound.get("compound", "unknown product"))
        acts = ", ".join(str(a.get("activity", "")) for a in compound.get("chem_acts") or [])
        if text_contains(f"{name} {acts}", ANTIMICROBIAL_KEYWORDS):
            antimicrobial_hits.append(name)
    if antimicrobial_hits:
        evidence.append(TraitEvidence("Antimicrobial production", INDIRECT, accession, "compounds.chem_acts", f"Reported antimicrobial activity for {', '.join(sorted(set(antimicrobial_hits))[:3])}."))

    # Keep resistance separate from antimicrobial production.
    for field, value in searchable_parts:
        if text_contains(value, RESISTANCE_KEYWORDS):
            evidence.append(TraitEvidence("Drug resistant", DIRECT if field == "genes" else INDIRECT, accession, field, "Resistance-related wording appears in MIBiG annotation."))
            break
    return list({(e.trait, e.accession, e.field, e.explanation): e for e in evidence}.values())
