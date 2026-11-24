"""Qualitätsbericht über Artikel und Wissensnetz."""
from __future__ import annotations

import re
from collections import Counter

from lexikon.normalize import Article
from lexikon.norms import is_known_law


#: Präposition, dann Lücke aus mehreren Leerzeichen, dann typischer Normanschluss.
#: Nicht nach einer Zahl (``§ 7  Abs. 1`` ist eine Doppel-Leerstelle der Quelle).
#: Ohne führendes ``.{0,40}``: der Kontext wird per Slicing ergänzt (sonst quadratisch).
GAP = re.compile(
    r"\b(?:von|vgl\.|nach|gem\.|gemäß|siehe|i\.\s?V\.\s?m\.) {2,}"
    r"(?:Abs\.|des|der|dem|SGB|BGB|FamFG)\b"
)


def _gap_snippets(text: str) -> list[str]:
    return [text[max(0, m.start() - 40):m.end() + 30].strip() for m in GAP.finditer(text)]


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
    norm_labels = {n["id"]: n["label"] for a in articles for n in a.norms}
    citing = Counter(n["id"] for a in articles for n in a.norms)
    out += ["", "## Meistzitierte Normen", "",
            f"{len(citing)} verschiedene Normen, zitiert in "
            f"{sum(1 for a in articles if a.norms)} Artikeln.", "",
            "| Norm | Artikel |", "|---|---|"]
    out += [f"| {norm_labels[i]} | {n} |" for i, n in sorted(citing.items(), key=lambda x: (-x[1], x[0]))[:50]]
    suspects = [(a.title, snippet) for a in articles for s in a.sections
                for snippet in _gap_snippets(s.text)]
    out += ["", "## Verdacht auf gelöschte Normverweise", "",
            "Stellen wie „nach Maßgabe von  des Landesgesetzes“. Prüfen, ob die Lücke schon "
            "im Original steht.", ""]
    out += [f"- {t}: `{snippet}`" for t, snippet in suspects] or ["- keine"]
    unknown = Counter(n["gesetz"] for a in articles for n in a.norms if not is_known_law(n["gesetz"]))
    out += ["", "## Unbekannte Gesetzeskürzel", "",
            "Aus Vorlagen übernommene Kürzel, die nicht in der Gesetzesliste stehen "
            "(Tippfehler im Wiki oder fehlender Eintrag in norms.py).", ""]
    out += [f"- {law}: {n}" for law, n in sorted(unknown.items())] or ["- keine"]
    out += ["", "## Tote Links", "", "| Ziel | Anzahl |", "|---|---|"]
    out += [f"| {target} | {n} |" for target, n in sorted(dead.items(), key=lambda x: (-x[1], x[0]))]
    return "\n".join(out) + "\n"
