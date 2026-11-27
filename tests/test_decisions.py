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
    ("OLG Frankfurt/Main, Beschluss vom 08.06.2006, 20 W 52/06", "OLG Frankfurt am Main", "Beschluss", "2006-06-08", "20 W 52/06"),
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
    assert [r.id for r in merged] == ["LG Frankfurt (Oder) 19 T 529/02", "XII ZB 236/05"]
    assert merged[1].art == "Beschluss"


@pytest.mark.parametrize("text", [
    "Rechtsprechung des BGH; FGPrax 1/2012",          # Zeitschrift, kein Finanzgericht
    "Urteil vom 02.02.2018, 2 AGH 12/17",             # Anwaltsgerichtshof, nicht AG
])
def test_court_not_inside_word(text):
    assert [r.gericht for r in parse_decisions(text)] in ([], [None])


def test_trailing_dot_in_place_from_typo():
    assert one("LG Lübeck. Beschluss vom 23.07.2007, 7 T 135/07").gericht == "LG Lübeck"
    assert one("OLG Frankfurt/M., Beschluss vom 1.2.2003, 20 W 1/03").gericht == "OLG Frankfurt am Main"


# --- Befunde aus dem Review vom 27.11.2026 (echte Beispiele) ---------------------------

def azs(text):
    return [(r.gericht, r.az) for r in parse_decisions(text)]


@pytest.mark.parametrize("text,expected", [
    # 1. BayObLG-Register
    ("BayObLG, Beschluss vom 12.09.2002, 3Z BR 169/02", [("BayObLG", "3Z BR 169/02")]),
    ("BayObLG, Beschluss vom 25.07.2001, 3 Z BR 102/01", [("BayObLG", "3Z BR 102/01")]),
    ("BayObLG 2 ZBR 157/04", [("BayObLG", "2Z BR 157/04")]),
    # 2. Adjektivische Gerichtsnamen, Aktenzeichen mit Gerichtspräfix
    ("Brandenburgisches OLG, Beschluss vom 01.03.2007, 11 Wx 7/07", [("OLG Brandenburg", "11 Wx 7/07")]),
    ("Thüringer OLG, Beschluss vom 1.2.2006, 9 W 627/05", [("OLG Jena", "9 W 627/05")]),
    ("Bayerisches LSG, Urteil vom 03.07.2006, L 13 R 352/06", [("LSG Bayern", "L 13 R 352/06")]),
    ("OVG Berlin-Brandenburg, Beschluss vom 08.06.2021, OVG 6 M 38/21", [("OVG Berlin-Brandenburg", "OVG 6 M 38/21")]),
    ("OLG Dresden, Beschluss vom 5.2.2015, 2 OLG 21 Ss 734/14", [("OLG Dresden", "2 OLG 21 Ss 734/14")]),
    # 3. „v“ ohne Punkt
    ("BGH Beschl v 26.3.2014, XII ZB 256/13", [("BGH", "XII ZB 256/13")]),
    ("LG Oldenburg Urt v 15.5.2009, 13 S 62/09", [("LG Oldenburg", "13 S 62/09")]),
    ("BSG Beschl. V. 21.08.2019, B 8 SO 2/19", [("BSG", "B 8 SO 2/19")]),
    # 4. Allein eindeutige Aktenzeichen ohne Gericht davor; Datum ohne „vom“
    ("im Anschluss an Senatsbeschluss vom 14. Oktober 2020 XII ZB 235/20", [("BGH", "XII ZB 235/20")]),
    ("BGH 7. Dezember 2006 - IX ZB 257/05", [("BGH", "IX ZB 257/05")]),
    ("OLG Stuttgart 15. April 2014 - 4 W 53/13", [("OLG Stuttgart", "4 W 53/13")]),
    # 5. Listen von Aktenzeichen, Plural
    ("Kammergericht Berlin, Beschluss vom 20.12.2005, 1 W 170/03 und 1 W 182/03",
     [("KG", "1 W 170/03"), ("KG", "1 W 182/03")]),
    ("BVerfG, Beschluss vom 26.05.2020, 2 BvR 1529/19, 2 BvR 1625/19",
     [("BVerfG", "2 BvR 1529/19"), ("BVerfG", "2 BvR 1625/19")]),
    ("BGH, Beschlüsse XII ZB 605/10, XII ZB 461/11", [("BGH", "XII ZB 605/10"), ("BGH", "XII ZB 461/11")]),
    # 6. Schreibweisen
    ("KG Berlin, Beschluss vom 13.10.2009, 1 W 161/08", [("KG", "1 W 161/08")]),
    ("OLG Frankfurt a.M., Beschluss vom 1.2.2010, 20 W 90/10", [("OLG Frankfurt am Main", "20 W 90/10")]),
    ("OLG Düsseldorf, Beschluss vom 1.2.2008, I-25 Wx 71/07", [("OLG Düsseldorf", "I-25 Wx 71/07")]),
    ("OLG Düsseldorf (25. Zivilsenat), Beschluss vom 1.2.2008, I-25 Wx 71/07", [("OLG Düsseldorf", "I-25 Wx 71/07")]),
    ("SG Berlin; Beschluss vom 1.2.2010, S 51 SO 1/10", [("SG Berlin", "S 51 SO 1/10")]),
    ("LSG NRW, Urteil vom 1.2.2010, L 9 SO 6/08", [("LSG Nordrhein-Westfalen", "L 9 SO 6/08")]),
    ("LG Frankfurt (Oder), Beschluss vom 1.2.2003, 19 T 529/02", [("LG Frankfurt (Oder)", "19 T 529/02")]),
    ("LG Frankfurt/Oder, Beschluss vom 1.2.2003, 19 T 529/02", [("LG Frankfurt (Oder)", "19 T 529/02")]),
    # Ortlose Gerichte werden nicht als Gericht übernommen
    ("das OLG, Beschluss vom 1.2.2003, 1 W 1/03", [(None, "1 W 1/03")]),
])
def test_review_findings(text, expected):
    assert azs(text) == expected


