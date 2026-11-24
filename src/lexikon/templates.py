"""Vorlagen des Lexikons: Darstellung als Text und Inventur.

Die Darstellung folgt den Vorlagendefinitionen im Lexikon (abgerufen am
24.11.2026), damit der Text dem entspricht, was Leser im Wiki sehen.
Unbekannte Vorlagen bleiben wörtlich erhalten und erscheinen in der Inventur.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Callable

import mwparserfromhell
from mwparserfromhell.nodes import Template

from lexikon.models import RawPage


def canonical_name(name: str) -> str:
    """MediaWiki-Regeln: Unterstrich = Leerzeichen, erster Buchstabe egal."""
    n = " ".join(name.replace("_", " ").split())
    return n[:1].upper() + n[1:]


def _arg(t: Template, key, default: str = "") -> str:
    if t.has(key):
        return str(t.get(key).value).strip()
    return default


def _norm_paragraph(t: Template) -> str:
    return f"§ {_arg(t, 1)}"


def _norm_dejure(t: Template) -> str:
    return f"{_arg(t, 1)} {_arg(t, 2)}"


def _norm_article(t: Template) -> str:
    return f"Art. {_arg(t, 1)}"


def _decision(t: Template) -> str:
    return _arg(t, 1)


def _quelle_wikipedia(t: Template) -> str:
    text = f"Quelle: Wikipedia, Artikel „{_arg(t, 1)}“"
    if stand := " ".join(_arg(t, 2).split()):
        text += f", Stand {stand}"
    if url := _arg(t, 3):
        text += f" ({url})"
    return text


def _infobox(t: Template) -> str:
    lines = []
    for p in t.params:
        value = str(p.value).strip()
        if value:
            lines.append(f"{str(p.name).strip()}: {value}")
    return "\n".join(lines)


def _drop(t: Template) -> str:
    return ""


Renderer = Callable[[Template], str]

#: Vorlage → (Behandlung, Darstellung). Die Behandlung dokumentiert docs/vorlagen.md.
RULES: dict[str, tuple[str, Renderer]] = {
    "Zitat de §": ("Normzitat", _norm_paragraph),
    "Zitat-dej": ("Normzitat", _norm_dejure),
    "Zitat Art": ("Normzitat", _norm_article),
    "Rspr": ("Entscheidungszitat", _decision),
    "Quelle Wikipedia": ("Text (Quellenhinweis)", _quelle_wikipedia),
    "Infobox Publikation": ("Text (Felder)", _infobox),
    "ISSN": ("Text", lambda t: f"ISSN {_arg(t, 1)}"),
    "TOC": ("verwerfen (Layout)", _drop),
    "Prettytable-R Gesetz": ("verwerfen (Layout)", _drop),
}


def render_template(t: Template, page_title: str) -> str:
    """Text, den die Vorlage im Wiki erzeugt; unbekannte Vorlagen wörtlich."""
    name = canonical_name(str(t.name))
    if name == "PAGENAME":
        return page_title
    rule = RULES.get(name)
    return rule[1](t) if rule else str(t)


@dataclass
class TemplateUsage:
    name: str
    count: int
    pages: int
    examples: list[str] = field(default_factory=list)
    treatment: str = "unbekannt"

    @property
    def known(self) -> bool:
        return self.name == "PAGENAME" or self.name in RULES


def inventory(pages: list[RawPage], max_examples: int = 3) -> list[TemplateUsage]:
    """Alle verwendeten Vorlagen, häufigste zuerst."""
    counts: Counter = Counter()
    where: dict[str, set[int]] = defaultdict(set)
    examples: dict[str, list[str]] = defaultdict(list)
    for page in pages:
        for t in mwparserfromhell.parse(page.wikitext).filter_templates():
            name = canonical_name(str(t.name))
            counts[name] += 1
            where[name].add(page.pageid)
            if len(examples[name]) < max_examples:
                examples[name].append(" ".join(str(t).split())[:120])
    result = []
    for name, count in sorted(counts.items(), key=lambda x: (-x[1], x[0])):
        treatment = "Seitentitel" if name == "PAGENAME" else RULES.get(name, ("unbekannt",))[0]
        result.append(TemplateUsage(name, count, len(where[name]), examples[name], treatment))
    return result


def inventory_report(usages: list[TemplateUsage]) -> str:
    unknown = [u for u in usages if not u.known]
    out = ["# Vorlagen-Inventur", "",
           f"- Vorlagen: {len(usages)}, Vorkommen: {sum(u.count for u in usages)}",
           f"- Unbekannte Vorlagen: {len(unknown)} (bleiben wörtlich im Text, Regel ergänzen)",
           "", "| Vorlage | Vorkommen | Seiten | Behandlung | Beispiel |", "|---|---|---|---|---|"]
    for u in usages:
        example = (u.examples[0] if u.examples else "").replace("|", "\\|")
        out.append(f"| {u.name} | {u.count} | {u.pages} | {u.treatment} | `{example}` |")
    return "\n".join(out) + "\n"
