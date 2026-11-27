"""Entscheidungszitate erkennen (siehe GLOSSARY.md: Entscheidungszitat).

Zwei Quellen:
- ``{{Rspr|…}}``-Vorlagen: Aktenzeichen oder amtliche Fundstelle, ohne Gericht.
- Fließtext: „Gericht, Art vom Datum – Aktenzeichen“ in vielen Schreibweisen.

Kennung: Aktenzeichen von BGH, BVerfG und BSG sind allein eindeutig
(``XII ZB 152/10``, ``2 BvR 2115/01``, ``B 8 SO 29/10``). Aktenzeichen anderer
Gerichte (``1 T 5/11``) sind es nur zusammen mit dem Gericht.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, replace

from lexikon.templates import canonical_name

MONTHS = {m: i for i, m in enumerate(
    ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August",
     "September", "Oktober", "November", "Dezember"], start=1)}

_PLACE = r"[A-ZÄÖÜ][\wäöüß.-]*(?:/[A-ZÄÖÜ][\wäöüß.-]*)?(?:\s(?:I{1,3}|am\sMain|an\sder\s\w+))?"
_COURT = (
    r"(?P<gericht>Kammergericht(?:\sBerlin)?|BVerfG|BVerwG|BayObLG|BGH|BSG|BFH|BAG|KG|EuGH|EGMR"
    rf"|(?:OLG|LG|AG|LSG|SG|VG|OVG|VGH|FG|LAG|ArbG)(?:\s(?!vom\b|v\.)(?:{_PLACE}))?)(?!\w)"
)
_ART = r"(?P<art>Beschluss|Beschl\.?|Urteil|Urt\.?)"
_DATE = (
    r"(?P<datum>\d{1,2}\.\s?\d{1,2}\.\s?(?:\d{4}|\d{2})\b"
    rf"|\d{{1,2}}\.\s?(?:{'|'.join(MONTHS)})\s\d{{4}})"
)
# Aktenzeichen: optional Registerzahl und römischer Senat/Abteilung, dann Register und Nummer/Jahr.
_AZ = (
    r"(?P<az>(?:\d+\s)?(?:[IVX]+[a-z]?\s)?(?:[BLS]\s\d+[a-z]?\s)?"
    r"(?:\d\s)?[A-Z][A-Za-z]{0,3}\s?\d+/\d{2,4}(?:\s?R\b)?"
    r"|(?:\d+\s)?[IVX]+\s\d+/\d{2,4})"
)
_PATTERN = re.compile(
    rf"\b{_COURT},?\s*(?:{_ART}\s*)?(?:(?:vom|v\.)\s*{_DATE})?[\s,;:–-]*(?:Az\.?:?\s*)?{_AZ}"
)
_FEDERAL_AZ = re.compile(r"^(?:[IVX]+[a-z]?\s[A-Z]|\d\sBv[A-Z]\s|B\s\d+[a-z]?\s)")
_FUNDSTELLE = re.compile(r"^(?P<slg>BVerfGE|BGHZ|BGHSt|BSGE|BVerwGE)\s\d+,\s?\d+")
SLG_COURT = {"BVerfGE": "BVerfG", "BGHZ": "BGH", "BGHSt": "BGH", "BSGE": "BSG", "BVerwGE": "BVerwG"}


@dataclass(frozen=True)
class DecisionRef:
    gericht: str | None = None
    art: str | None = None
    datum: str | None = None  # ISO yyyy-mm-dd
    az: str | None = None
    fundstelle: str | None = None

    @property
    def id(self) -> str:
        if self.az:
            if _FEDERAL_AZ.match(self.az) or not self.gericht:
                return self.az
            return f"{self.gericht} {self.az}"
        return self.fundstelle or ""

    @property
    def label(self) -> str:
        head = ", ".join(p for p in [self.gericht, self.art] if p)
        if self.datum:
            y, m, d = self.datum.split("-")
            head = f"{head} vom {d}.{m}.{y}" if head else f"vom {d}.{m}.{y}"
        tail = self.az or self.fundstelle or ""
        if not head:
            return tail
        return f"{head} – {tail}" if self.az else f"{head}, {tail}"


def _iso(datum: str | None) -> str | None:
    if not datum:
        return None
    if m := re.fullmatch(r"(\d{1,2})\.\s?(\d{1,2})\.\s?(\d{2}|\d{4})", datum):
        d, mo, y = (int(x) for x in m.groups())
    else:
        d_s, mo_s, y_s = re.fullmatch(r"(\d{1,2})\.\s?(\S+)\s(\d{4})", datum).groups()
        d, mo, y = int(d_s), MONTHS[mo_s], int(y_s)
    if y < 100:
        y += 2000 if y < 50 else 1900
    return f"{y:04d}-{mo:02d}-{d:02d}"


def _court(name: str) -> str:
    if name.startswith("Kammergericht"):
        return "KG"
    name = " ".join(name.split())
    # „LG Lübeck.“ (Tippfehler im Wiki) ohne Punkt; Abkürzungen wie „Frankfurt/M.“ behalten
    return name[:-1] if name.endswith(".") and "/" not in name else name


def _art(art: str | None) -> str | None:
    if not art:
        return None
    return "Beschluss" if art.startswith("Beschl") else "Urteil"


def _court_for_az(az: str) -> str | None:
    if re.match(r"^[IVX]+[a-z]?\s[A-Z]", az):
        return "BGH"
    if re.match(r"^\d\sBv[A-Z]\s", az):
        return "BVerfG"
    if re.match(r"^B\s\d", az):
        return "BSG"
    return None


def parse_decisions(text: str) -> list[DecisionRef]:
    """Entscheidungszitate mit Gericht aus Fließtext, ohne Dubletten."""
    found: dict[str, DecisionRef] = {}
    for m in _PATTERN.finditer(text):
        ref = DecisionRef(_court(m.group("gericht")), _art(m.group("art")), _iso(m.group("datum")),
                          " ".join(m.group("az").split()))
        found.setdefault(ref.id, ref)
    return list(found.values())


def decisions_from_templates(code) -> list[DecisionRef]:
    """Entscheidungszitate aus ``{{Rspr|…}}``-Vorlagen."""
    found: dict[str, DecisionRef] = {}
    for t in code.filter_templates():
        if canonical_name(str(t.name)) != "Rspr" or not t.has(1):
            continue
        value = " ".join(str(t.get(1).value).split())
        if m := _FUNDSTELLE.match(value):
            ref = DecisionRef(gericht=SLG_COURT[m.group("slg")], fundstelle=m.group(0))
        elif value:
            ref = DecisionRef(gericht=_court_for_az(value), az=value)
        else:
            continue
        found.setdefault(ref.id, ref)
    return list(found.values())


def _fill(a: DecisionRef, b: DecisionRef) -> DecisionRef:
    return replace(a, **{f: getattr(b, f) for f in ("gericht", "art", "datum")
                         if getattr(a, f) is None and getattr(b, f) is not None})


def merge_decisions(refs: list[DecisionRef]) -> list[DecisionRef]:
    """Führt Zitate derselben Entscheidung zusammen.

    Ein Vorlagenzitat ohne Gericht (``19 T 529/02``) wird dem Fließtextzitat mit
    gleichem Aktenzeichen zugeschlagen (``LG Frankfurt/Oder 19 T 529/02``).
    """
    by_id: dict[str, DecisionRef] = {}
    for r in refs:
        by_id[r.id] = _fill(by_id[r.id], r) if r.id in by_id else r
    with_court = {r.az for r in by_id.values() if r.az and r.id != r.az}
    return [r for r in by_id.values() if not (r.az and r.id == r.az and r.az in with_court)]