@pytest.mark.parametrize("text", [
    "BayObLG BtE 1996/97, 87",            # 7. Zeitschrift, keine Entscheidung
    "LG Kleve BtE 1992/93, 38",
    "AG Kaiserslautern RdLH 3/1995, 28",
    "LG Köln NJW 5/2001",
])
def test_journals_are_not_aktenzeichen(text):
    assert parse_decisions(text) == []


def test_bsg_r_suffix_same_id():
    a = one("BSG, Urteil vom 1.2.2002, B 12 KR 14/01 R")
    b = one("BSG, Urteil vom 1.2.2002, B 12 KR 14/01")
    assert a.id == b.id == "B 12 KR 14/01"
    assert a.az == "B 12 KR 14/01 R"


def test_bayoblg_spacing_same_id():
    assert one("BayObLG 3 Z BR 102/01").id == one("BayObLG, 3Z BR 102/01").id == "3Z BR 102/01"


def test_roman_rule_not_too_broad():
    assert one("VG Bremen, Urteil vom 1.2.1955, II A 17/54").id == "VG Bremen II A 17/54"
    tpl = decisions_from_templates(mwparserfromhell.parse("{{Rspr|VI R 52/17}}"))
    assert tpl[0].gericht == "BFH"


def test_invalid_date_dropped():
    assert one("BGH, Beschluss vom 31.11.2010, XII ZB 1/10").datum is None


def test_template_journal_fundstelle():
    refs = decisions_from_templates(mwparserfromhell.parse("{{Rspr|NJW 1998, 1774}} {{Rspr|BVerGE 70, 297}}"))
    assert [(r.az, r.fundstelle) for r in refs] == [(None, "NJW 1998, 1774"), (None, "BVerGE 70, 297")]


@pytest.mark.parametrize("text", ["BGH" + " " * 8000 + "x", "BGH, Beschluss vom " + "1 W 1/03, " * 500,
                                  "OLG " * 3000])
def test_no_slow_regex(text):
    import time
    start = time.perf_counter()
    parse_decisions(text)
    assert time.perf_counter() - start < 1.0


def test_courtless_prose_yields_nothing():
    """Ohne Ort und ohne zitierten Spruch ist ein lokales Aktenzeichen nicht zuzuordnen."""
    assert parse_decisions("das OLG hat mit Beschluss vom 1.2.2003, 1 W 1/03 entschieden") == []


@pytest.mark.parametrize("text,expected", [
    # Stichprobe nach dem Umbau: Zahl vor dem Gericht (Ende der vorigen Fundstelle)
    ("BtPrax 2006, 76 LG Halle, Beschluss vom 8.1.2008, 1 T 155/07", [("LG Halle", "1 T 155/07")]),
    ("vom 5.4.2006 LG Trier, Beschluss 5 T 140/05 vom 1.2.2006", [("LG Trier", "5 T 140/05")]),
    ("-LG Bielefeld , Beschluss vom 12.05.2006, 25 T 89/06", [("LG Bielefeld", "25 T 89/06")]),
    ("LG Freiburg (Breisgau), Beschluss vom 23.05.2025, 4 T 40/25", [("LG Freiburg (Breisgau)", "4 T 40/25")]),
    ("VG Karlsruhe, · Gerichtsbescheid vom 30.8.2012 · Az. 6 K 1287/12", [("VG Karlsruhe", "6 K 1287/12")]),
    ("LG Ellwangen, Endurteil vom 20.11.2025, 3 O 185/25", [("LG Ellwangen", "3 O 185/25")]),
    ("Kammergericht Berlin, Beschluss vom 23.01.2007, |1 W 430/03", [("KG", "1 W 430/03")]),
    # weiterhin: Gericht im Aktenzeichen wird nicht als eigenes Zitat gelesen
    ("OLG Dresden, Beschluss vom 5.2.2015, 2 OLG 21 Ss 734/14", [("OLG Dresden", "2 OLG 21 Ss 734/14")]),
])
def test_sample_after_rewrite(text, expected):
    assert azs(text) == expected
