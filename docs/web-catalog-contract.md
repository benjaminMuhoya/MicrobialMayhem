# Web runtime catalog v2

The browser receives only `web/public/data/`: a 384-fighter core roster, a compact search index, and a version/checksum manifest. Raw BacDive, raw MIBiG, the legacy 260 MiB JSON, SQLite source data, and developer scripts are excluded from the deployed client.

Each fighter retains a stable ID, names/search key, strain, BGC accessions, products, activities, compact trait evidence, short description/fact, habitat, colony appearance, cell shape, motility, and provenance/content version.

`catalog_storage.py` schema v2 now persists `cell_shape` and `motility`. Its loader remains compatible with schema v1 databases by returning `Unknown` when those columns are absent. The existing v1 runtime database is not overwritten during the web transition.

Rebuild with `python3 scripts/build_web_catalog.py`. Validate with `python3 scripts/validate_web_catalog.py`. A release must publish the data files and manifest together. Clients compare `schemaVersion`, `contentVersion`, and `minimumClient`; saved games refer to `catalogId`, never array position.

The initial core roster is selected round-robin by genus, preferring records with known morphology, motility, habitat, and enrichment. The current output is about 465 KiB uncompressed, with 329/384 known cell shapes and 313/384 known motility records. Later full-roster shards should use the same contract and manifest without changing saved-game identity.

