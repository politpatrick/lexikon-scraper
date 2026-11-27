import mwparserfromhell
import pytest

from lexikon.decisions import DecisionRef, decisions_from_templates, merge_decisions, parse_decisions


def one(text):
    refs = parse_decisions(text)
    assert len(refs) == 1, refs
    return refs[0]


@pytest.mark.parametrize("text,gericht,art,datum,az", [
    # Akzeptanzkriterien Ticket 06
    ("LG Augsburg, Beschluss vom 30. Januar 2018 – 054 T 161/18", "LG Augsburg", "Beschluss", "2018-01-30", "054 T 161/18"),
    ("BGH XII ZB 123/20", "BGH", None, None, "XII ZB 123/20"),
    # Stichprobe echte Daten
    ("BGH, Urteil vom 23. Februar 1979, Az. V ZR 171/77", "BGH", "Urteil", "1979-02-23", "V ZR 171/77"),
    ("BGH, Beschluss vom 05.01.2011 - XII ZB 152/10", "BGH", "Beschluss", "2011-01-05", "XII ZB 152/10"),
    ("AG Dresden, Beschluss vom 10.03.2022, 404 XVII 2174/21", "AG Dresden", "Beschluss", "2022-03-10", "404 XVII 2174/21"),
    ("BSG, Urteil vom 17.06.2021, B 3 P 5/19", "BSG", "Urteil", "2021-06-17", "B 3 P 5/19"),
    ("OLG Celle, Beschl vom 27.5.2015, 6 W 75/16", "OLG Celle", "Beschluss", "2015-05-27", "6 W 75/16"),
    ("OLG München, Beschl. vom 17.7.2015,  34 Wx 179/15", "OLG München", "Beschluss", "2015-07-17", "34 Wx 179/15"),
    ("BSG vom 25.08.2011 – B 8 SO 29/10", "BSG", None, "2011-08-25", "B 8 SO 29/10"),
    ("LG Mühlhausen vom 28.06.2011, Az.: 1 T 5/11", "LG Mühlhausen", None, "2011-06-28", "1 T 5/11"),
    ("OLG Frankfurt/Main, Beschluss vom 08.06.2006, 20 W 52/06", "OLG Frankfurt/Main", "Beschluss", "2006-06-08", "20 W 52/06"),
    ("Kammergericht Berlin, Beschluss vom 21.08.1994, 1 W 1905/93", "KG", "Beschluss", "1994-08-21", "1 W 1905/93"),
    ("BVerfG vom 19.09.2006, 2 BvR 2115/01", "BVerfG", None, "2006-09-19", "2 BvR 2115/01"),
    ("LG München I, Beschluss vom 1.2.03, 13 T 1/03", "LG München I", "Beschluss", "2003-02-01", "13 T 1/03"),
])
def test_parse_decisions(text, gericht, art, datum, az):
    r = one(text)
    assert (r.gericht, r.art, r.datum, r.az) == (gericht, art, datum, az)


def test_federal_az_is_unique_without_court():
    assert one("BGH, Beschluss vom 05.01.2011 - XII ZB 152/10").id == "XII ZB 152/10"
    assert one("BVerfG vom 19.09.2006, 2 BvR 2115/01").id == "2 BvR 2115/01"
    assert one("BSG vom 25.08.2011 – B 8 SO 29/10").id == "B 8 SO 29/10"


def test_local_az_needs_court():
    assert one("LG Mühlhausen vom 28.06.2011, Az.: 1 T 5/11").id == "LG Mühlhausen 1 T 5/11"


def test_label():
    assert one("LG Augsburg, Beschluss vom 30. Januar 2018 – 054 T 161/18").label == \
        "LG Augsburg, Beschluss vom 30.01.2018 – 054 T 161/18"
    assert DecisionRef(az="XII ZB 1/20").label == "XII ZB 1/20"
    assert DecisionRef(fundstelle="BVerfGE 31, 58", gericht="BVerfG").label == "BVerfG, BVerfGE 31, 58"


@pytest.mark.parametrize("text", ["§ 1814 BGB", "BayObLG BtPrax 2002, 36/37", "Der BGH hat entschieden.",
                                  "FamRZ 1999, 1300"])
def test_no_false_positives(text):
    assert parse_decisions(text) == []


def test_templates_az_and_fundstelle():
    code = mwparserfromhell.parse("{{Rspr|XII ZB 236/05}} {{rspr|BVerfGE 31, 58}} {{Rspr|19 T 529/02}}")
    refs = decisions_from_templates(code)
    assert [(r.id, r.gericht) for r in refs] == [
        ("XII ZB 236/05", "BGH"), ("BVerfGE 31, 58", "BVerfG"), ("19 T 529/02", None)]


def test_merge_prefers_court_aware_refs():
    text_refs = parse_decisions("LG Frankfurt/Oder, Beschluss vom 1.2.2003, 19 T 529/02 und BGH, Beschluss XII ZB 236/05")
    tpl_refs = decisions_from_templates(mwparserfromhell.parse("{{Rspr|19 T 529/02}} {{Rspr|XII ZB 236/05}}"))
    merged = merge_decisions(text_refs + tpl_refs)
    assert [r.id for r in merged] == ["LG Frankfurt/Oder 19 T 529/02", "XII ZB 236/05"]
    assert merged[1].art == "Beschluss"


@pytest.mark.parametrize("text", [
    "Rechtsprechung des BGH; FGPrax 1/2012",          # Zeitschrift, kein Finanzgericht
    "Urteil vom 02.02.2018, 2 AGH 12/17",             # Anwaltsgerichtshof, nicht AG
])
def test_court_not_inside_word(text):
    assert [r.gericht for r in parse_decisions(text)] in ([], [None])


def test_trailing_dot_in_place_from_typo():
    assert one("LG Lübeck. Beschluss vom 23.07.2007, 7 T 135/07").gericht == "LG Lübeck"
    assert one("OLG Frankfurt/M., Beschluss vom 1.2.2003, 20 W 1/03").gericht == "OLG Frankfurt/M."
