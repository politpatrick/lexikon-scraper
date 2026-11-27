"""Alte und neue Fassung des Betreuungsrechts (Reform zum 1.1.2023).

Die Reform hat die §§ 1773–1921 BGB vollständig neu geordnet:
- §§ 1889–1921 BGB und Buchstaben-Paragraphen wie § 1835a gibt es seit 2023 nicht mehr;
  ein Zitat meint immer die alte Fassung (geprüft mit Open Legal Data am 27.11.2026).
- §§ 1773–1888 BGB gibt es alt und neu mit anderem Inhalt (§ 1821 a.F.: Genehmigung von
  Grundstücksgeschäften; § 1821 n.F.: Wünsche des Betreuten). Ohne „a.F.“ entscheidet der
  Kontext des Abschnitts; ohne eindeutigen Kontext bleibt die Fassung „unbestimmt“.

Die Zuordnung alt → neu stammt aus der im Lexikon verlinkten Synopse
(``data/reform2023_bgb.csv``).
"""
from __future__ import annotations

import csv
import re
from dataclasses import replace
from functools import lru_cache
from importlib import resources

from lexikon.norms import NormRef

REFORM_START, LAST_CURRENT, REFORM_END = 1773, 1888, 1921
REFORM_DATE = "2023-01-01"

_OLD_TEXT = re.compile(r"bis (?:zum )?31\.12\.2022|\balte[nmr]? (?:Recht|Fassung)\b|\bbisherige[nmr]? Recht\b",
                       re.IGNORECASE)
_NEW_TEXT = re.compile(r"\b(?:ab|seit) (?:dem )?1\.\s?1\.\s?(?:20)?23\b|\bneue[nmr]? Recht\b|\bn\.\s?F\.",
                       re.IGNORECASE)


def _number(ref: NormRef) -> int | None:
    if ref.gesetz != "BGB" or ref.einheit != "§":
        return None
    m = re.match(r"\d+", ref.nummer)
    return int(m.group(0)) if m else None


def in_reform_range(ref: NormRef) -> bool:
    n = _number(ref)
    return n is not None and REFORM_START <= n <= REFORM_END


def _old_only(ref: NormRef) -> bool:
    """Nummern, die es seit 2023 nicht mehr gibt: §§ 1889–1921 und Buchstaben-Paragraphen
    in §§ 1773–1888 (§ 1835a, § 1836d …; die neue Zählung kennt dort keine Buchstaben)."""
    n = _number(ref)
    if n is None or not REFORM_START <= n <= REFORM_END:
        return False
    return n > LAST_CURRENT or not ref.nummer.isdigit()


@lru_cache(maxsize=1)
def load_mapping() -> dict[str, list[str]]:
    """Alte Paragraphennummer → Nachfolger in der neuen Fassung."""
    text = resources.files("lexikon").joinpath("data/reform2023_bgb.csv").read_text(encoding="utf-8")
    rows = csv.DictReader((l for l in text.splitlines() if not l.startswith("#")), delimiter=";")
    mapping: dict[str, list[str]] = {}
    for row in rows:
        mapping.setdefault(row["alt"], []).append(row["neu"])
    return mapping


def section_signal(refs: list[NormRef], text: str, decision_dates: list[str]) -> str | None:
    """``alt``/``neu``, wenn der Abschnitt eindeutig auf eine Fassung hinweist, sonst None."""
    old = (any(r.alte_fassung or _old_only(r) or r.gesetz == "FGG" for r in refs)
           or bool(_OLD_TEXT.search(text))
           or bool(decision_dates) and max(decision_dates) < REFORM_DATE)
    new = (any(r.gesetz == "BtOG" for r in refs)
           or bool(_NEW_TEXT.search(text))
           or bool(decision_dates) and min(decision_dates) >= REFORM_DATE)
    if old and not new:
        return "alt"
    if new and not old:
        return "neu"
    return None


_NEW_MARK = r"(?:jetzt|nunmehr|heute|neue[nmrs]?|neu gefasste[nmr]?)"
_OLD_MARK = r"(?:früher|vormals|ehemals|bisher|bisherige[nmr]?|alte[nmr]?)"


def _local_marker(text: str, nummer: str) -> str | None:
    """Hinweis direkt am Zitat: „jetzt § 1814“, „nach dem neuen § 1820“, „§ 1814 n.F.“."""
    new = old = False
    for m in re.finditer(rf"§§?\s?{re.escape(nummer)}(?![\w])", text):
        before = text[max(0, m.start() - 30):m.start()]
        after = text[m.end():m.end() + 30]
        if re.search(rf"\b{_NEW_MARK}\s+(?:dem\s+|den\s+|der\s+)?$", before, re.I) or re.match(
                r"[^§;]{0,20}?\bn\.\s?F\.", after):
            new = True
        if re.search(rf"\b{_OLD_MARK}\s+(?:dem\s+|den\s+|der\s+)?$", before, re.I):
            old = True
    if new and not old:
        return "neu"
    if old and not new:
        return "alt"
    return None


def apply_fassung(refs: list[NormRef], signal: str | None, text: str = "") -> list[NormRef]:
    """Ordnet Zitate aus §§ 1773–1921 BGB ohne „a.F.“ der Fassung zu.

    Vorrang: Hinweis direkt am Zitat („a.F.“, „früher“ → alt; „jetzt“, „neuen“, „n.F.“ → neu);
    dann Nachfolger-Regel (steht im Abschnitt eine alte Norm zusammen mit ihrem Nachfolger
    laut Synopse, ist das ein Vergleich und der Nachfolger meint die neue Fassung); dann ein
    Abschnittssignal „neu“; sonst unbestimmt.

    Ein Abschnittssignal „alt“ macht ein doppeldeutiges Zitat bewusst NICHT alt: Die meisten
    Artikel sind auf das neue Recht umgestellt und nennen altes Recht, alte Rechtsprechung
    oder „bis zum 31.12.2022“ nur zum Vergleich. In einer Stichprobe vom 27.11.2026 war die
    Einordnung „alt“ aus dem Abschnittskontext nur bei etwa 5 von 12 Zitaten richtig.
    """
    mapping = load_mapping()
    old_cited = {r.nummer for r in refs if in_reform_range(r) and (r.alte_fassung or _old_only(r))}
    successors = {new for old in old_cited for new in mapping.get(old, [])}
    result = []
    for r in refs:
        if r.alte_fassung or not in_reform_range(r):
            result.append(r)
            continue
        if _old_only(r):
            result.append(replace(r, alte_fassung=True))
            continue
        local = _local_marker(text, r.nummer) if text else None
        decided = local or ("neu" if r.nummer in successors or signal == "neu" else None)
        if decided == "alt":
            result.append(replace(r, alte_fassung=True))
        elif decided == "neu":
            result.append(r)
        else:
            result.append(replace(r, unbestimmt=True))
    return result
