import pytest
import mwparserfromhell

from lexikon.models import RawPage
from lexikon.templates import canonical_name, inventory, inventory_report, render_template


def tpl(text):
    return mwparserfromhell.parse(text).filter_templates()[0]


@pytest.mark.parametrize("wikitext,expected", [
    # Darstellung laut Vorlagendefinition im Lexikon (abgerufen 24.11.2026)
    ("{{Zitat de §|1801|bgb}}", "§ 1801"),
    ("{{Zitat-dej|§|1868|bgb}}", "§ 1868"),
    ("{{Zitat-dej|§§|433|BGB}}", "§§ 433"),
    ("{{Zitat-dej|Art.|14|GG}}", "Art. 14"),
    ("{{Zitat Art|24|bgbeg}}", "Art. 24"),
    ("{{Rspr|2 BvR 2115/01}}", "2 BvR 2115/01"),
    ("{{rspr|BVerfGE 75, 318}}", "BVerfGE 75, 318"),
    ("{{ISSN|1864-7820}}", "ISSN 1864-7820"),
    ("{{TOC}}", ""),
    ("{{Prettytable-R Gesetz}}", ""),
])
def test_render_known_templates(wikitext, expected):
    assert render_template(tpl(wikitext), "Seite") == expected


def test_pagename():
    assert render_template(tpl("{{PAGENAME}}"), "Betreuer") == "Betreuer"


def test_quelle_wikipedia_keeps_attribution():
    t = tpl("{{Quelle Wikipedia|Betreuungsrecht|9. Juni 2006|3=http://de.wikipedia.org/x}}")
    assert render_template(t, "S") == "Quelle: Wikipedia, Artikel „Betreuungsrecht“, Stand 9. Juni 2006 (http://de.wikipedia.org/x)"


def test_infobox_rendered_as_lines():
    t = tpl("{{Infobox Publikation\n|titel = BtPrax\n|bild = \n|issn = 1864-7820\n}}")
    assert render_template(t, "S") == "titel: BtPrax\nissn: 1864-7820"


def test_unknown_template_kept_verbatim():
    assert render_template(tpl("{{Neu|x}}"), "S") == "{{Neu|x}}"


def test_canonical_name_first_letter_and_spaces():
    assert canonical_name("rspr") == canonical_name("Rspr") == "Rspr"
    assert canonical_name(" Zitat_de  § ") == "Zitat de §"


def test_inventory_counts_and_report():
    pages = [
        RawPage(1, "A", 1, "t", "{{Zitat de §|1|bgb}} {{Zitat de §|2|bgb}} {{Neu}}"),
        RawPage(2, "B", 1, "t", "{{rspr|X}} {{Rspr|Y}} {{Zitat de §|3|bgb}}"),
    ]
    inv = {u.name: u for u in inventory(pages)}
    assert inv["Zitat de §"].count == 3 and inv["Zitat de §"].pages == 2
    assert inv["Rspr"].count == 2
    assert inv["Neu"].known is False
    report = inventory_report(inventory(pages))
    assert "| Zitat de § | 3 | 2 |" in report
    assert "Unbekannte Vorlagen: 1" in report
