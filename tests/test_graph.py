from lexikon.graph import build_graph
from lexikon.normalize import Article
from lexikon.report import quality_report


def norm(i, label):
    return {"id": i, "label": label, "gesetz": "BGB", "einheit": "§", "nummer": i[4:],
            "alte_fassung": False}


def art(pageid, slug, links=(), cats=(), ext=(), dead=(), norms=()):
    return Article(pageid=pageid, title=slug.title(), slug=slug, revid=1, timestamp="t",
                   categories=list(cats), internal_links=list(links),
                   external_links=list(ext), dead_links=list(dead),
                   wikipedia_links=["de:Notar"], images=["x.jpg"], norms=list(norms))


ARTICLES = [
    art(1, "betreuer", links=["betreuungsgericht"], cats=["Personen"],
        ext=["https://www.bgh.de/a", "https://www.bgh.de/b"], dead=["gibt-es-nicht"],
        norms=[norm("BGB§1814", "§ 1814 BGB"), norm("BGB§1816", "§ 1816 BGB")]),
    art(2, "betreuungsgericht", links=["betreuer"], cats=["Personen", "Gericht"],
        norms=[norm("BGB§1814", "§ 1814 BGB")]),
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


def test_norm_nodes_and_edges():
    g = build_graph(ARTICLES)
    nodes = {n["id"]: n for n in g["nodes"]}
    assert nodes["norm:BGB§1814"]["label"] == "§ 1814 BGB"
    assert nodes["norm:BGB§1814"]["file_type"] == "concept"
    rel = {(e["source"], e["relation"], e["target"]) for e in g["links"]}
    assert ("art:betreuer", "cites_norm", "norm:BGB§1814") in rel
    assert ("art:betreuungsgericht", "cites_norm", "norm:BGB§1814") in rel


def test_report_top_norms():
    r = quality_report(ARTICLES, build_graph(ARTICLES))
    section = r.split("## Meistzitierte Normen")[1]
    assert "| § 1814 BGB | 2 |" in section
    assert "| § 1816 BGB | 1 |" in section


def test_report_gap_suspects():
    a = art(4, "luecke")
    from lexikon.normalize import Section
    a.sections = [Section(("Einleitung",), "nach Maßgabe von  des Landesgesetzes.")]
    part = quality_report([a], build_graph([a])).split("## Verdacht auf gelöschte Normverweise")[1]
    assert "- Luecke: `nach Maßgabe von  des Landesgesetzes.`" in part


def test_report_no_gap_for_double_space_after_number():
    a = art(5, "quelle")
    from lexikon.normalize import Section
    a.sections = [Section(("Einleitung",), "erlischt der Anspruch (§ 7  Abs. 1 VBVG).")]
    part = quality_report([a], build_graph([a])).split("## Verdacht auf gelöschte Normverweise")[1]
    assert part.split("##")[0].strip().endswith("- keine")


def test_report_unknown_laws():
    a = art(6, "x", norms=[{"id": "XYZ§1", "label": "§ 1 XYZ", "gesetz": "XYZ", "einheit": "§",
                            "nummer": "1", "alte_fassung": False}])
    part = quality_report([a], build_graph([a])).split("## Unbekannte Gesetzeskürzel")[1]
    assert "XYZ" in part.split("##")[0]


def test_report_gap_check_is_fast():
    import time
    from lexikon.normalize import Section
    a = art(7, "lang")
    a.sections = [Section(("E",), "Wort " * 40000)]
    start = time.perf_counter()
    quality_report([a], build_graph([a]))
    assert time.perf_counter() - start < 0.5


def dec(i, label):
    return {"id": i, "label": label, "gericht": "BGH", "art": None, "datum": None, "az": i, "fundstelle": None}


def test_decision_nodes_edges_and_report():
    arts = [art(1, "a"), art(2, "b")]
    arts[0].decisions = [dec("XII ZB 1/20", "BGH – XII ZB 1/20")]
    arts[1].decisions = [dec("XII ZB 1/20", "BGH – XII ZB 1/20"), dec("V ZR 2/19", "BGH – V ZR 2/19")]
    g = build_graph(arts)
    nodes = {n["id"]: n for n in g["nodes"]}
    assert nodes["dec:XII ZB 1/20"]["label"] == "BGH – XII ZB 1/20"
    rel = {(e["source"], e["relation"], e["target"]) for e in g["links"]}
    assert ("art:b", "cites_decision", "dec:V ZR 2/19") in rel
    section = quality_report(arts, g).split("## Meistzitierte Entscheidungen")[1]
    assert "| BGH – XII ZB 1/20 | 2 |" in section
