import re

import pytest

from lexikon.fassung import apply_fassung, load_mapping, section_signal
from lexikon.norms import NormRef


def bgb(n, af=False):
    return NormRef("BGB", "§", n, af)


def test_mapping_from_synopse():
    m = load_mapping()
    assert m["1896"] == ["1814", "1815"]
    assert m["1821"] == ["1850"]
    assert "1632" not in m          # gilt unverändert, kein Vorgänger im Reformbereich


@pytest.mark.parametrize("refs,text,dates,expected", [
    ([bgb("1896", True)], "", [], "alt"),                         # a.F.-Zitat im Abschnitt
    ([bgb("1906")], "", [], "alt"),                               # § 1906 gibt es nur noch alt
    ([NormRef("FGG", "§", "69")], "", [], "alt"),                 # FGG seit 2009 außer Kraft
    ([], "nach dem bis zum 31.12.2022 geltenden Recht", [], "alt"),
    ([], "", ["2015-03-01", "2019-01-01"], "alt"),                # nur Rechtsprechung vor der Reform
    ([NormRef("BtOG", "§", "12")], "", [], "neu"),
    ([], "Seit dem 1.1.2023 gilt", [], "neu"),
    ([], "", ["2024-05-01"], "neu"),
    ([bgb("1906")], "Seit dem 1.1.2023 gilt", [], None),          # widersprüchlich
    ([], "", ["2015-01-01", "2024-01-01"], "alt"),             # jede Entscheidung vor 2023 ist Altbezug
    ([], "kein Hinweis", [], None),
])
def test_section_signal(refs, text, dates, expected):
    assert section_signal(refs, text, dates) == expected


def test_apply_fassung():
    refs = [bgb("1821"), bgb("1906"), bgb("242"), NormRef("FamFG", "§", "26"), bgb("1814", True)]
    # Abschnittssignal „alt“ reicht nicht: überarbeitete Artikel nennen altes Recht oft nur zum Vergleich
    alt = [r.id for r in apply_fassung(refs, "alt")]
    assert alt == ["BGB§1821@unbestimmt", "BGB§1906@aF", "BGB§242", "FamFG§26", "BGB§1814@aF"]
    neu = [r.id for r in apply_fassung(refs, "neu")]
    assert neu == ["BGB§1821", "BGB§1906@aF", "BGB§242", "FamFG§26", "BGB§1814@aF"]
    offen = apply_fassung(refs, None)
    assert [r.id for r in offen] == ["BGB§1821@unbestimmt", "BGB§1906@aF", "BGB§242", "FamFG§26", "BGB§1814@aF"]
    assert offen[0].label == "§ 1821 BGB (alte oder neue Fassung)"


def test_fassung_property():
    assert bgb("1821", True).fassung == "alt"
    assert NormRef("BGB", "§", "1821", unbestimmt=True).fassung == "unbestimmt"
    assert apply_fassung([bgb("1821")], "neu")[0].fassung == "neu"
    assert bgb("242").fassung is None


# --- Stichprobe echte Daten: Vergleich alt/neu im selben Abschnitt -----------------------

@pytest.mark.parametrize("text,refs,expected", [
    ("Betreuungsvorsorge (§ 1896 Abs. 2 BGB jetzt § 1814 Abs. 3 BGB).",
     [bgb("1896"), bgb("1814")], ["BGB§1896@aF", "BGB§1814"]),
    ("§ 1896 Abs. 3 BGB; Rpfleger 2009, 290. Böhm: nach dem neuen § 1820 Abs. 4 BGB; FamRZ 2022",
     [bgb("1896"), bgb("1820")], ["BGB§1896@aF", "BGB§1820"]),
    # Nachfolger laut Synopse im selben Abschnitt wie die alte Norm → Vergleich, also neu
    ("Zu § 1896 BGB und § 1815 BGB", [bgb("1896"), bgb("1815")], ["BGB§1896@aF", "BGB§1815"]),
])
def test_local_markers_and_successors_in_old_section(text, refs, expected):
    signal = section_signal(refs, text, [])
    assert signal == "alt"
    assert [r.id for r in apply_fassung(refs, signal, text)] == expected


def test_local_old_marker_in_new_section():
    text = "Seit dem 1.1.2023 gilt § 1821 BGB; früher § 1823 BGB."
    refs = [bgb("1821"), bgb("1823")]
    assert [r.id for r in apply_fassung(refs, section_signal(refs, text, []), text)] == ["BGB§1821", "BGB§1823@aF"]


def test_unrelated_norm_in_old_section_is_unbestimmt():
    text = "Zu § 1896 BGB und § 1821 BGB"     # § 1821 ist kein Nachfolger von § 1896
    refs = [bgb("1896"), bgb("1821")]
    assert [r.id for r in apply_fassung(refs, "alt", text)] == ["BGB§1896@aF", "BGB§1821@unbestimmt"]


