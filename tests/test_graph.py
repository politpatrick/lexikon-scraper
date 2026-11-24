from lexikon.graph import build_graph
from lexikon.normalize import Article
from lexikon.report import quality_report


def art(pageid, slug, links=(), cats=(), ext=(), dead=()):
    return Article(pageid=pageid, title=slug.title(), slug=slug, revid=1, timestamp="t",
                   categories=list(cats), internal_links=list(links),
                   external_links=list(ext), dead_links=list(dead),
                   wikipedia_links=["de:Notar"], images=["x.jpg"])


ARTICLES = [
    art(1, "betreuer", links=["betreuungsgericht"], cats=["Personen"],
        ext=["https://www.bgh.de/a", "https://www.bgh.de/b"], dead=["gibt-es-nicht"]),
    art(2, "betreuungsgericht", links=["betreuer"], cats=["Personen", "Gericht"]),
    art(3, "waise", dead=["gibt-es-nicht"]),
]


def test_edges_reference_existing_nodes():
    g = build_graph(ARTICLES)
    ids = {n["id"] for n in g["nodes"]}
    assert all(e["source"] in ids and e["target"] in ids for e in g["links"])


def test_node_and_edge_fields():
    g = build_graph(ARTICLES)
    assert all(n["source_file"] and n["label"] and n["file_type"] for n in g["nodes"])
    assert all(e["confidence"] == "EXTRACTED" and e["source_file"] for e in g["links"])
    assert g["directed"] is False and g["multigraph"] is False


def test_relations():
    g = build_graph(ARTICLES)
    rel = {(e["source"], e["relation"], e["target"]) for e in g["links"]}
    assert ("art:betreuer", "links_to", "art:betreuungsgericht") in rel
    assert ("art:betreuungsgericht", "in_category", "cat:Gericht") in rel
    assert ("art:betreuer", "references_external", "ext:www.bgh.de") in rel


def test_external_hosts_deduplicated():
    g = build_graph(ARTICLES)
    ext = [e for e in g["links"] if e["relation"] == "references_external"]
    assert len(ext) == 1


def test_links_to_only_between_articles():
    g = build_graph(ARTICLES)
    for e in g["links"]:
        if e["relation"] == "links_to":
            assert e["target"].startswith("art:")


def test_report_sections():
    r = quality_report(ARTICLES, build_graph(ARTICLES))
    for heading in ("## Kennzahlen", "## Waisen", "## Tote Links"):
        assert heading in r
    assert "Waise" in r.split("## Waisen")[1].split("##")[0]
    assert "gibt-es-nicht | 2" in r
