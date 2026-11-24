"""Kommandozeile: ``python -m lexikon archive|build``."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lexikon.archive import dump_json, load_raw, sync_raw
from lexikon.graph import build_graph
from lexikon.links import slug
from lexikon.normalize import build_redirect_map, normalize
from lexikon.report import quality_report


def cmd_archive(args) -> int:
    import requests

    from lexikon.api import iter_raw_pages

    unreadable: list[dict] = []
    with requests.Session() as session:
        res = sync_raw(iter_raw_pages(session, unreadable=unreadable), Path(args.raw), unreadable)
    print(f"Rohseiten: {res.written} geschrieben, {res.unchanged} unverändert, "
          f"{len(res.deleted)} neu als gelöscht protokolliert, "
          f"{res.unreadable} ohne abrufbare Revision (siehe _unreadable.jsonl)")
    return 0


def cmd_build(args) -> int:
    pages = load_raw(Path(args.raw), include_deleted=False)
    redirects = build_redirect_map(pages)
    content = [p for p in pages if not p.is_redirect and slug(p.title) not in redirects]
    for p in pages:
        if p.is_redirect and slug(p.title) not in redirects:
            print(f"Warnung: Weiterleitung ohne erkennbares Ziel: {p.title}", file=sys.stderr)
    known = {slug(p.title) for p in content}
    articles = [normalize(p, redirects, known) for p in content]

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
    b.set_defaults(func=cmd_build)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
