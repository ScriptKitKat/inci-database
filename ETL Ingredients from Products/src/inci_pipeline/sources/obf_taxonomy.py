"""Parse the Open Beauty Facts ingredients taxonomy.

Source file: `taxonomies/ingredients.txt` in the openbeautyfacts-server
GitHub repo. Format is the Open Food Facts taxonomy DSL:

  # comments
  < en:parent_canonical_name        # parent reference

  en: canonical name, synonym1, synonym2
  fr: nom canonique, synonyme
  cas:en: 12345-67-8
  ec:en: 234-567-8
  wikidata:en: Q12345

Entries are separated by blank lines. The first language line's first
comma-separated value is the canonical name. We treat English (`en:`)
as primary and use other-language canonicals as translation aliases.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

# property:lang: value   (lang may be missing)
_PROP_LANG = re.compile(r"^([a-z][a-z0-9_]+):([a-z]{2}):\s*(.+)$")
_PROP_BARE = re.compile(r"^([a-z][a-z0-9_]+):\s*(.+)$")
_LANG_LINE = re.compile(r"^([a-z]{2}):\s*(.+)$")


@dataclass
class OBFEntry:
    en_canonical: str = ""
    en_synonyms: list[str] = field(default_factory=list)
    other_lang_names: dict[str, list[str]] = field(default_factory=dict)
    cas_number: str | None = None
    ec_number: str | None = None
    wikidata_id: str | None = None
    pubchem_cid: str | None = None
    parents: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return bool(self.en_canonical)

    @property
    def all_aliases(self) -> list[str]:
        out: list[str] = list(self.en_synonyms)
        for names in self.other_lang_names.values():
            out.extend(names)
        return out


def parse(path: Path) -> Iterator[OBFEntry]:
    current: OBFEntry | None = None
    with path.open(encoding="utf-8") as fh:
        for raw_line in fh:
            line = raw_line.rstrip("\n").rstrip("\r")
            if not line.strip():
                if current and current.is_valid:
                    yield current
                current = None
                continue
            if line.lstrip().startswith("#"):
                continue
            if current is None:
                current = OBFEntry()
            if line.startswith("<"):
                # parent reference like "< en:hydroxy acids"
                m = _LANG_LINE.match(line[1:].strip())
                if m and m.group(1) == "en":
                    current.parents.append(m.group(2).strip())
                continue

            _absorb_line(current, line.strip())
    if current and current.is_valid:
        yield current


def _absorb_line(entry: OBFEntry, line: str) -> None:
    m = _PROP_LANG.match(line)
    if m:
        prop, lang, value = m.group(1), m.group(2), m.group(3).strip()
        _absorb_property(entry, prop, lang, value)
        return
    m = _LANG_LINE.match(line)
    if m:
        lang, value = m.group(1), m.group(2).strip()
        names = [n.strip() for n in value.split(",") if n.strip()]
        if not names:
            return
        if lang == "en":
            if not entry.en_canonical:
                entry.en_canonical = names[0]
                entry.en_synonyms.extend(names[1:])
            else:
                entry.en_synonyms.extend(names)
        else:
            entry.other_lang_names.setdefault(lang, []).extend(names)
        return
    m = _PROP_BARE.match(line)
    if m:
        prop, value = m.group(1), m.group(2).strip()
        _absorb_property(entry, prop, "", value)


def _absorb_property(entry: OBFEntry, prop: str, lang: str, value: str) -> None:
    if prop == "cas" and entry.cas_number is None:
        entry.cas_number = value
    elif prop == "ec" and entry.ec_number is None:
        entry.ec_number = value
    elif prop == "wikidata" and entry.wikidata_id is None:
        entry.wikidata_id = value
    elif prop in {"pubchem_compound_id", "pubchem_compound"} and entry.pubchem_cid is None:
        entry.pubchem_cid = value
