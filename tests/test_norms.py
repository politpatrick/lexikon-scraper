import mwparserfromhell
import pytest

from lexikon.norms import NormRef, canonical_law, norms_from_templates, parse_norms


def ids(text):
    return [n.id for n in parse_norms(text)]


@pytest.mark.parametrize("text,expected", [
    ("§§ 99, 104 FamFG", ["FamFG§99", "FamFG§104"]),
    ("§ 272 Abs. 2 FamFG", ["FamFG§272"]),
    ("Art. 24 EGBGB", ["EGBGBArt.24"]),
    ("§ 15, § 19 RPflG", ["RPflG§15", "RPflG§19"]),
    ("§§ 1814 ff. BGB", ["BGB§1814"]),
    ("§ 1896 BGB a.F.", ["BGB§1896"]),
    ("§ 42 Abs. 1 Nr. 2 SGB XII i.V.m. § 27a SGB XII", ["SGBXII§42", "SGBXII§27a"]),
    ("vgl. § 30 Abs. 3 SGB-I", ["SGBI§30"]),
    ("(§ 108  Abs. 2 BGB).", ["BGB§108"]),
    ("§ 7 Abs. 1 Satz 2 VBVG", ["VBVG§7"]),
    ("§ 1906a BGB", ["BGB§1906a"]),
    ("nach § 1833 BGB erforderliche", ["BGB§1833"]),
    ("§ 15 RpflG", ["RPflG§15"]),
])
def test_parse_norms(text, expected):
    assert ids(text) == expected


@pytest.mark.parametrize("text", [
    "Münchener Kommentar, BGB, § 1896 Rn. 76",   # Gesetz steht davor
    "§ 12 des Entwurfs",                          # kein Gesetz
    "§ 5 BGB-E",                                  # Entwurf, kein geltendes Gesetz
])
def test_no_false_positives(text):
    assert ids(text) == []


def test_alte_fassung_marked():
    assert parse_norms("§ 1896 BGB a.F.")[0].alte_fassung is True
    assert parse_norms("§ 1896 BGB a. F.")[0].alte_fassung is True
    assert parse_norms("§ 1814 BGB")[0].alte_fassung is False


def test_label():
    assert NormRef("SGB XII", "§", "42").label == "§ 42 SGB XII"
    assert NormRef("EGBGB", "Art.", "24").label == "Art. 24 EGBGB"


@pytest.mark.parametrize("slug,law", [
    ("bgb", "BGB"), ("BGB", "BGB"), ("sgb_1", "SGB I"), ("sgb_12", "SGB XII"),
    ("SGB_XI", "SGB XI"), ("vbvg_2023", "VBVG"), ("ao_1977", "AO"), ("bgbeg", "EGBGB"),
    ("btog", "BtOG"), ("famfg", "FamFG"), ("persstg", "PStG"), ("LFGG", "LFGG"),
])
def test_canonical_law_from_url_slug(slug, law):
    assert canonical_law(slug) == law


def test_norms_from_templates():
    code = mwparserfromhell.parse(
        "{{Zitat de §|37|lfgg}} {{Zitat-dej|§§|433|BGB}} {{Zitat Art|14|gg}} {{Zitat de §|30|sgb_1}} {{Rspr|X}}")
    assert [n.id for n in norms_from_templates(code)] == ["LFGG§37", "BGB§433", "GGArt.14", "SGBI§30"]
