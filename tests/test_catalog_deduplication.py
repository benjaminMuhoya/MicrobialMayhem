from catalog_deduplication import deduplicate_fighters, fighter_identity_key


def fighter(bacdive_id, name, strain="no", **extra):
    return {
        "catalog_id": f"bacdive:{bacdive_id}",
        "bacdive_id": str(bacdive_id),
        "full_name": name,
        "strain": strain,
        "products": extra.get("products", []),
        "activities": extra.get("activities", []),
        "isolation_habitat": extra.get("isolation_habitat", "Unknown"),
    }


def test_duplicate_name_and_unspecified_strain_keeps_complete_representative():
    name = "<I>Streptomyces</I> Waksman and Henrici 1943 (Approved Lists 1980)"
    sparse = fighter(1, name)
    complete = fighter(2, name, products=["daunorubicin"], isolation_habitat="soil")
    kept, removed = deduplicate_fighters([sparse, complete])
    assert removed == 1
    assert kept == [complete]


def test_distinct_meaningful_strains_are_not_deduplicated():
    name = "<I>Streptomyces</I> Waksman and Henrici 1943 (Approved Lists 1980)"
    first = fighter(1, name, strain="Tü 365")
    second = fighter(2, name, strain="FD 23604")
    kept, removed = deduplicate_fighters([first, second])
    assert removed == 0
    assert kept == [first, second]
    assert fighter_identity_key(first) != fighter_identity_key(second)


def test_identity_normalization_ignores_markup_case_and_spacing():
    first = fighter(1, "<I>Escherichia</I> <I>coli</I>", strain="K-12")
    second = fighter(2, " escherichia   coli ", strain="k 12")
    assert fighter_identity_key(first) == fighter_identity_key(second)
