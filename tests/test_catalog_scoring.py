import random

from bacterial_catalog import BacteriumCatalogEntry, MibigRecord, build_catalog, choose_opponent, sample_catalog, search_catalog
from scoring import MATCHED, UNKNOWN, RANDOM_VARIATION_RANGE, score_battle
from trait_inference import TraitEvidence, DIRECT, INDIRECT


def entry(name, traits=(), products=(), activities=(), strain=""):
    return BacteriumCatalogEntry(
        catalog_id=name.casefold(), full_name=name, display_name=name, genus=name.split()[0], species=name.split()[1] if len(name.split()) > 1 else "sp.", strain=strain,
        accessions=["BGCX"], products=list(products), activities=list(activities), traits=list(traits), record_count=1,
    )


def trait(name):
    return TraitEvidence(name, DIRECT, "BGCX", "genes", f"{name} evidence")


def env_component(breakdown):
    return next(c for c in breakdown.components if c.name == "Environment")


def variation_component(breakdown):
    return next(c for c in breakdown.components if c.name == "Battle variation")


def test_cryophile_vs_non_cryophile_in_cold():
    cryo = entry("Cold bug", [trait("Cryophile")])
    unk = entry("Mystery bug")
    p, o = score_battle(cryo, unk, "Cold", 5, 5, True, True, seed=1)
    assert p.environment_status == MATCHED
    assert env_component(p).value > env_component(o).value


def test_thermophile_vs_cryophile_in_hot():
    thermo = entry("Hot bug", [trait("Thermophile")])
    cryo = entry("Cold bug", [trait("Cryophile")])
    p, o = score_battle(thermo, cryo, "Hot", 5, 5, True, True, seed=2)
    assert p.environment_status == MATCHED
    assert o.environment_status != MATCHED
    assert env_component(p).value == 12
    assert env_component(o).value == 0


def test_drug_resistant_vs_non_resistant_in_antibiotics():
    resistant = entry("Resistant bug", [trait("Drug resistant")])
    other = entry("Other bug")
    p, o = score_battle(resistant, other, "In the presence of antibiotics", 5, 5, True, True, seed=3)
    assert p.environment_status == MATCHED
    assert env_component(p).value == 12
    assert env_component(o).value == 0


def test_halophile_vs_unsupported_in_salty():
    halo = entry("Salt bug", [trait("Halophile")])
    unknown = entry("Unknown bug")
    p, o = score_battle(halo, unknown, "Salty", 5, 5, True, True, seed=4)
    assert p.environment_status == MATCHED
    assert o.environment_status == UNKNOWN
    assert env_component(p).value == 12


def test_both_fighters_matched_to_same_environment():
    a = entry("Salt one", [trait("Halophile")])
    b = entry("Salt two", [trait("Halophile")])
    p, o = score_battle(a, b, "Salty", 5, 5, True, True, seed=5)
    assert env_component(p).value == env_component(o).value == 12


def test_neither_fighter_matched_gets_shared_modest_penalty():
    a = entry("A bug")
    b = entry("B bug")
    p, o = score_battle(a, b, "Cold", 5, 5, True, True, seed=6)
    assert p.environment_status == o.environment_status == UNKNOWN
    assert env_component(p).value == env_component(o).value == -3


def test_unknown_is_not_treated_as_negative_when_other_matches():
    a = entry("A bug")
    b = entry("Cold bug", [trait("Cryophile")])
    p, o = score_battle(a, b, "Cold", 5, 5, True, True, seed=7)
    assert p.environment_status == UNKNOWN
    assert env_component(p).value == 0
    assert env_component(o).value == 12


def test_antibiotic_production_is_not_resistance():
    producer = entry("Producer bug", [TraitEvidence("Antimicrobial production", INDIRECT, "BGCX", "chem_acts", "antibacterial")], products=["antibiotic X"], activities=["antibacterial"])
    other = entry("Other bug")
    p, _ = score_battle(producer, other, "In the presence of antibiotics", 5, 5, True, True, seed=8)
    assert producer.has_trait("Antimicrobial production")
    assert not producer.has_trait("Drug resistant")
    assert p.environment_status == UNKNOWN
    assert next(c for c in p.components if c.name == "Defense").value == 0


def test_duplicate_records_map_to_one_catalog_entry():
    cluster = {"mibig_accession": "BGC1", "organism_name": "Bacillus testis A", "biosyn_class": ["NRP"], "compounds": [{"compound": "x"}]}
    records = [MibigRecord("BGC1", "Bacillus testis A", cluster), MibigRecord("BGC2", "Bacillus testis A", {**cluster, "mibig_accession": "BGC2"})]
    cat = build_catalog(records)
    assert len(cat) == 1
    assert sorted(cat[0].accessions) == ["BGC1", "BGC2"]


def test_search_full_genus_partial_and_strain():
    cat = [entry("Bacillus subtilis 168", strain="168"), entry("Pseudomonas fluorescens Pf0-1", strain="Pf0-1")]
    assert search_catalog("Bacillus subtilis", cat)[0].full_name.startswith("Bacillus")
    assert search_catalog("Pseudomonas", cat)[0].genus == "Pseudomonas"
    assert search_catalog("fluor", cat)[0].genus == "Pseudomonas"
    assert search_catalog("Pf0", cat)[0].strain == "Pf0-1"


def test_random_sampling_at_most_10_unique():
    cat = [entry(f"Bacillus testis {i}") for i in range(20)]
    sample = sample_catalog(10, seed=10, catalog=cat)
    assert len(sample) == 10
    assert len({e.catalog_id for e in sample}) == 10


