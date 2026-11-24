"""Normzitate erkennen und kanonisieren (siehe GLOSSARY.md: Normzitat, Norm).

Zwei Quellen:
- Zitat-Vorlagen (``Zitat de §``, ``Zitat-dej``, ``Zitat Art``): Paragraph und
  Gesetz stehen zerlegt in den Parametern; das Gesetz als URL-Kürzel.
- Fließtext: ``§ 42 Abs. 1 Nr. 2 SGB XII``, ``§§ 99, 104 FamFG``. Erkannt wird nur,
  wenn das Gesetzeskürzel direkt hinter der Zitatkette steht. Verweise mit
  vorangestelltem Gesetz (``BGB § 1833``) oder über ``i.V.m.`` hinweg werden
  bewusst nicht zugeordnet, weil das Gesetz dort mehrdeutig ist.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from lexikon.templates import canonical_name

LAWS = [
    "AGG", "AMG", "AO", "AsylbLG", "AufenthG", "BDSG", "BeurkG", "BGB", "BNotO", "BRAO",
    "BSHG", "BtBG", "BtOG", "BtRegV", "BVormVG", "DSGVO", "EGBGB", "EGGVG", "EStG", "FamFG",
    "FGG", "GBO", "GG", "GNotKG", "GVG", "HeimG", "HGB", "InsO", "JVEG", "KostO", "LFGG",
    "LPartG", "NamÄndG", "PAuswG", "PsychKG", "PsychKHG", "PStG", "RPflG", "RVG", "SGG",
    "StGB", "StPO", "StVollzG", "UStG", "VBVG", "VVG", "VwGO", "VwVfG", "VwZG", "WBVG",
]
#: Schreibvarianten im Fließtext → kanonisches Kürzel
TEXT_VARIANTS = {"RpflG": "RPflG", "RpflgG": "RPflG"}
#: URL-Kürzel von gesetze-im-internet.de/dejure.org, die nicht dem Kürzel entsprechen
SLUG_LAWS = {"bgbeg": "EGBGB", "persstg": "PStG", "nam_ndg": "NamÄndG"}

ROMAN = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII", "XIV"]
_BY_LOWER = {law.lower(): law for law in LAWS}

_UNIT = r"(?:§§?|Art\.)"
_NUM = r"\d+[a-z]?\b"
_SUB = r"(?:Abs\.|Absatz|Satz|S\.|Nr\.|Nummer|Ziff\.|Ziffer|Buchst\.|lit\.|Alt\.|Halbs\.)"
_TOKEN = rf"(?:{_UNIT}|{_SUB}|{_NUM}|und|u\.|bis|oder|ff\.|f\.|[,–-])"
_SGB = r"SGB[  -]?(?P<sgb>XIV|XIII|XII|XI|X|IX|VIII|VII|VI|V|IV|III|II|I|1[0-4]|[1-9])"
_NAMES = sorted(LAWS + list(TEXT_VARIANTS), key=len, reverse=True)
_LAW = rf"(?:{_SGB}|(?P<name>{'|'.join(map(re.escape, _NAMES))}))"
_PATTERN = re.compile(
    rf"(?P<chain>{_UNIT}\s*{_NUM}(?:\s*{_TOKEN})*?)\s*{_LAW}(?![\w-])(?P<af>\s*a\.\s?F\.)?"
)
_TOKENS = re.compile(rf"(?P<unit>{_UNIT})|(?P<sub>{_SUB})|(?P<num>{_NUM})")


@dataclass(frozen=True)
class NormRef:
    gesetz: str
    einheit: str  # "§" oder "Art."
    nummer: str
    alte_fassung: bool = False

    @property
    def id(self) -> str:
        return f"{self.gesetz.replace(' ', '')}{self.einheit}{self.nummer}"

    @property
    def label(self) -> str:
        return f"{self.einheit} {self.nummer} {self.gesetz}"


def _sgb(numeral: str) -> str:
    return f"SGB {ROMAN[int(numeral)] if numeral.isdigit() else numeral}"


def canonical_law(slug: str) -> str:
    """URL-Kürzel (``sgb_12``, ``vbvg_2023``, ``bgbeg``) → kanonisches Gesetzeskürzel."""
    s = slug.strip()
    low = re.sub(r"_\d{4}$", "", s.lower())
    if low in SLUG_LAWS:
        return SLUG_LAWS[low]
    if m := re.fullmatch(r"sgb_?([ivx]+|\d{1,2})", low):
        return _sgb(m.group(1).upper())
    return _BY_LOWER.get(low, s.upper())


def _units(chain: str) -> list[tuple[str, str]]:
    result, unit, mode = [], None, None
    for m in _TOKENS.finditer(chain):
        if m.group("unit"):
            unit, mode = ("Art." if m.group("unit") == "Art." else "§"), "para"
        elif m.group("sub"):
            mode = "sub"
        elif m.group("num") and mode == "para":
            result.append((unit, m.group("num")))
    return result


def parse_norms(text: str) -> list[NormRef]:
    """Normzitate aus Fließtext in Reihenfolge des Auftretens, ohne Dubletten."""
    found: dict[str, NormRef] = {}
    for m in _PATTERN.finditer(text):
        law = _sgb(m.group("sgb")) if m.group("sgb") else TEXT_VARIANTS.get(m.group("name"), m.group("name"))
        for unit, number in _units(m.group("chain")):
            ref = NormRef(law, unit, number, bool(m.group("af")))
            found.setdefault(ref.id, ref)
    return list(found.values())


def _arg(t, key) -> str:
    return str(t.get(key).value).strip() if t.has(key) else ""


def norms_from_templates(code) -> list[NormRef]:
    """Normzitate aus den Zitat-Vorlagen eines geparsten Wikitexts."""
    found: dict[str, NormRef] = {}
    for t in code.filter_templates():
        name = canonical_name(str(t.name))
        if name == "Zitat de §":
            unit, number, slug = "§", _arg(t, 1), _arg(t, 2)
        elif name == "Zitat Art":
            unit, number, slug = "Art.", _arg(t, 1), _arg(t, 2)
        elif name == "Zitat-dej":
            unit = "Art." if _arg(t, 1).startswith("Art") else "§"
            number, slug = _arg(t, 2), _arg(t, 3)
        else:
            continue
        m = re.match(_NUM, number)
        if not (m and slug):
            continue
        ref = NormRef(canonical_law(slug), unit, m.group(0))
        found.setdefault(ref.id, ref)
    return list(found.values())
