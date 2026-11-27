"""Rohseite → Artikel: Abschnitte mit Pfad und typisierte Links."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

import mwparserfromhell
from mwparserfromhell.nodes import (
    Comment, ExternalLink, Heading, HTMLEntity, Tag, Template, Text, Wikilink,
)

from lexikon.links import classify, slug
from lexikon.models import RawPage
from lexikon.decisions import (DecisionRef, completeness, decisions_from_templates, merge_decisions,
                               parse_decisions)
from lexikon.norms import NORM_TEMPLATES, NormRef, norms_from_templates, parse_norms
from lexikon.templates import canonical_name, render_template

INTRO = "Einleitung"
REDIRECT_RE = re.compile(r"^\s*#\s*(?:weiterleitung|redirect)\s*:?\s*\[\[([^\]|]+)", re.IGNORECASE)


CATEGORY_SLUG_PREFIXES = ("kategorie:", "category:")


def target_category_name(redirects: dict[str, str], key: str) -> str:
    """Kategoriename aus dem aufgelösten Slug, Anfangsbuchstabe groß."""
    name = resolve(key, redirects).split(":", 1)[1].replace("-", " ")
    return name[:1].upper() + name[1:]


@dataclass
class Section:
    path: tuple[str, ...]
    text: str
    norms: list[str] = field(default_factory=list)
    decisions: list[str] = field(default_factory=list)


@dataclass
class Article:
    pageid: int
    title: str
    slug: str
    revid: int
    timestamp: str
    categories: list[str]
    sections: list[Section] = field(default_factory=list)
    internal_links: list[str] = field(default_factory=list)
    wikipedia_links: list[str] = field(default_factory=list)
    images: list[str] = field(default_factory=list)
    external_links: list[str] = field(default_factory=list)
    category_links: list[str] = field(default_factory=list)
    dead_links: list[str] = field(default_factory=list)
    norms: list[dict] = field(default_factory=list)
    decisions: list[dict] = field(default_factory=list)

    def to_json(self) -> dict:
        d = dict(self.__dict__)
        d["sections"] = [{"path": list(s.path), "text": s.text, "norms": s.norms,
                          "decisions": s.decisions} for s in self.sections]
        return d


def _clean_target(target: str) -> str:
    return target.strip().lstrip(":").split("#", 1)[0].strip()


def redirect_target(page: RawPage) -> str | None:
    """Ziel einer Weiterleitungsseite (ohne Anker) oder None.

    Erkennt ``#WEITERLEITUNG``/``#REDIRECT`` mit und ohne Doppelpunkt. Meldet
    die API eine Weiterleitung mit anderem Zauberwort, gilt der erste Link.
    """
    m = REDIRECT_RE.match(page.wikitext)
    if m:
        return _clean_target(m.group(1)) or None
    if page.is_redirect:
        links = mwparserfromhell.parse(page.wikitext).filter_wikilinks()
        if links:
            return _clean_target(str(links[0].title)) or None
    return None


def is_content(page: RawPage) -> bool:
    """Seite mit eigenem Inhalt, also keine Weiterleitung."""
    return not page.is_redirect and redirect_target(page) is None


def build_redirect_map(pages: list[RawPage], unreadable: list[dict] = ()) -> dict[str, str]:
    """Slug der Weiterleitung → Slug des direkten Ziels.

    Inhaltsseiten haben Vorrang: Hat eine Weiterleitung denselben Slug wie ein
    Artikel (z. B. Titel mit Soft-Hyphens), wird sie ignoriert. Für Seiten ohne
    abrufbare Revision dient ``redirect_to`` aus der Weiterleitungstabelle.
    """
    content = {slug(p.title) for p in pages if is_content(p)}
    candidates = [(p.title, redirect_target(p)) for p in pages if not is_content(p)]
    candidates += [(u["title"], u.get("redirect_to")) for u in unreadable]
    result = {}
    for title, target in candidates:
        source = slug(title)
        if target and source not in content and slug(target) != source:
            result[source] = slug(target)
    return result


def resolve(key: str, redirects: dict[str, str]) -> str | None:
    """Folgt Weiterleitungsketten; None bei einer Schleife."""
    seen = set()
    while key in redirects:
        if key in seen:
            return None
        seen.add(key)
        key = redirects[key]
    return key


#: Platzhalter für Norm-Vorlagen beim Parsen des Fließtexts: unterbricht Zitatketten,
#: damit „{{Zitat de §|8|vbvg}} VBVG“ nicht zusätzlich als aktuelles § 8 VBVG zählt.
MASK = "\u2063"


def _render(nodes, title: str = "", mask_norms: bool = False) -> str:
    out = []
    for node in nodes:
        if isinstance(node, Text):
            out.append(node.value)
        elif isinstance(node, Wikilink):
            kind, target = classify(str(node.title))
            if kind in ("image", "category"):
                continue
            if node.text is not None:
                out.append(_render(node.text.nodes, title, mask_norms))
            elif kind == "wikipedia":
                out.append(target.split(":", 1)[-1])
            else:
                out.append(target)
        elif isinstance(node, ExternalLink):
            out.append(_render(node.title.nodes, title, mask_norms) if node.title else str(node.url))
        elif isinstance(node, Tag):
            if node.tag in ("br",):
                out.append("\n")
            elif node.tag == "li":
                out.append("-")
            elif node.contents is not None:
                inner = _render(node.contents.nodes, title, mask_norms)
                if node.tag != "ref":
                    out.append(inner)
                elif inner.strip():
                    out.append(f" [{inner.strip()}]")
        elif isinstance(node, Comment):
            continue
        elif isinstance(node, HTMLEntity):
            out.append(node.normalize())
        elif isinstance(node, Template):
            if mask_norms and canonical_name(str(node.name)) in NORM_TEMPLATES:
                out.append(MASK)
            else:
                out.append(render_template(node, title))
        else:
            out.append(str(node))
    return "".join(out)


def _clean(text: str) -> str:
    lines = [line.rstrip() for line in text.splitlines()]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def _section_norms(nodes: list, title: str) -> list[NormRef]:
    """Normzitate aus Vorlagen und Fließtext; Vorlagen werden nicht doppelt gezählt."""
    found: dict[str, NormRef] = {}
    code = mwparserfromhell.parse("".join(str(n) for n in nodes))
    for ref in norms_from_templates(code) + parse_norms(_render(nodes, title, mask_norms=True)):
        found.setdefault(ref.id, ref)
    return list(found.values())


def _section_decisions(nodes: list, title: str) -> list[DecisionRef]:
    code = mwparserfromhell.parse("".join(str(n) for n in nodes))
    return merge_decisions(parse_decisions(_render(nodes, title)) + decisions_from_templates(code))


def _sections(code, title: str) -> list[tuple[Section, list[NormRef], list[DecisionRef]]]:
    sections: list[tuple[Section, list[NormRef], list[DecisionRef]]] = []
    stack: list[tuple[int, str]] = []
    path: tuple[str, ...] = (INTRO,)
    heading: list = []
    buf: list = []

    def flush():
        text = _clean(_render(buf, title))
        if text:
            nodes = heading + [Text("\n")] + buf
            refs = _section_norms(nodes, title)
            decs = _section_decisions(nodes, title)
            sections.append((Section(path, text, [r.id for r in refs], [d.id for d in decs]), refs, decs))

    for node in code.nodes:
        if isinstance(node, Heading):
            flush()
            buf = []
            heading = list(node.title.nodes)
            while stack and stack[-1][0] >= node.level:
                stack.pop()
            stack.append((node.level, " ".join(_render(heading, title).split())))
            path = tuple(t for _, t in stack)
        else:
            buf.append(node)
    flush()
    return sections


def normalize(page: RawPage, redirects: dict[str, str], known: set[str]) -> Article:
    """Übersetzt eine (Nicht-Weiterleitungs-)Rohseite in einen Artikel."""
    code = mwparserfromhell.parse(page.wikitext)
    internal, dead, wiki, images, cat_links = set(), set(), [], [], []
    for link in code.filter_wikilinks():
        kind, target = classify(str(link.title))
        if kind == "internal":
            if not target:
                continue
            key = slug(target)
            resolved = resolve(key, redirects)
            if resolved in known:
                internal.add(resolved)
            elif resolved and resolved.startswith(CATEGORY_SLUG_PREFIXES):
                cat_links.append(target_category_name(redirects, key))
            else:
                dead.add(key)
        elif kind == "wikipedia":
            wiki.append(target)
        elif kind == "image":
            images.append(target)
        elif kind == "category-link":
            cat_links.append(target)
    external = [str(l.url) for l in code.filter_external_links()]
    own = slug(page.title)
    internal.discard(own)
    sections = _sections(code, page.title)
    norms: dict[str, dict] = {}
    decisions: dict[str, dict] = {}
    for _, _, decs in sections:
        for dref in decs:
            decisions.setdefault(dref.id, {"id": dref.id, "label": dref.label, "gericht": dref.gericht,
                                           "art": dref.art, "datum": dref.datum, "az": dref.az,
                                           "fundstelle": dref.fundstelle})
    for _, refs, _ in sections:
        for r in refs:
            norms.setdefault(r.id, {"id": r.id, "label": r.label, "gesetz": r.gesetz,
                                    "einheit": r.einheit, "nummer": r.nummer,
                                    "alte_fassung": r.alte_fassung})
    return Article(
        pageid=page.pageid,
        title=page.title,
        slug=own,
        revid=page.revid,
        timestamp=page.timestamp,
        categories=list(page.categories),
        sections=[sec for sec, _, _ in sections],
        internal_links=sorted(internal),
        wikipedia_links=sorted(set(wiki)),
        images=sorted(set(images)),
        external_links=sorted(set(external)),
        category_links=sorted(set(cat_links)),
        dead_links=sorted(dead),
        norms=[norms[k] for k in sorted(norms)],
        decisions=[decisions[k] for k in sorted(decisions)],
    )


def unify_decisions(articles: list[Article]) -> None:
    """Vereinheitlicht Entscheidungszitate über alle Artikel (ändert die Artikel).

    - Ein Zitat ohne Gericht (nur Aktenzeichen) wird dem einzigen Zitat mit Gericht
      und gleichem Aktenzeichen zugeordnet; bei mehreren Kandidaten bleibt es offen.
    - Je Entscheidung gelten die Angaben des vollständigsten Zitats (Gericht, Art,
      Datum), damit Knoten, Artikel und Bericht dieselbe Bezeichnung tragen.
    """
    best: dict[str, dict] = {}
    for a in articles:
        for d in a.decisions:
            if d["id"] not in best or completeness(d) > completeness(best[d["id"]]):
                best[d["id"]] = d
    qualified: dict[str, set[str]] = {}
    for i, d in best.items():
        if d["az"] and i != d["az"]:
            qualified.setdefault(re.sub(r"\sR$", "", d["az"]), set()).add(i)
    remap = {i: next(iter(qualified[i])) for i, d in best.items()
             if d["az"] and i == re.sub(r"\sR$", "", d["az"]) and len(qualified.get(i, ())) == 1}
    for a in articles:
        ids = sorted({remap.get(d["id"], d["id"]) for d in a.decisions})
        a.decisions = [best[i] for i in ids]
        for sec in a.sections:
            sec.decisions = list(dict.fromkeys(remap.get(i, i) for i in sec.decisions))
