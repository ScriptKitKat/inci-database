from pathlib import Path

from inci_pipeline.sources.obf_taxonomy import parse

SAMPLE = """\
# Header comment

en: water, aqua, h2o
fr: eau
de: Wasser
cas:en: 7732-18-5
ec:en: 231-791-2
wikidata:en: Q283

< en:water
en: deionized water, distilled water
fr: eau déionisée

en: Salicylic Acid, Acidum salicylicum, 2-hydroxybenzoic acid
fr: acide salicylique
cas:en: 69-72-7
ec:en: 200-712-3
wikidata:en: Q422
pubchem_compound_id:en: 338

en: Niacinamide, Nicotinamide
cas:en: 98-92-0
"""


def test_parses_three_entries(tmp_path: Path):
    p = tmp_path / "ingredients.txt"
    p.write_text(SAMPLE, encoding="utf-8")
    entries = list(parse(p))
    assert len(entries) == 4


def test_canonical_and_synonyms(tmp_path: Path):
    p = tmp_path / "ingredients.txt"
    p.write_text(SAMPLE, encoding="utf-8")
    by_name = {e.en_canonical: e for e in parse(p)}

    water = by_name["water"]
    assert "aqua" in water.en_synonyms
    assert "h2o" in water.en_synonyms
    assert water.other_lang_names["fr"] == ["eau"]
    assert water.cas_number == "7732-18-5"
    assert water.ec_number == "231-791-2"
    assert water.wikidata_id == "Q283"


def test_parents_recorded(tmp_path: Path):
    p = tmp_path / "ingredients.txt"
    p.write_text(SAMPLE, encoding="utf-8")
    by_name = {e.en_canonical: e for e in parse(p)}

    distilled = by_name["deionized water"]
    assert "water" in distilled.parents


def test_pubchem_property(tmp_path: Path):
    p = tmp_path / "ingredients.txt"
    p.write_text(SAMPLE, encoding="utf-8")
    by_name = {e.en_canonical: e for e in parse(p)}

    sa = by_name["Salicylic Acid"]
    assert sa.cas_number == "69-72-7"
    assert sa.pubchem_cid == "338"
    assert "Acidum salicylicum" in sa.en_synonyms


def test_handles_missing_optional_fields(tmp_path: Path):
    p = tmp_path / "ingredients.txt"
    p.write_text(SAMPLE, encoding="utf-8")
    by_name = {e.en_canonical: e for e in parse(p)}

    nm = by_name["Niacinamide"]
    assert nm.cas_number == "98-92-0"
    assert nm.ec_number is None
    assert nm.wikidata_id is None
    assert nm.pubchem_cid is None
    assert "Nicotinamide" in nm.en_synonyms
