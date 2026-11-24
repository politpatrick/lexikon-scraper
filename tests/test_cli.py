import json

from lexikon.__main__ import main
from lexikon.archive import sync_raw
from lexikon.models import RawPage


def test_build_end_to_end(tmp_path):
    raw = tmp_path / "raw"
    sync_raw([
        RawPage(1, "Betreuer", 5, "t", "Text mit [[Betreuerin]] und [[Fehlt]]\n[[Kategorie:Personen]]", ("Personen",)),
        RawPage(2, "Betreuerin", 6, "t", "#WEITERLEITUNG [[Betreuer]]", (), True),
        RawPage(3, "Gericht", 7, "t", "Siehe [[Betreuerin]].", ()),
    ], raw)
    rc = main(["build", "--raw", str(raw), "--articles", str(tmp_path / "articles"),
               "--graph", str(tmp_path / "graph" / "graph.json"),
               "--report", str(tmp_path / "reports" / "qualitaet.md"),
               "--templates-report", str(tmp_path / "reports" / "vorlagen.md")])
    assert rc == 0
    files = sorted(p.name for p in (tmp_path / "articles").glob("*.json"))
    assert files == ["1.json", "3.json"]
    gericht = json.loads((tmp_path / "articles" / "3.json").read_text(encoding="utf-8"))
    assert gericht["internal_links"] == ["betreuer"]
    graph = json.loads((tmp_path / "graph" / "graph.json").read_text(encoding="utf-8"))
    assert any(e["source"] == "art:gericht" and e["target"] == "art:betreuer"
               for e in graph["links"])
    assert "## Waisen" in (tmp_path / "reports" / "qualitaet.md").read_text(encoding="utf-8")


def test_build_removes_stale_article_files(tmp_path):
    raw = tmp_path / "raw"
    sync_raw([RawPage(1, "A", 1, "t", "x", ())], raw)
    arts = tmp_path / "articles"
    arts.mkdir()
    (arts / "99.json").write_text("{}")
    main(["build", "--raw", str(raw), "--articles", str(arts),
          "--graph", str(tmp_path / "g.json"), "--report", str(tmp_path / "r.md"),
          "--templates-report", str(tmp_path / "v.md")])
    assert sorted(p.name for p in arts.glob("*.json")) == ["1.json"]


def test_build_keeps_article_on_slug_collision(tmp_path):
    raw = tmp_path / "raw"
    sync_raw([
        RawPage(1, "Einwilligungsvorbehalt", 1, "t", "Inhalt", ()),
        RawPage(2, "E­inwilligungs­vor­be­halt", 1, "t", "#redirect [[Einwilligungsvorbehalt]]", (), True),
        RawPage(3, "Andere", 1, "t", "[[Einwilligungsvorbehalt]] [[BtPrax]]", ()),
        RawPage(4, "Betreuungsrechtliche Praxis", 1, "t", "Zeitschrift", ()),
    ], raw, unreadable=[{"pageid": 9, "title": "BtPrax", "lastrevid": 1,
                         "redirect_to": "Betreuungsrechtliche Praxis"}])
    main(["build", "--raw", str(raw), "--articles", str(tmp_path / "a"),
          "--graph", str(tmp_path / "g.json"), "--report", str(tmp_path / "r.md"),
          "--templates-report", str(tmp_path / "v.md")])
    assert sorted(p.name for p in (tmp_path / "a").glob("*.json")) == ["1.json", "3.json", "4.json"]
    andere = json.loads((tmp_path / "a" / "3.json").read_text(encoding="utf-8"))
    assert andere["internal_links"] == ["betreuungsrechtliche-praxis", "einwilligungsvorbehalt"]
    assert andere["dead_links"] == []


def test_build_writes_template_inventory(tmp_path):
    raw = tmp_path / "raw"
    sync_raw([RawPage(1, "A", 1, "t", "{{Zitat de §|1|bgb}} {{Neu}}", ())], raw)
    main(["build", "--raw", str(raw), "--articles", str(tmp_path / "a"),
          "--graph", str(tmp_path / "g.json"), "--report", str(tmp_path / "r.md"),
          "--templates-report", str(tmp_path / "v.md")])
    report = (tmp_path / "v.md").read_text(encoding="utf-8")
    assert "| Zitat de § | 1 | 1 | Normzitat |" in report
    assert "Unbekannte Vorlagen: 1" in report
