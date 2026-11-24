from lexikon.models import RawPage


def test_rawpage_roundtrip():
    p = RawPage(
        pageid=42,
        title="E­in­wil­li­gungs­vor­be­halt für Ärzte",
        revid=1001,
        timestamp="2023-04-26T10:00:00Z",
        wikitext="'''Text''' mit [[Betreuer]]",
        categories=("Verfahren", "Öffentliches Recht"),
        is_redirect=False,
    )
    assert RawPage.from_json(p.to_json()) == p
