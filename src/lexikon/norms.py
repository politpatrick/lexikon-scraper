"""Normzitate erkennen und kanonisieren (siehe GLOSSARY.md: Normzitat, Norm).

Zwei Quellen:
- Zitat-Vorlagen (``Zitat de §``, ``Zitat-dej``, ``Zitat Art``): Paragraph und
  Gesetz stehen zerlegt in den Parametern; das Gesetz als URL-Kürzel.
- Fließtext: ``§ 42 Abs. 1 Nr. 2 SGB XII``, ``§§ 99, 104 FamFG``. Erkannt wird nur,
  wenn das Gesetzeskürzel direkt hinter der Zitatkette steht. Verweise mit
  vorangestelltem Gesetz (``BGB § 1833``) oder über ``i.V.m.`` hinweg werden
  bewusst nicht zugeordnet, weil das Gesetz dort mehrdeutig ist.

Die alte Fassung (``a.F.``) ist Teil der ID: § 1822 BGB a.F. und § 1822 BGB
regeln nach der Reform 2023 verschiedene Dinge und sind verschiedene Knoten.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from lexikon.templates import canonical_name

LAWS = [
    "AGG", "AMG", "AO", "AsylbLG", "AufenthG", "BDSG", "BeurkG", "BGB", "BNotO", "BRAO",
    "BSHG", "BtÄndG", "BtBG", "BtOG", "BtRegV", "BVormVG", "DSGVO", "EGBGB", "EGGVG", "EStG",
    "FamFG", "FGG", "GBO", "GG", "GNotKG", "GVG", "HeimG", "HGB", "InsO", "JVEG", "KJHG",
    "KostO", "LFGG", "LPartG", "NamÄndG", "PAuswG", "PsychKG", "PsychKHG", "PStG", "RPflG",
    "RVG", "SGG", "StGB", "StPO", "StVollzG", "UN-BRK", "UStG", "VBVG", "VVG", "VwGO",
    "VwVfG", "VwZG", "WBVG", "ZPO",
]
#: Schreibvarianten im Fließtext → kanonisches Kürzel
TEXT_VARIANTS = {"RpflG": "RPflG", "RpflgG": "RPflG"}
#: URL-Kürzel von gesetze-im-internet.de/dejure.org, die nicht dem Kürzel entsprechen
SLUG_LAWS = {"bgbeg": "EGBGB", "persstg": "PStG", "nam_ndg": "NamÄndG", "btgb": "BtBG"}
#: URL-Kürzel, die auf die bis 31.12.2022 geltende Fassung zeigen (``vbvg`` vs. ``vbvg_2023``)
OLD_VERSION_SLUGS = {"vbvg"}

ROMAN = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII", "XIV"]
_BY_LOWER = {law.lower(): law for law in LAWS}

# Bausteine. ``§§?(?!§)`` und die atomaren Gruppen verhindern exponentielles Backtracking,
# die Kettenlänge ist begrenzt.
_UNIT = r"(?:§§?(?!§)|Art\.)"
_NUM = r"\d+[a-z]?\b"
_SUB = r"(?:Abs\.|Abs\b|Absatz|Satz|S\.|Nr\.|Nummer|Ziff\.|Ziffer|Buchst\.|lit\.|Alt\.|Halbs\.)"
_ROMAN_SUB = r"\b[IVX]{1,4}\b"
_SEP = r"(?:,|und\b|sowie\b|u\.)"
_TOKEN = rf"(?:{_UNIT}|{_SUB}|{_NUM}|{_SEP}|{_ROMAN_SUB}|bis\b|oder\b|ff\.?|f\.|[–-])"
_SGB = r"SGB[  -]?(?P<sgb>XIV|XIII|XII|XI|X|IX|VIII|VII|VI|V|IV|III|II|I|1[0-4]|[1-9])"
_NAMES = sorted(LAWS + list(TEXT_VARIANTS), key=len, reverse=True)
_LAW = rf"(?:{_SGB}|(?P<name>{'|'.join(map(re.escape, _NAMES))}))"
_AF = r"(?P<af>\s*\(?\s*(?:a\.\s?F\.?|aF|in der bis (?:zum )?31\.12\.2022 geltenden Fassung)(?!\w))?"
#: Leerraum mit höchstens einem Zeilenumbruch: Ketten laufen nicht über Absätze hinweg.
_WS = r"[^\S\n]*+(?:\n[^\S\n]*+)?"
_PATTERN = re.compile(
    rf"(?P<chain>{_UNIT}{_WS}{_NUM}(?:{_WS}(?>{_TOKEN})){{0,40}}?){_WS}{_LAW}(?![\w-]){_AF}"
)
_TOKENS = re.compile(
    rf"(?P<unit>{_UNIT})|(?P<sub>{_SUB}|{_ROMAN_SUB})|(?P<sep>{_SEP})|(?P<num>{_NUM})"
)


@dataclass(frozen=True)
class NormRef:
    gesetz: str
    einheit: str  # "§" oder "Art."
    nummer: str   # "1814", "1906a" oder zusammengesetzt "229 § 54" (Art. 229 § 54 EGBGB)
    alte_fassung: bool = False
    unbestimmt: bool = False  # Nummer gibt es alt und neu, Kontext entscheidet nicht (fassung.py)

    @property
    def id(self) -> str:
        base = f"{self.gesetz.replace(' ', '')}{self.einheit}{self.nummer.replace(' ', '')}"
        if self.alte_fassung:
            return base + "@aF"
        return base + ("@unbestimmt" if self.unbestimmt else "")

    @property
    def label(self) -> str:
        base = f"{self.einheit} {self.nummer} {self.gesetz}"
        if self.alte_fassung:
            return base + " a.F."
        return base + (" (alte oder neue Fassung)" if self.unbestimmt else "")

    @property
    def fassung(self) -> str | None:
        """``alt``, ``unbestimmt``, ``neu`` (Reformbereich ohne Hinweis auf alt) oder None."""
        if self.alte_fassung:
            return "alt"
        if self.unbestimmt:
            return "unbestimmt"
        from lexikon.fassung import LAST_CURRENT, REFORM_START
        if self.gesetz == "BGB" and self.einheit == "§" and self.nummer.isdigit():
            return "neu" if REFORM_START <= int(self.nummer) <= LAST_CURRENT else None
        return None


def _sgb(numeral: str) -> str:
    return f"SGB {ROMAN[int(numeral)] if numeral.isdigit() else numeral}"


def is_known_law(law: str) -> bool:
    return law in LAWS or law.startswith("SGB ")


def canonical_law(slug: str) -> str:
    """URL-Kürzel (``sgb_12``, ``vbvg_2023``, ``bgbeg``) → kanonisches Gesetzeskürzel.

    Unbekannte Kürzel werden großgeschrieben übernommen; der Qualitätsbericht listet sie.
    """
    s = slug.strip()
    low = re.sub(r"_\d{4}$", "", s.lower())
    if low in SLUG_LAWS:
        return SLUG_LAWS[low]
    if m := re.fullmatch(r"sgb_?([ivx]+|\d{1,2})", low):
        return _sgb(m.group(1).upper())
    return _BY_LOWER.get(low, s.upper())


def _units(chain: str) -> list[tuple[str, str]]:
    """Zerlegt eine Zitatkette in (Einheit, Nummer).

    Nach ``Abs.``/``Satz``/``Nr.`` gehören Zahlen zur Untergliederung. In ``§§``-Ketten
    beginnt nach einem Trenner (``,``/``und``) wieder ein Paragraph, außer die Zahl setzt
    die Untergliederung fort (``Abs. 2 und 3``); bei ``§`` nie (``§ 272 Abs. 2, 3`` meint
    Absätze). ``Art. 229 § 54`` ist eine zusammengesetzte Norm.
    """
    result: list[tuple[str, str]] = []
    unit, plural, mode, last_art = None, False, None, False
    last_sub: int | None = None
    after_sep = False
    for m in _TOKENS.finditer(chain):
        if m.group("unit"):
            token = m.group("unit")
            if token.startswith("§") and last_art and result:
                unit, mode = "compound", "para"
                continue
            unit = "Art." if token == "Art." else "§"
            plural, mode, last_art = token == "§§", "para", False
        elif m.group("sub"):
            mode, last_art, last_sub = "sub", False, None
        elif m.group("sep"):
            after_sep = True
            last_art = False
            continue
        elif m.group("num") and mode == "sub":
            digits = re.match(r"\d+", m.group("num")).group(0)
            continues = last_sub is not None and int(digits) == last_sub + 1
            if plural and after_sep and not continues:
                mode = "para"
            else:
                last_sub = int(digits)
        if m.group("num") and mode == "para":
            number = m.group("num")
            if unit == "compound":
                art = result.pop()
                result.append(("Art.", f"{art[1]} § {number}"))
                unit, mode, last_art = "§", "sub", False
            else:
                result.append((unit, number))
                last_art = unit == "Art."
            last_sub = None
        after_sep = False
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


NORM_TEMPLATES = {"Zitat de §", "Zitat Art", "Zitat-dej"}


def _arg(t, key) -> str:
    return str(t.get(key).value).strip() if t.has(key) else ""


def norm_from_template(t) -> NormRef | None:
    """Normzitat aus einer Zitat-Vorlage, sonst None."""
    name = canonical_name(str(t.name))
    if name == "Zitat de §":
        unit, number, slug = "§", _arg(t, 1), _arg(t, 2)
    elif name == "Zitat Art":
        unit, number, slug = "Art.", _arg(t, 1), _arg(t, 2)
    elif name == "Zitat-dej":
        unit = "Art." if _arg(t, 1).startswith("Art") else "§"
        number, slug = _arg(t, 2), _arg(t, 3)
    else:
        return None
    m = re.match(_NUM, number)
    if not (m and slug):
        return None
    return NormRef(canonical_law(slug), unit, m.group(0), slug.lower() in OLD_VERSION_SLUGS)


def norms_from_templates(code) -> list[NormRef]:
    """Normzitate aus den Zitat-Vorlagen eines geparsten Wikitexts."""
    found: dict[str, NormRef] = {}
    for t in code.filter_templates():
        if (ref := norm_from_template(t)) is not None:
            found.setdefault(ref.id, ref)
    return list(found.values())
