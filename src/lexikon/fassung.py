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

from lexikon.norms import _PATTERN, NormRef, _units

REFORM_START, LAST_CURRENT, REFORM_END = 1773, 1888, 1921
#: Im alten Recht weggefallen (Familienrat, aufgehoben 1980): ein Zitat meint neues Recht.
VACANT_OLD = range(1858, 1882)
REFORM_DATE = "2023-01-01"

_OLD_TEXT = re.compile(r"bis (?:zum )?31\.12\.2022|\balte[nmr]? (?:Recht|Fassung)\b|\bbisherige[nmr]? Recht\b",
                       re.IGNORECASE)
# Nur Formulierungen, die eindeutig die Reform 2023 meinen. „n.F.“ oder „nach neuem Recht“
# allein treffen auch FamFG 2009, BTHG (SGB IX n.F.) oder Aufsätze von 1991.
_NEW_TEXT = re.compile(
    r"\b(?:ab|seit) (?:dem )?1\.\s?1\.\s?(?:20)?23\b|\bneue[nmr]? Betreuungsrecht"
    r"|Reform des Vormundschafts- und Betreuungsrechts|Betreuungsrechtsreform 2023",
    re.IGNORECASE)


def _number(ref: NormRef) -> int | None:
    if ref.gesetz != "BGB" or ref.einheit != "§":
        return None
    m = re.match(r"\d+", ref.nummer)
    return int(m.group(0)) if m else None


def in_reform_range(ref: NormRef) -> bool:
    n = _number(ref)
    return n is not None and REFORM_START <= n <= REFORM_END


def _vacant_old(ref: NormRef) -> bool:
    n = _number(ref)
    return n is not None and n in VACANT_OLD and ref.nummer.isdigit()


def chain_old_numbers(text: str) -> set[str]:
    """Nummern aus Zitatketten, die eine seit 2023 nicht mehr bestehende Nummer enthalten.

    „§§ 1908i Abs. 1 Satz 1, 1821, 1822 BGB“ ist eine Verweisung des alten Rechts; § 1821 und
    § 1822 meinen dort die alte Fassung.
    """
    result: set[str] = set()
    for m in _PATTERN.finditer(text):
        if m.group("name") != "BGB":
            continue
        nums = [n for unit, n in _units(m.group("chain")) if unit == "§"]
        refs = [NormRef("BGB", "§", n) for n in nums]
        if any(_old_only(r) for r in refs):
            result.update(r.nummer for r in refs if in_reform_range(r))
    return result


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
    rows = csv.DictReader((l for l in text.splitlines() if l.strip() and not l.startswith("#")), delimiter=";")
    mapping: dict[str, list[str]] = {}
    for row in rows:
        old, new = row["alt"].strip(), row["neu"].strip()
        if not (re.fullmatch(r"\d+[a-z]?", old) and re.fullmatch(r"\d+[a-z]?", new)):
            raise ValueError(f"Ungültige Zeile in reform2023_bgb.csv: {row}")
        if new not in mapping.setdefault(old, []):
            mapping[old].append(new)
    return mapping


def section_signal(refs: list[NormRef], text: str, decision_dates: list[str]) -> str | None:
    """``alt``/``neu``, wenn der Abschnitt eindeutig auf eine Fassung hinweist, sonst None."""
    old = (any(r.alte_fassung or _old_only(r) or r.gesetz == "FGG" for r in refs)
           or bool(_OLD_TEXT.search(text))
           or any(d < REFORM_DATE for d in decision_dates))  # jede Entscheidung vor 2023
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

    Vorrang: Nummern, die es nur alt oder nur neu gibt (§§ 1889–1921, Buchstaben → alt;
    §§ 1858–1881, im alten Recht weggefallen → neu); Hinweis direkt am Zitat („a.F.“, „früher“
    → alt; „jetzt“, „neuen“, „n.F.“ → neu); Kette mit einer nur alten Nummer → alt; dann Nachfolger-Regel (steht im Abschnitt eine alte Norm zusammen mit ihrem Nachfolger
    laut Synopse, ist das ein Vergleich und der Nachfolger meint die neue Fassung); dann ein
    Abschnittssignal „neu“; sonst unbestimmt.

    Ein Abschnittssignal „alt“ macht ein doppeldeutiges Zitat bewusst NICHT alt: Die meisten
    Artikel sind auf das neue Recht umgestellt und nennen altes Recht, alte Rechtsprechung
    oder „bis zum 31.12.2022“ nur zum Vergleich. In einer Stichprobe vom 27.11.2026 war die
    Einordnung „alt“ aus dem Abschnittskontext nur bei etwa 5 von 12 Zitaten richtig.
    """
    mapping = load_mapping()
    in_old_chain = chain_old_numbers(text) if text else set()
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
        if _vacant_old(r):
            result.append(r)
            continue
        local = _local_marker(text, r.nummer) if text else None
        if local:
            decided = local
        elif r.nummer in in_old_chain:
            decided = "alt"
        elif r.nummer in successors or signal == "neu":
            decided = "neu"
        else:
            decided = None
        if decided == "alt":
            result.append(replace(r, alte_fassung=True))
        elif decided == "neu":
            result.append(r)
        else:
            result.append(replace(r, unbestimmt=True))
    return result
