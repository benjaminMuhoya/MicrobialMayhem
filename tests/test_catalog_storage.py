import sqlite3

from catalog_storage import load_catalog_database, write_catalog_database


def fighter(catalog_id, strain, accessions=None, products=None):
    return {
        "catalog_id": catalog_id,
        "full_name": "<I>Bacillus</I> <I>storageus</I>",
        "display_name": "B. storageus",
        "genus": "Bacillus",
        "species": "storageus",
        "strain": strain,
        "source": "BacDive",
        "bacdive_id": catalog_id.split(":")[-1],
        "accessions": accessions or [],
        "products": products or [],
        "activities": ["antibacterial"] if products else [],
        "traits": [],
    }


def test_sqlite_round_trip_preserves_runtime_fields(tmp_path):
    path = tmp_path / "catalog.sqlite3"
    original = fighter("bacdive:1", "DSM 1", ["BGC1"], ["product one"])
    write_catalog_database(path, [original], {"source": "test"})
    loaded, metadata = load_catalog_database(path)
    assert loaded[0]["catalog_id"] == original["catalog_id"]
    assert loaded[0]["accessions"] == ["BGC1"]
    assert loaded[0]["products"] == ["product one"]
    assert metadata["playable_fighter_count"] == 1


def test_sqlite_normalizes_repeated_enrichment_profiles(tmp_path):
    path = tmp_path / "catalog.sqlite3"
    profile = {"accessions": ["BGC1", "BGC2"], "products": ["shared product"]}
    write_catalog_database(
        path,
        [fighter("bacdive:1", "DSM 1", **profile), fighter("bacdive:2", "DSM 2", **profile)],
    )
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM fighters").fetchone()[0] == 2
        assert connection.execute("SELECT COUNT(*) FROM enrichment_profiles").fetchone()[0] == 1


def test_sqlite_writer_removes_true_duplicate_identities(tmp_path):
    path = tmp_path / "catalog.sqlite3"
    sparse = fighter("bacdive:1", "no")
    complete = fighter("bacdive:2", "no", ["BGC1"], ["product one"])
    metadata = write_catalog_database(path, [sparse, complete])
    loaded, _ = load_catalog_database(path)
    assert metadata["duplicate_fighters_removed"] == 1
    assert [item["catalog_id"] for item in loaded] == ["bacdive:2"]
