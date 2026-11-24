"""Qualitätsbericht über Artikel und Wissensnetz."""
from __future__ import annotations

from collections import Counter

from lexikon.normalize import Article


def quality_report(articles: list[Article], graph: dict) -> str:
    node_types = Counter(n["id"].split(":", 1)[0] for n in graph["nodes"])
    relations = Counter(e["relation"] for e in graph["links"])
    incoming = {e["target"] for e in graph["links"] if e["relation"] == "links_to"}
    orphans = sorted(a.title for a in articles if f"art:{a.slug}" not in incoming)
    dead = Counter(d for a in articles for d in a.dead_links)

    out = ["# Qualitätsbericht Wissensnetz", "", "## Kennzahlen", "",
           f"- Artikel: {len(articles)}",
           f"- Knoten: {len(graph['nodes'])} "
           f"({', '.join(f'{k}: {v}' for k, v in sorted(node_types.items()))})",
           f"- Kanten: {len(graph['links'])} "
           f"({', '.join(f'{k}: {v}' for k, v in sorted(relations.items()))})",
           f"- Wikipedia-Links: {sum(len(a.wikipedia_links) for a in articles)}",
           f"- Bilder: {sum(len(a.images) for a in articles)}",
           f"- Tote interne Links: {sum(dead.values())} (verschiedene Ziele: {len(dead)})",
           "", "## Waisen", "",
           "Artikel ohne eingehenden Link aus einem anderen Artikel.", ""]
    out += [f"- {t}" for t in orphans] or ["- keine"]
    out += ["", "## Tote Links", "", "| Ziel | Anzahl |", "|---|---|"]
    out += [f"| {target} | {n} |" for target, n in sorted(dead.items(), key=lambda x: (-x[1], x[0]))]
    return "\n".join(out) + "\n"
