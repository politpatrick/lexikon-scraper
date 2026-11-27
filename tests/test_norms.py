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
    ("§ 1896 BGB a.F.", ["BGB§1896@aF"]),
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


# --- Befunde aus dem Review vom 24.11.2026 -------------------------------------------

def test_alte_fassung_is_part_of_id():
    old, new = parse_norms("§ 1822 BGB a.F. und § 1822 BGB")
    assert (old.id, old.label) == ("BGB§1822@aF", "§ 1822 BGB a.F.")
    assert (new.id, new.label) == ("BGB§1822", "§ 1822 BGB")


@pytest.mark.parametrize("text", [
    "§ 5 Abs. 3 Satz 2 Nr. 1 VBVG aF",
    "§ 1896 BGB a. F.",
    "§ 1896 BGB in der bis zum 31.12.2022 geltenden Fassung",
])
def test_alte_fassung_variants(text):
    assert parse_norms(text)[0].alte_fassung is True


def test_vbvg_slug_is_old_version_vbvg_2023_current():
    code = mwparserfromhell.parse("{{Zitat de §|8|vbvg}} {{Zitat de §|8|vbvg_2023}}")
    assert [n.id for n in norms_from_templates(code)] == ["VBVG§8@aF", "VBVG§8"]


def test_typo_slug_btgb():
    assert canonical_law("btgb") == "BtBG"


@pytest.mark.parametrize("text,expected", [
    ("§§ 1915 Abs. 1, 1835 Abs. 4 BGB", ["BGB§1915", "BGB§1835"]),
    ("§§ 108 Abs. 1 und 1903 Satz 2 BGB", ["BGB§108", "BGB§1903"]),
    ("§§ 10 Abs. 2, 11 FamFG", ["FamFG§10", "FamFG§11"]),
    ("§§ 70 Abs. 3 Nr. 1, 271 Nr. 1 FamFG", ["FamFG§70", "FamFG§271"]),
    ("§ 272 Abs. 2, 3 FamFG", ["FamFG§272"]),
    ("Art. 229 § 54 Abs. 3 EGBGB", ["EGBGBArt.229§54"]),
    ("§§ 51 Abs. 1, 53 ZPO", ["ZPO§51", "ZPO§53"]),
    ("§ 5 III VBVG", ["VBVG§5"]),
    ("§§ 70 III Satz 1 Nr. 1, 271 Nr. 1 FamFG", ["FamFG§70", "FamFG§271"]),
])
def test_review_chains(text, expected):
    assert ids(text) == expected


def test_compound_label():
    assert parse_norms("Art. 229 § 54 EGBGB")[0].label == "Art. 229 § 54 EGBGB"


@pytest.mark.parametrize("text", ["§§ 1 " * 30, "§§ 1814 ff., " * 30, "§ 1, " * 3000])
def test_no_catastrophic_backtracking(text):
    import time
    start = time.perf_counter()
    parse_norms(text)
    assert time.perf_counter() - start < 1.0


@pytest.mark.parametrize("text,expected", [
    # Stichprobe echte Daten: Kette darf nicht über einen Absatzwechsel laufen
    ("§§ 68b, 69d\n\nAbs. 2 und 3 FGG", []),
    # „Abs. 2 und 3“: fortlaufende Zahl gehört zur Untergliederung, nicht neuer Paragraph
    ("§§ 68b Abs. 2 und 3 FGG", ["FGG§68b"]),
    ("§§ 68 Abs. 1 Satz 1 und Abs. 3 FGG", ["FGG§68"]),
    ("§§ 212 Abs. 1, 13 Abs.1, 25 Abs. 1 Alt. 2 StGB", ["StGB§212", "StGB§13", "StGB§25"]),
    ("§§ 1908i Abs. 1 Satz 1, 1821 Abs. 1 Nr. 1 und Nr. 2 BGB", ["BGB§1908i", "BGB§1821"]),
    ("§ 1814\nBGB", ["BGB§1814"]),
])
def test_sample_findings(text, expected):
    assert ids(text) == expected


@pytest.mark.parametrize("text", [
    "§§ 1908i Abs. 1 Satz 1, 1822 Nr. 2 BGB (in der bis zum 31.12.2022 geltenden Fassung)",
    "§ 1836 I BGB (a.F.",
])
def test_parenthesised_old_version_marker(text):
    assert all(r.alte_fassung for r in parse_norms(text))