@pytest.mark.parametrize("text,refs,expected", [
    # Stichprobe echte Daten: neue Normen in Abschnitten mit alten Bezügen
    ("Bis zum 31.12.2022 galt § 1896 BGB. Ergänzungsbetreuer gemäß § 1817 Abs. 5 BGB",
     [bgb("1896"), bgb("1817")], ["BGB§1896@aF", "BGB§1817@unbestimmt"]),
    ("§ 1904 BGB a.F. ... stets die Genehmigung gem. § 1829 BGB", [bgb("1904", True), bgb("1829")],
     ["BGB§1904@aF", "BGB§1829"]),                      # Nachfolger (ergänzte Zuordnung)
    ("Früher § 1821 BGB", [bgb("1821")], ["BGB§1821@aF"]),  # Hinweis am Zitat
])
def test_review_sample_cases(text, refs, expected):
    assert [r.id for r in apply_fassung(refs, section_signal(refs, text, []), text)] == expected


def test_mapping_supplemented_rows():
    m = load_mapping()
    assert m["1904"] == ["1829"] and m["1899"] == ["1817"]


def test_nf_marker_with_mixed_section_signal():
    text = "§ 1814 BGB n.F. und § 1906 BGB"
    refs = [bgb("1814"), bgb("1906")]
    assert section_signal(refs, text, []) == "alt"         # bloßes „n.F.“ ist kein Abschnittssignal mehr
    assert [r.id for r in apply_fassung(refs, None, text)] == ["BGB§1814", "BGB§1906@aF"]


@pytest.mark.parametrize("nummer", ["1835a", "1836a", "1836d", "1836e"])
def test_letter_suffix_in_reform_range_is_old(nummer):
    """Im geltenden Recht gibt es in §§ 1773–1888 keine Buchstaben-Paragraphen (geprüft: 1835a, 1836d)."""
    assert apply_fassung([bgb(nummer)], None)[0].id == f"BGB§{nummer}@aF"


# --- Befunde aus dem Review vom 27.11.2026 (echte Beispiele) ------------------------------

def run(text, refs, dates=()):
    return [r.id for r in apply_fassung(refs, section_signal(refs, text, list(dates)), text)]


def test_chain_with_old_only_number_is_old():
    """Abschlussbericht 2003: § 1821 in einer Kette mit § 1908i ist § 1821 a.F., nicht Nachfolger."""
    text = ("Der Betreuer bedarf ferner der Genehmigung hinsichtlich der in §§ 1908i Abs. 1 Satz 1, "
            "1821, 1822 Nr. 1-4, 1823 BGB genannten Rechtsgeschäfte.")
    refs = [bgb("1908i"), bgb("1821"), bgb("1822"), bgb("1823")]
    assert run(text, refs) == ["BGB§1908i@aF", "BGB§1821@aF", "BGB§1822@aF", "BGB§1823@aF"]


def test_chain_rule_beats_successor_rule():
    text = "§§ 1908i Abs. 1 Satz 1, 1816 BGB und § 1896 BGB"     # 1816 ist Nachfolger von 1897, nicht hier
    refs = [bgb("1908i"), bgb("1816"), bgb("1896")]
    assert run(text, refs) == ["BGB§1908i@aF", "BGB§1816@aF", "BGB§1896@aF"]


def test_ff_without_dot_does_not_break_chain():
    text = "§§ 1942 ff BGB"
    from lexikon.norms import parse_norms
    assert [r.id for r in parse_norms(text)] == ["BGB§1942"]


def test_mixed_decision_dates_block_section_neu():
    """Erbausschlagung: Rechtsprechung 1997–2024 und „seit 1.1.2023“ → nicht pauschal neu."""
    text = "Seit dem 1.1.2023 gilt Neues. Nach dem Sinn und Zweck der §§ 1821, 1822 BGB"
    assert run(text, [bgb("1821"), bgb("1822")], ["1997-05-01", "2024-02-01"]) == [
        "BGB§1821@unbestimmt", "BGB§1822@unbestimmt"]


@pytest.mark.parametrize("text", [
    "Nach dem FamFG n.F. gilt § 1821 BGB",
    "Bork: Die Prozessfähigkeit nach neuem Recht; MDR 1991. § 1821 BGB",
    "§ 117 Abs. 2 SGB IX n.F. sowie § 1821 BGB",
])
def test_new_text_signal_only_for_2023_reform(text):
    assert run(text, [bgb("1821")]) == ["BGB§1821@unbestimmt"]


def test_new_text_signal_for_reform_wording():
    assert run("Nach dem neuen Betreuungsrecht gilt § 1821 BGB", [bgb("1821")]) == ["BGB§1821"]


@pytest.mark.parametrize("nummer", ["1858", "1862", "1863", "1868", "1871", "1877", "1880", "1881"])
def test_vacant_old_numbers_are_new(nummer):
    """§§ 1858–1881 waren im alten Recht weggefallen (Familienrat) → Zitat meint neues Recht."""
    assert run(f"§ {nummer} BGB", [bgb(nummer)]) == [f"BGB§{nummer}"]


def test_mapping_review_corrections():
    m = load_mapping()
    assert m["1835a"] == ["1878"]
    assert m["1836c"] == ["1880"] and m["1909"] == ["1809"] and m["1908a"] == ["1814"]
    assert "1820" not in m["1897"]
    assert all(re.fullmatch(r"\d+[a-z]?", n) for news in m.values() for n in news)


def test_fassung_property_only_up_to_1888():
    assert bgb("1906").fassung is None          # ohne apply_fassung keine Aussage „neu“
