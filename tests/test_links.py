import pytest

from lexikon.links import classify, slug


@pytest.mark.parametrize("title,expected", [
    ("Betreuer (Ehrenamt)", "betreuer-(ehrenamt)"),
    ("e­in­wil­li­gungs­vor­be­halt", "einwilligungsvorbehalt"),
    ("Gesund­heitssorge", "gesundheitssorge"),
    ("Vormünder- und Betreuervergütungsgesetz", "vormünder--und-betreuervergütungsgesetz"),
    ("Advance_Care_Planning", "advance-care-planning"),
    ("  Betreuer  ", "betreuer"),
])
def test_slug(title, expected):
    assert slug(title) == expected


def test_slug_first_letter_case_insensitive():
    assert slug("betreuer") == slug("Betreuer")


@pytest.mark.parametrize("target,expected", [
    ("Betreuer", ("internal", "Betreuer")),
    ("Betreuer#Auswahl", ("internal", "Betreuer")),
    (":Betreuer", ("internal", "Betreuer")),
    ("wikipedia:de:Notar", ("wikipedia", "de:Notar")),
    ("Wikipedia:de:Amtsgericht", ("wikipedia", "de:Amtsgericht")),
    ("Bild:Justiz.jpg", ("image", "Justiz.jpg")),
    ("Datei:x.png", ("image", "x.png")),
    ("File:x.png", ("image", "x.png")),
    ("Image:x.png", ("image", "x.png")),
    ("Kategorie:Verfahren", ("category", "Verfahren")),
    (":Kategorie:Verfahren", ("category-link", "Verfahren")),
    ("Betreuungsrecht-Lexikon:Haftungsausschluss", ("internal", "Betreuungsrecht-Lexikon:Haftungsausschluss")),
])
def test_classify(target, expected):
    assert classify(target) == expected
