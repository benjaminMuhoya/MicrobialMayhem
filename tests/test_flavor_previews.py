from bacterial_catalog import BacteriumCatalogEntry
from flavor_text import FlavorDeck, friendly_value, is_missing, result_message
from preview_models import COLONY_PRESETS, animation_time, colony_particles, environment_effect_text, environment_particles, quadratic_path
from trait_inference import DIRECT, TraitEvidence


def entry(name="Bacillus testis", traits=()):
    return BacteriumCatalogEntry(
        catalog_id=name.casefold(), full_name=name, display_name=name,
        genus=name.split()[0], species=name.split()[1], strain="", traits=list(traits),
    )


def test_missing_values_receive_short_scientifically_honest_fallbacks():
    deck = FlavorDeck("test")
    outputs = [friendly_value(value, context, deck=deck, key=str(index)) for index, (value, context) in enumerate([
        ("Unknown", "trait"), ("No data", "habitat"), ("", "activity"), (None, "general"),
    ])]
    assert all(output and len(output) <= 64 for output in outputs)
    assert len(set(outputs)) == len(outputs)
    assert all(not any(fake in output.casefold() for fake in ("thermophile", "halophile", "resistant")) for output in outputs)
    assert is_missing("No curated morphology information available.")


def test_result_messages_are_contextual_stable_and_not_repeated():
    deck = FlavorDeck("session")
    category, first = result_message(31, 30, "A", deck, "battle-1")
    _, same = result_message(31, 30, "A", deck, "battle-1")
    _, second = result_message(32, 31, "A", deck, "battle-2")
    assert category == "close" and first == same and second != first
    assert result_message(50, 20, "A", deck, "battle-3")[0] == "dominant"


def test_preview_models_are_stable_and_reduced_motion_can_freeze_phase():
    assert colony_particles(500, "fighter") == colony_particles(500, "fighter")
    assert environment_particles("Hot", "match") == environment_particles("Hot", "match")
    assert len(colony_particles(1000, "fighter")) > len(colony_particles(50, "fighter"))
    path = quadratic_path((0, 0), (10, 0), -4)
    assert path[0] == (0, 0) and path[-1] == (10, 0) and min(y for _, y in path) < 0
    assert animation_time(12.5, False) == 12.5
    assert animation_time(12.5, True) == 0
    assert [preset.cfu for preset in COLONY_PRESETS] == [50, 250, 500, 750, 1000]
    assert all(preset.title and preset.flavor for preset in COLONY_PRESETS)


def test_environment_modifier_copy_matches_real_scoring_rules():
    normal = entry("Bacillus normalis")
    hot = entry("Bacillus thermus", [TraitEvidence("Thermophile", DIRECT, "BGC", "genes", "evidence")])
    assert "+0 environment points to both" in environment_effect_text(normal, hot, "Neutral")
    text = environment_effect_text(hot, normal, "Hot")
    assert "your fighter +12" in text and "rival +0" in text
    assert "both receive -3" in environment_effect_text(normal, entry("Bacillus other"), "Cold")
