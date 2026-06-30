from bacterial_names import format_bacterial_name, sanitize_designation


def test_bacdive_markup_and_authority_are_structured():
    name = format_bacterial_name(
        "<I>Escherichia</I> <I>coli</I> (Migula 1895) "
        "Castellani and Chalmers 1919 (Approved Lists 1980)"
    )
    assert name.scientific == "Escherichia coli"
    assert name.authority == "Castellani & Chalmers, 1919"
    assert name.approval == "Approved Lists 1980"
    assert "<" not in name.plain and ">" not in name.plain


def test_subspecies_is_kept_separate_from_genus_and_species():
    name = format_bacterial_name(
        "<I>Planomonospora</I> <I>parontospora</I> subsp. "
        "<I>parontospora</I> (Thiemann et al. 1967) Thiemann et al. 1968"
    )
    assert name.scientific == "Planomonospora parontospora"
    assert name.short_secondary == "subsp. parontospora"


def test_sanitizer_never_exposes_malformed_italic_tags():
    assert sanitize_designation("<I>Bacillus</I> <I>cereus</I>") == "Bacillus cereus"
