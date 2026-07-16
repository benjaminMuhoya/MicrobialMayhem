#!/usr/bin/env python3
"""Validate checksums, required fields, identities, and compatibility metadata."""
from __future__ import annotations
import hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/"web"/"public"/"data"

def main():
    manifest=json.loads((DATA/"manifest.v2.json").read_text()); assert manifest["schemaVersion"]==2
    for item in manifest["files"]:
        body=(DATA/item["path"]).read_bytes(); assert len(body)==item["bytes"]; assert hashlib.sha256(body).hexdigest()==item["sha256"]
    fighters=json.loads((DATA/"fighters-core.v2.json").read_text())["fighters"]
    assert len(fighters)==manifest["fighterCount"] and len({f["catalogId"] for f in fighters})==len(fighters)
    required=("catalogId","fullName","searchKey","accessions","products","activities","traits","description","curiousFact","habitat","colonyAppearance","cellShape","motility","provenance")
    for fighter in fighters:
        assert all(field in fighter for field in required), fighter.get("catalogId")
        assert fighter["catalogId"] and fighter["fullName"] and fighter["provenance"]["contentVersion"]==manifest["contentVersion"]
    print(f"Validated schema v2 / content {manifest['contentVersion']} / {len(fighters)} fighters")

if __name__=="__main__": main()

