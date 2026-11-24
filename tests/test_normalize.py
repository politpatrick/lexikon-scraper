from pathlib import Path

from lexikon.models import RawPage
from lexikon.normalize import build_redirect_map, normalize

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