def test_selected_player_excluded_from_opponent_selection():
    cat = [entry("A bug"), entry("B bug")]
    opponent = choose_opponent(cat[0].catalog_id, seed=1, catalog=cat)
    assert opponent.catalog_id != cat[0].catalog_id


def test_score_deterministic_with_seed():
    a = entry("A bug", [trait("Cryophile")])
    b = entry("B bug")
    assert score_battle(a, b, "Cold", 5, 5, True, False, seed=42) == score_battle(a, b, "Cold", 5, 5, True, False, seed=42)


def test_random_variation_within_small_range():
    a = entry("A bug")
    b = entry("B bug")
    p, o = score_battle(a, b, "Cold", 5, 5, True, True, seed=11)
    assert abs(variation_component(p).value) <= RANDOM_VARIATION_RANGE
    assert abs(variation_component(o).value) <= RANDOM_VARIATION_RANGE


def test_missing_optional_mibig_fields_do_not_crash_catalog():
    cat = build_catalog([MibigRecord("BGCX", "Bacillus minimalis", {"organism_name": "Bacillus minimalis"})])
    assert len(cat) == 1
    assert cat[0].full_name == "Bacillus minimalis"

from bacterial_catalog import bgc_summary, catalog_stats
from colony_scoring import colony_growth_score, colony_score_from_cfu, generate_opponent_cfu
from environment_icons import ENVIRONMENT_ICONS
from gui_helpers import pluralize, wrap_text
from taxonomy_filter import classify_organism


def test_only_curated_bacterial_organisms_enter_playable_catalog():
    bacterial = MibigRecord("B1", "Bacillus subtilis 168", {"organism_name": "Bacillus subtilis 168", "compounds": []})
    unknown = MibigRecord("U1", "Mystery eukaryote", {"organism_name": "Mystery eukaryote", "compounds": []})
    cat = build_catalog([bacterial, unknown])
    assert [e.full_name for e in cat] == ["Bacillus subtilis 168"]
    assert cat[0].taxonomy_group == "Bacteria"


def test_obvious_fungal_examples_are_excluded():
    for name in ["Hypholoma sublateritium", "Ustilago maydis", "Chaetomium olivaceum"]:
        assert not classify_organism(name).is_bacterial


def test_bgc_singular_plural_labels_are_correct():
    one = entry("Bacillus one")
    one.accessions = ["BGC1"]
    two = entry("Bacillus two")
    two.accessions = ["BGC1", "BGC2"]
    assert "1 BGC" in bgc_summary(one)
    assert "1 known MIBiG record" in bgc_summary(one)
    assert "2 BGCs" in bgc_summary(two)
    assert "2 known MIBiG records" in bgc_summary(two)
    assert pluralize(1, "MIBiG record") == "1 MIBiG record"
    assert pluralize(4, "MIBiG record") == "4 MIBiG records"


def test_colony_scores_differ_at_requested_values():
    values = [colony_score_from_cfu(cfu) for cfu in [50, 250, 500, 750, 1000]]
    assert len(set(values)) == 5


def test_colony_score_increases_monotonically_and_within_range():
    scores = [colony_score_from_cfu(cfu) for cfu in range(0, 1001, 50)]
    assert scores == sorted(scores)
    assert min(scores) >= 0
    assert max(scores) <= 10


def test_player_and_opponent_use_same_colony_formula():
    a = entry("A bug")
    b = entry("B bug")
    p, o = score_battle(a, b, "Cold", 250, 250, True, True, seed=20)
    pc = next(c for c in p.components if c.name == "Colony")
    oc = next(c for c in o.components if c.name == "Colony")
    assert pc.value == oc.value == colony_score_from_cfu(250)


def test_opponent_cfu_is_generated_and_stored_in_breakdown():
    cfu = generate_opponent_cfu(seed=12)
    assert 0 <= cfu <= 1000
    a = entry("A bug")
    b = entry("B bug")
    _, o = score_battle(a, b, "Cold", 100, cfu, True, True, seed=12)
    assert o.colony_cfu == cfu


def test_results_breakdown_components_add_to_total_with_colony_value():
    a = entry("A bug")
    b = entry("B bug")
    p, o = score_battle(a, b, "Cold", 500, 750, True, False, seed=13)
    assert round(p.component_total(), 2) == p.total
    assert round(o.component_total(), 2) == o.total
    assert p.colony_cfu == 500
    assert o.colony_cfu == 750


def test_unknown_colony_morphology_has_safe_fallback():
    cat = build_catalog([MibigRecord("BGCX", "Bacillus minimalis", {"organism_name": "Bacillus minimalis", "compounds": []})])
    assert cat[0].colony_appearance == "No curated morphology information available."


def test_environment_icons_and_labels_map_correctly():
    assert set(ENVIRONMENT_ICONS) == {"Salty", "Alkaline", "Hot", "Cold", "Acidic", "In the presence of antibiotics"}
    assert all(ENVIRONMENT_ICONS.values())


def test_long_text_wrapping_stays_within_assigned_width():
    text = "This is a deliberately long organism description that should wrap into several readable lines."
    lines = wrap_text(text, 20, len)
    assert len(lines) > 1
    assert all(len(line) <= 20 for line in lines)


def test_colony_labels_are_dynamic():
    labels = [colony_growth_score(cfu)[1] for cfu in [0, 50, 250, 500, 750, 1000]]
    assert labels == ["Very small colony", "Small colony", "Moderate colony", "Large colony", "Very large colony", "Massive colony"]
