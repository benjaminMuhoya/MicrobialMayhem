"""Offline taxonomy filtering for playable bacterial MIBiG entries.

MIBiG JSON records in this repository expose `ncbi_tax_id` but not a complete
lineage table. To avoid network lookups during gameplay, this module uses a
curated local genus allow-list for bacterial genera commonly represented in the
bundled records and a deny-list for obvious non-bacterial genera observed in the
same data. Records outside the allow-list are excluded cautiously.
"""
from __future__ import annotations

from dataclasses import dataclass

BACTERIAL_GENERA = {
    "Acetobacter", "Acidithiobacillus", "Acinetobacter", "Actinoplanes", "Actinomadura", "Actinosynnema",
    "Aeromonas", "Amycolatopsis", "Anabaena", "Anaplasma", "Arthrobacter", "Aulosira", "Bacillus",
    "Bacteroides", "Bifidobacterium", "Bordetella", "Brevibacillus", "Burkholderia", "Calothrix",
    "Campylobacter", "Caulobacter", "Cellulomonas", "Chitinophaga", "Chromobacterium", "Clostridium",
    "Collimonas", "Corynebacterium", "Cupriavidus", "Curtobacterium", "Cyanobacterium", "Desulfovibrio",
    "Dickeya", "Dietzia", "Enterobacter", "Enterococcus", "Erwinia", "Escherichia", "Flavobacterium",
    "Frankia", "Gluconacetobacter", "Gordonia", "Hahella", "Herpetosiphon", "Janthinobacterium",
    "Kitasatospora", "Klebsiella", "Kocuria", "Komagataeibacter", "Lactobacillus", "Lactococcus",
    "Lechevalieria", "Leptolyngbya", "Leptospira", "Lysobacter", "Microbacterium", "Microcystis",
    "Micromonospora", "Micrococcus", "Moorea", "Mycobacterium", "Myxococcus", "Nocardia", "Nocardiopsis",
    "Nostoc", "Oceanobacillus", "Oscillatoria", "Paenibacillus", "Pantoea", "Paraburkholderia",
    "Photorhabdus", "Planobispora", "Planomonospora", "Plectonema", "Pseudoalteromonas", "Pseudomonas",
    "Rhodococcus", "Rhodopseudomonas", "Rivularia", "Saccharomonospora", "Saccharopolyspora", "Salinispora",
    "Serratia", "Shewanella", "Sinorhizobium", "Sorangium", "Staphylococcus", "Streptococcus", "Streptomyces",
    "Stigmatella", "Synechococcus", "Synechocystis", "Thermobifida", "Thermomonospora", "Verrucosispora",
    "Vibrio", "Xanthomonas", "Xenorhabdus", "Yersinia",
}

NON_BACTERIAL_GENERA = {
    "Acremonium", "Alternaria", "Arabidopsis", "Aspergillus", "Botrytis", "Candida", "Chaetomium",
    "Claviceps", "Cochliobolus", "Dendrothele", "Drosophila", "Epichloe", "Fusarium", "Homo", "Hypholoma",
    "Lentinula", "Magnaporthe", "Monascus", "Mus", "Neurospora", "Oryza", "Penicillium", "Pestalotiopsis",
    "Rattus", "Saccharomyces", "Sordaria", "Trichoderma", "Ustilago", "Zea",
}

@dataclass(frozen=True)
class TaxonomyDecision:
    is_bacterial: bool
    reason: str
    taxonomy_group: str


def classify_organism(name: str, ncbi_tax_id: str | int | None = None) -> TaxonomyDecision:
    genus = name.split()[0].strip("[]") if name.split() else ""
    if genus in BACTERIAL_GENERA:
        return TaxonomyDecision(True, "curated bacterial genus allow-list", "Bacteria")
    if genus in NON_BACTERIAL_GENERA:
        return TaxonomyDecision(False, "curated non-bacterial genus deny-list", "Non-bacterial")
    return TaxonomyDecision(False, "no offline lineage or curated bacterial-genus evidence", "Unclassified")
