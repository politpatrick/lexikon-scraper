"""Wissensnetz als graphify-kompatibler node-link-Graph (ADR 0002)."""
from __future__ import annotations

from urllib.parse import urlparse

from lexikon.normalize import Article


def article_file(a: Article) -> str:
    return f"articles/{a.pageid}.json"


def build_graph(articles: list[Article]) -> dict:
    """Knoten: art:/cat:/ext:. Kanten: links_to, in_category, references_external.

    ``directed: false`` folgt der graphify-Konvention; die Richtung steckt in
    der Reihenfolge source → target.
    """
    nodes: dict[str, dict] = {}
    edges: list[dict] = []
    seen_edges: set[tuple[str, str, str]] = set()

    def node(node_id: str, label: str, file_type: str, source_file: str) -> None:
        nodes.setdefault(node_id, {"id": node_id, "label": label,
                                   "file_type": file_type, "source_file": source_file})

    def edge(src: str, rel: str, tgt: str, source_file: str) -> None:
        if (src, rel, tgt) in seen_edges:
            return
        seen_edges.add((src, rel, tgt))
        edges.append({"source": src, "target": tgt, "relation": rel,
                      "confidence": "EXTRACTED", "source_file": source_file})

    for a in articles:
        node(f"art:{a.slug}", a.title, "document", article_file(a))
    for a in articles:
        me, sf = f"art:{a.slug}", article_file(a)
        for target in a.internal_links:
            if f"art:{target}" in nodes:
                edge(me, "links_to", f"art:{target}", sf)
        for cat in a.categories:
            node(f"cat:{cat}", cat, "concept", sf)
            edge(me, "in_category", f"cat:{cat}", sf)
        for url in a.external_links:
            host = urlparse(url).netloc.lower()
            if host:
                node(f"ext:{host}", host, "concept", sf)
                edge(me, "references_external", f"ext:{host}", sf)
    return {"directed": False, "multigraph": False, "graph": {},
            "nodes": sorted(nodes.values(), key=lambda n: n["id"]),
            "links": edges}
