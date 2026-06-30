"""Safe, reusable formatting for bacterial designations from BacDive and MIBiG."""
from __future__ import annotations

import re
from dataclasses import dataclass

TAG_RE = re.compile(r"<\s*/?\s*i\s*>", re.IGNORECASE)
ANY_TAG_RE = re.compile(r"<[^>]*>")
ITALIC_VALUE_RE = re.compile(r"<\s*i\s*>(.*?)<\s*/\s*i\s*>", re.IGNORECASE)
APPROVAL_RE = re.compile(r"\s*\(?\s*Approved Lists?\s+\d{4}\s*\)?", re.IGNORECASE)
LEADING_AUTHORITY_RE = re.compile(r"^\s*\([^)]*\)\s*")
YEAR_RE = re.compile(r"\b(1[6-9]\d{2}|20\d{2})\b")


@dataclass(frozen=True)
class BacterialName:
    original: str
    plain: str
    genus: str
    species: str
    rank: str
    infraspecific: str
    designation: str
    authority: str
    approval: str

    @property
    def scientific(self) -> str:
        return " ".join(part for part in (self.genus, self.species) if part) or self.plain

    @property
    def short_secondary(self) -> str:
        if self.rank and self.infraspecific:
            return f"{self.rank} {self.infraspecific}"
        return self.authority or self.designation

    @property
    def expanded_details(self) -> str:
        return "; ".join(part for part in (self.designation, self.authority, self.approval) if part)


def sanitize_designation(value: str | None) -> str:
    """Remove markup and broken punctuation without exposing angle brackets."""
    text = TAG_RE.sub("", str(value or ""))
    text = ANY_TAG_RE.sub("", text)
    text = text.replace("<", "").replace(">", "")
    text = re.sub(r"\s+", " ", text).strip(" .;,<>")
    text = re.sub(r"\s+([,;)])", r"\1", text)
    text = re.sub(r"([(])\s+", r"\1", text)
    return text


def _short_authority(value: str) -> str:
    value = LEADING_AUTHORITY_RE.sub("", value).strip(" ,;.")
    value = re.sub(r"\bet\s+al\.?(?=\s|$)", "et al.", value, flags=re.IGNORECASE)
    value = re.sub(r"\s+and\s+", " & ", value)
    match = YEAR_RE.search(value)
    if match:
        before = value[:match.start()].rstrip(" ,")
        value = f"{before}, {match.group(1)}" if before else match.group(1)
    return value


def format_bacterial_name(value: str | None) -> BacterialName:
    """Return plain and structured name components for every UI context."""
    original = str(value or "")
    italic_values = [sanitize_designation(v) for v in ITALIC_VALUE_RE.findall(original)]
    plain = sanitize_designation(original)

    genus = italic_values[0] if italic_values else ""
    species = italic_values[1] if len(italic_values) > 1 else ""
    rank = ""
    infraspecific = ""
    rank_match = re.search(r"\b(subsp\.|ssp\.|var\.)\s+([A-Za-z][\w-]*)", plain, re.IGNORECASE)
    if rank_match:
        rank = "subsp." if rank_match.group(1).lower() in {"subsp.", "ssp."} else "var."
        infraspecific = rank_match.group(2)

    if not genus:
        words = plain.split()
        genus = words[0] if words else "Unknown"
        if len(words) > 1 and words[1].casefold() not in {"sp.", "subsp.", "ssp.", "var."}:
            species = words[1]

    biological = " ".join(part for part in (genus, species) if part)
    if rank and infraspecific:
        biological = f"{biological} {rank} {infraspecific}".strip()
    tail = plain[len(biological):].strip(" ,;.") if plain.casefold().startswith(biological.casefold()) else ""

    approvals = APPROVAL_RE.findall(tail)
    approval = sanitize_designation(approvals[0]).strip("() ") if approvals else ""
    tail_without_approval = APPROVAL_RE.sub("", tail).strip(" ,;.")

    authority = ""
    designation = ""
    if YEAR_RE.search(tail_without_approval) or " et al" in tail_without_approval.lower():
        authority = _short_authority(tail_without_approval)
    else:
        designation = tail_without_approval

    return BacterialName(
        original=original,
        plain=plain,
        genus=genus,
        species=species,
        rank=rank,
        infraspecific=infraspecific,
        designation=designation,
        authority=authority,
        approval=approval,
    )
