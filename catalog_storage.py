"""Normalized SQLite storage for the runtime bacterial fighter catalog."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from catalog_deduplication import deduplicate_fighters

SCHEMA_VERSION = 2
PROFILE_FIELDS = ("accessions", "products", "activities", "traits")
FIGHTER_FIELDS = (
    "catalog_id",
    "full_name",
    "display_name",
    "genus",
    "species",
    "strain",
    "description",
    "taxonomy_group",
    "colony_appearance",
    "curious_fact",
    "source",
    "bacdive_id",
    "isolation_habitat",
    "cell_shape",
    "motility",
)


def compact_json(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def write_catalog_database(path: Path, fighters: list[dict], metadata: dict | None = None) -> dict:
    """Write an atomic, deduplicated database with shared enrichment profiles."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    unique_fighters, duplicates_removed = deduplicate_fighters(fighters)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.unlink(missing_ok=True)

    connection = sqlite3.connect(temporary)
    try:
        connection.executescript(
            """
            PRAGMA journal_mode=OFF;
            PRAGMA synchronous=OFF;
            CREATE TABLE metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            ) WITHOUT ROWID;
            CREATE TABLE enrichment_profiles (
                profile_id INTEGER PRIMARY KEY,
                accessions TEXT NOT NULL,
                products TEXT NOT NULL,
                activities TEXT NOT NULL,
                traits TEXT NOT NULL,
                UNIQUE(accessions, products, activities, traits)
            );
            CREATE TABLE fighters (
                catalog_id TEXT PRIMARY KEY,
                profile_id INTEGER NOT NULL REFERENCES enrichment_profiles(profile_id),
                sort_order INTEGER NOT NULL,
                full_name TEXT NOT NULL,
                display_name TEXT NOT NULL,
                genus TEXT NOT NULL,
                species TEXT NOT NULL,
                strain TEXT NOT NULL,
                description TEXT NOT NULL,
                taxonomy_group TEXT NOT NULL,
                colony_appearance TEXT NOT NULL,
                curious_fact TEXT NOT NULL,
                source TEXT NOT NULL,
                bacdive_id TEXT NOT NULL,
                isolation_habitat TEXT NOT NULL,
                cell_shape TEXT NOT NULL,
                motility TEXT NOT NULL
            ) WITHOUT ROWID;
            CREATE INDEX fighters_name_idx ON fighters(full_name COLLATE NOCASE);
            CREATE INDEX fighters_genus_idx ON fighters(genus COLLATE NOCASE);
            """
        )
        profiles: dict[tuple[str, ...], int] = {}
        next_profile_id = 1
        fighter_rows = []
        for sort_order, fighter in enumerate(unique_fighters):
            profile = tuple(compact_json(fighter.get(field, [])) for field in PROFILE_FIELDS)
            profile_id = profiles.get(profile)
            if profile_id is None:
                profile_id = next_profile_id
                next_profile_id += 1
                profiles[profile] = profile_id
                connection.execute(
                    "INSERT INTO enrichment_profiles VALUES (?, ?, ?, ?, ?)",
                    (profile_id, *profile),
                )
            values = [str(fighter.get(field, "") or "") for field in FIGHTER_FIELDS]
            fighter_rows.append((values[0], profile_id, sort_order, *values[1:]))
        connection.executemany(
            "INSERT INTO fighters VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            fighter_rows,
        )
        db_metadata = dict(metadata or {})
        db_metadata.update(
            {
                "schema_version": SCHEMA_VERSION,
                "playable_fighter_count": len(unique_fighters),
                "duplicate_fighters_removed": int(db_metadata.get("duplicate_fighters_removed", 0)) + duplicates_removed,
                "enrichment_profile_count": len(profiles),
            }
        )
        connection.executemany(
            "INSERT INTO metadata VALUES (?, ?)",
            ((key, compact_json(value)) for key, value in sorted(db_metadata.items())),
        )
        connection.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
        connection.commit()
        connection.execute("VACUUM")
    finally:
        connection.close()
    temporary.replace(path)
    return db_metadata


def load_catalog_database(path: Path) -> tuple[list[dict], dict]:
    """Load runtime fields and reconstruct shared lists from normalized profiles."""
    connection = sqlite3.connect(f"file:{Path(path)}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        metadata = {row["key"]: json.loads(row["value"]) for row in connection.execute("SELECT key, value FROM metadata")}
        query = """
            SELECT f.*, p.accessions, p.products, p.activities, p.traits
            FROM fighters AS f
            JOIN enrichment_profiles AS p USING (profile_id)
            ORDER BY f.sort_order
        """
        available_columns = {row[1] for row in connection.execute("PRAGMA table_info(fighters)")}
        fighters = []
        for row in connection.execute(query):
            fighter = {field: row[field] if field in available_columns else "Unknown" for field in FIGHTER_FIELDS}
            for field in PROFILE_FIELDS:
                fighter[field] = json.loads(row[field])
            fighters.append(fighter)
        return fighters, metadata
    finally:
        connection.close()
