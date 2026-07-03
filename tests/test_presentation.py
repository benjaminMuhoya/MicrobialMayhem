from bacterial_catalog import BacteriumCatalogEntry
from presentation import ability_for, environment_visual, fighter_visual, morphology_for, summary_ability, summary_arsenal_status


def entry(**updates):
    values = dict(
        catalog_id="bacillus-test", full_name="Bacillus testis", display_name="B. testis",
        genus="Bacillus", species="testis", strain="", cell_shape="Unknown",
    )
    values.update(updates)
    return BacteriumCatalogEntry(**values)


def test_recorded_morphology_drives_silhouette():
    assert morphology_for(entry(cell_shape="coccus")) == "coccus"
    assert morphology_for(entry(cell_shape="rod-shaped")) == "bacillus"
    assert morphology_for(entry(cell_shape="spiral")) == "spiral"
    assert morphology_for(entry(cell_shape="filamentous")) == "filamentous"


def test_unknown_morphology_has_stable_procedural_fallback():
    first = fighter_visual(entry())
    second = fighter_visual(entry())
    assert first == second
    assert first.morphology in {"coccus", "bacillus", "spiral", "filamentous", "irregular"}


def test_reported_non_motile_cell_does_not_receive_flagella():
    assert fighter_visual(entry(motility="non-motile")).has_flagella is False


def test_ability_prefers_named_product_then_bgc_fallback():
    assert ability_for(entry(products=["surfactin"], accessions=["BGC1"])) == "surfactin"
    assert ability_for(entry(accessions=["BGC1", "BGC2"])) == "BGC Arsenal ×2"
    assert any(word in ability_for(entry()).lower() for word in ("documented", "study", "unresolved"))
    assert summary_ability(entry(products=["Kitacinnamycin A"])) == "Kitacinnamycin A"
    long_name = "An exceptionally long documented biosynthetic product name"
    assert summary_ability(entry(products=[long_name])) == long_name
    assert summary_ability(entry(accessions=["BGC1"])) == "Still under investigation"
    assert summary_ability(entry()) == "Not yet documented"
    assert summary_arsenal_status(entry(), True) == "NONE DOCUMENTED"
    assert summary_arsenal_status(entry(accessions=["BGC1"]), True) == "ACTIVATED"
    assert summary_arsenal_status(entry(accessions=["BGC1"]), False) == "DORMANT"


def test_every_environment_has_a_safe_visual_profile():
    assert environment_visual("Hot").title == "Hot Spring"
    assert environment_visual("not-real").key == "Neutral"
