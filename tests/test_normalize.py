from pathlib import Path

from lexikon.models import RawPage
from lexikon.normalize import build_redirect_map, is_content, normalize

FIX = Path(__file__).parent / "fixtures" / "wikitext"
KNOWN = {"betreuerbestellung", "betreuungsgericht", "betreuer", "betreuungsverfahren"}


def raw(title, text, pageid=1, redirect=False):
    return RawPage(pageid=pageid, title=title, revid=7, timestamp="2023-04-26T10:00:00Z",
                   wikitext=text, categories=("Verfahren",), is_redirect=redirect)


def verfahren(redirects=None):
    page = raw("Betreuungsverfahren", (FIX / "verfahren.txt").read_text(encoding="utf-8"))
    return normalize(page, redirects or {"betreuerin": "betreuer"}, KNOWN)


def test_metadata():
    a = verfahren()
    assert (a.pageid, a.title, a.slug, a.revid) == (1, "Betreuungsverfahren", "betreuungsverfahren", 7)
    assert a.categories == ["Verfahren"]


def test_section_paths():
    paths = [s.path for s in verfahren().sections]
    assert paths == [
        ("Einleitung",),
        ("Zuständigkeit bei Gericht",),
        ("Zuständigkeit bei Gericht", "International zuständig"),
        ("Literatur",),
    ]


def test_links_typed():
    a = verfahren()
    assert a.wikipedia_links == ["de:Freiwillige Gerichtsbarkeit"]
    assert a.images == ["Justiz.jpg"]
    assert a.external_links == ["http://www.bundesanzeiger-verlag.de/betreuung", "https://example.org/x"]
    assert a.category_links == ["Verfahren"]
    assert all(not l.startswith(("wikipedia", "bild")) for l in a.internal_links)


def test_link_text_kept():
    a = verfahren()
    text = a.sections[1].text
    assert "der Betreuer" in text
    assert "Betreuungsgericht" in text
    assert "[[" not in text
    assert "betreuer" in a.internal_links


def test_wikipedia_display_text_kept_and_image_dropped():
    text = verfahren().sections[0].text
    assert "freiwilligen Gerichtsbarkeit" in text
    assert "Justiz.jpg" not in text and "thumb" not in text
    assert "Kommentar" not in text


def test_templates_and_refs_not_silently_dropped():
    text = verfahren().sections[2].text
    assert "{{§|30|SGB I}}" in text
    assert "054 T 161/18" in text


def test_external_link_title_in_text():
    assert "BtPrax" in verfahren().sections[3].text


def test_redirect_resolved():
    a = verfahren()
    assert a.internal_links == ["betreuer", "betreuerbestellung", "betreuungsgericht"]


def test_dead_link():
    assert verfahren().dead_links == ["gibt-es-nicht"]


def test_redirect_chain_and_loop():
    pages = [
        raw("A", "#WEITERLEITUNG [[B]]", 1, True),
        raw("B", "#REDIRECT [[C#Teil]]", 2, True),
        raw("X", "#weiterleitung [[Y]]", 3, True),
        raw("Y", "#WEITERLEITUNG [[X]]", 4, True),
    ]
    redirects = build_redirect_map(pages)
    assert redirects == {"a": "b", "b": "c", "x": "y", "y": "x"}
    a = normalize(raw("Q", "[[A]] [[X]]"), redirects, {"c"})
    assert a.internal_links == ["c"]
    assert a.dead_links == ["x"]


def test_redirect_fixture_detected():
    p = raw("Betreuerin", (FIX / "weiterleitung.txt").read_text(encoding="utf-8"), 9)
    assert build_redirect_map([p]) == {"betreuerin": "betreuer"}


def test_to_json_shape():
    d = verfahren().to_json()
    assert d["sections"][2]["path"] == ["Zuständigkeit bei Gericht", "International zuständig"]
    assert d["slug"] == "betreuungsverfahren"


def test_list_items_readable():
    assert verfahren().sections[2].text.startswith("- deutsche Staatsbürgerschaft\n- Ausländer")


def test_redirect_variants():
    pages = [
        raw("A", "#WEITERLEITUNG: [[Ziel]]", 1, True),
        raw("B", "#WEITERLEITUNG [[:Ziel]]", 2, True),
        raw("C", "#REDIRECT[[ Ziel | Text ]]", 3, True),
    ]
    assert build_redirect_map(pages) == {"a": "ziel", "b": "ziel", "c": "ziel"}


def test_flagged_redirect_uses_first_link():
    assert build_redirect_map([raw("D", "#UMLEITUNG [[Ziel]]", 4, True)]) == {"d": "ziel"}


def test_reused_named_ref_leaves_no_empty_brackets():
    a = normalize(raw("R", 'Satz.<ref name="a">BGH XII ZB 1/20</ref> Mehr.<ref name="a"/>'), {}, set())
    assert a.sections[0].text == "Satz. [BGH XII ZB 1/20] Mehr."


def test_content_page_wins_slug_collision_with_redirect():
    """Live-Befund: Weiterleitung mit Soft-Hyphens hat denselben Slug wie der Artikel."""
    pages = [
        raw("Einwilligungsvorbehalt", "Text", 1),
        raw("E­inwilligungs­vor­be­halt", "#redirect [[Einwilligungsvorbehalt]]", 2, True),
        raw("Gesundheitssorge", "Text", 3),
        raw("Gesund­heitssorge", "#redirect [[Gesundheitsfürsorge]]", 4, True),
    ]
    redirects = build_redirect_map(pages)
    assert redirects == {}
    a = normalize(raw("Q", "[[Einwilligungsvorbehalt]] [[Gesundheitssorge]]"), redirects,
                  {"einwilligungsvorbehalt", "gesundheitssorge"})
    assert a.internal_links == ["einwilligungsvorbehalt", "gesundheitssorge"]


