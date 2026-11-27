"""Kommandozeile: ``python -m lexikon archive|build``."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lexikon.archive import dump_json, load_raw, load_unreadable, sync_raw
from lexikon.graph import build_graph
from lexikon.links import slug
from lexikon.normalize import build_redirect_map, is_content, normalize, unify_decisions
from lexikon.report import quality_report
from lexikon.templates import inventory, inventory_report


def cmd_archive(args) -> int:
    import requests

    from lexikon.api import fetch_redirect_targets, iter_raw_pages

    unreadable: list[dict] = []
    with requests.Session() as session:
        pages = list(iter_raw_pages(session, unreadable=unreadable))
        targets = fetch_redirect_targets(session, [u["title"] for u in unreadable])
    for u in unreadable:
        if u["title"] in targets:
            u["redirect_to"] = targets[u["title"]]
    res = sync_raw(pages, Path(args.raw), unreadable)
    print(f"Rohseiten: {res.written} geschrieben, {res.unchanged} unverändert, "
          f"{len(res.deleted)} neu als gelöscht protokolliert, "
          f"{res.unreadable} ohne abrufbare Revision (siehe _unreadable.jsonl)")
    return 0


def cmd_build(args) -> int:
    pages = load_raw(Path(args.raw), include_deleted=False)
    redirects = build_redirect_map(pages, load_unreadable(Path(args.raw)))
    content = [p for p in pages if is_content(p)]
    for p in pages:
        if not is_content(p) and slug(p.title) not in redirects:
            print(f"Hinweis: Weiterleitung ohne eigenen Eintrag: {p.title}", file=sys.stderr)
    known = {slug(p.title) for p in content}
    articles = [normalize(p, redirects, known) for p in content]
    unify_decisions(articles)

    out = Path(args.articles)
    out.mkdir(parents=True, exist_ok=True)
    wanted = {f"{a.pageid}.json" for a in articles}
    for stale in out.glob("*.json"):
        if stale.name not in wanted:
            stale.unlink()
    for a in articles:
        dump_json(a.to_json(), out / f"{a.pageid}.json")

    graph = build_graph(articles)
    graph_path = Path(args.graph)
    graph_path.parent.mkdir(parents=True, exist_ok=True)
    dump_json(graph, graph_path)

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(quality_report(articles, graph), encoding="utf-8")
    templates_path = Path(args.templates_report)
    templates_path.parent.mkdir(parents=True, exist_ok=True)
    templates_path.write_text(inventory_report(inventory(content)), encoding="utf-8")
    print(f"Artikel: {len(articles)}, Weiterleitungen: {len(redirects)}, "
          f"Knoten: {len(graph['nodes'])}, Kanten: {len(graph['links'])}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="lexikon")
    sub = parser.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("archive", help="Rohseiten aus dem Lexikon abrufen")
    a.add_argument("--raw", default="raw")
    a.set_defaults(func=cmd_archive)
    b = sub.add_parser("build", help="Artikel, Wissensnetz und Bericht aus raw/ erzeugen")
    b.add_argument("--raw", default="raw")
    b.add_argument("--articles", default="articles")
    b.add_argument("--graph", default="graph/graph.json")
    b.add_argument("--report", default="reports/qualitaet.md")
    b.add_argument("--templates-report", default="reports/vorlagen.md")
    b.set_defaults(func=cmd_build)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