def test_unreadable_redirects_from_redirect_table():
    unreadable = [
        {"pageid": 1, "title": "BtPrax", "lastrevid": 1, "redirect_to": "Betreuungsrechtliche Praxis"},
        {"pageid": 2, "title": "Betreuer", "lastrevid": 2, "redirect_to": "Kategorie:Betreuungspersonen"},
        {"pageid": 3, "title": "Leer", "lastrevid": 3},
    ]
    redirects = build_redirect_map([], unreadable)
    assert redirects == {"btprax": "betreuungsrechtliche-praxis", "betreuer": "kategorie:betreuungspersonen"}
    a = normalize(raw("Q", "[[BtPrax]] [[Betreuer]] [[Leer]]"), redirects, {"betreuungsrechtliche-praxis"})
    assert a.internal_links == ["betreuungsrechtliche-praxis"]
    assert a.category_links == ["Betreuungspersonen"]
    assert a.dead_links == ["leer"]


def test_is_content():
    assert is_content(raw("A", "Text"))
    assert not is_content(raw("B", "#WEITERLEITUNG [[A]]"))
    assert not is_content(raw("C", "egal", redirect=True))


def test_norm_templates_rendered_regression():
    """Live-Befund: Der alte Scraper machte daraus „vgl.  Abs. 3 SGB-I“."""
    text = ("nach Maßgabe von {{Zitat de §|1|lfgg}} des Landesgesetzes; vgl. {{Zitat de §|30|sgb_1}} "
            "Abs. 3 SGB-I und {{Rspr|XII ZB 1/20}} sowie {{PAGENAME}}")
    a = normalize(raw("Betreuungsverfahren", text), {}, set())
    assert a.sections[0].text == ("nach Maßgabe von § 1 des Landesgesetzes; vgl. § 30 Abs. 3 SGB-I "
                                  "und XII ZB 1/20 sowie Betreuungsverfahren")


def test_norms_per_section_and_article():
    text = ("Einleitung mit {{Zitat de §|37|lfgg}} des Landesgesetzes.\n"
            "== Verfahren ==\nNach {{Zitat de §|1814|bgb}} [[BGB]] und § 272 Abs. 2 FamFG sowie § 1814 BGB.")
    a = normalize(raw("X", text), {}, {"bgb"})
    assert a.sections[0].norms == ["LFGG§37"]
    assert a.sections[1].norms == ["BGB§1814", "FamFG§272"]
    assert [n["id"] for n in a.norms] == ["BGB§1814", "FamFG§272", "LFGG§37"]
    assert a.norms[0] == {"id": "BGB§1814", "label": "§ 1814 BGB", "gesetz": "BGB",
                          "einheit": "§", "nummer": "1814", "alte_fassung": False}


def test_old_and_current_version_are_separate_norms():
    a = normalize(raw("X", "§ 1822 BGB a.F. und später § 1822 BGB"), {}, set())
    assert [(n["id"], n["label"], n["alte_fassung"]) for n in a.norms] == [
        ("BGB§1822", "§ 1822 BGB", False),
        ("BGB§1822@aF", "§ 1822 BGB a.F.", True),
    ]


def test_heading_templates_rendered_and_norms_attached():
    """Review: ==… {{Zitat de §|3|vbvg_2023}} VBVG== wurde zu „Zeitvergütung ( VBVG)“."""
    a = normalize(raw("V", "Intro\n== Zeitvergütung ({{Zitat de §|3|vbvg_2023}} VBVG) ==\nText.\n"
                           "== Volljährigkeit (§ 2 BGB) ==\nMehr."), {}, set())
    assert a.sections[1].path == ("Zeitvergütung (§ 3 VBVG)",)
    assert a.sections[1].norms == ["VBVG§3"]
    assert a.sections[2].norms == ["BGB§2"]


def test_template_norm_not_double_counted_from_rendered_text():
    """{{Zitat de §|8|vbvg}} VBVG darf nicht zusätzlich als aktuelles § 8 VBVG zählen."""
    a = normalize(raw("V", "Für {{Zitat de §|8|vbvg}} VBVG gilt"), {}, set())
    assert a.sections[0].norms == ["VBVG§8@aF"]
    assert a.sections[0].text == "Für § 8 VBVG gilt"


def test_decisions_per_section_and_article():
    text = ("Einleitung: LG Frankfurt/Oder, Beschluss vom 1.2.2003, {{Rspr|19 T 529/02}}.\n"
            "== Rechtsprechung ==\nBGH, Beschluss vom 05.01.2011 - XII ZB 152/10; vgl. {{rspr|BVerfGE 31, 58}}.")
    a = normalize(raw("X", text), {}, set())
    assert a.sections[0].decisions == ["LG Frankfurt/Oder 19 T 529/02"]
    assert a.sections[1].decisions == ["XII ZB 152/10", "BVerfGE 31, 58"]
    assert [d["id"] for d in a.decisions] == ["BVerfGE 31, 58", "LG Frankfurt/Oder 19 T 529/02", "XII ZB 152/10"]
    assert a.decisions[2] == {"id": "XII ZB 152/10", "label": "BGH, Beschluss vom 05.01.2011 – XII ZB 152/10",
                              "gericht": "BGH", "art": "Beschluss", "datum": "2011-01-05",
                              "az": "XII ZB 152/10", "fundstelle": None}
