"""Entscheidungszitate erkennen (siehe GLOSSARY.md: Entscheidungszitat).

Quellen:
- Fließtext: Gericht, dann optional Spruchkörper, Art und Datum, dann ein oder
  mehrere Aktenzeichen („BGH, Beschluss vom 05.01.2011 - XII ZB 152/10“,
  „Kammergericht Berlin, … 1 W 170/03 und 1 W 182/03“).
- Fließtext ohne Gericht: Aktenzeichen, die das Gericht selbst erkennen lassen
  (BGH ``XII ZB``, BVerfG ``2 BvR``, BSG ``B 8 SO``, BayObLG ``3Z BR``).
- ``{{Rspr|…}}``-Vorlagen: Aktenzeichen oder Fundstelle (``BVerfGE 31, 58``).

Kennung: allein eindeutige Aktenzeichen (siehe ``_SELF_IDENTIFYING``) stehen für
sich; alle anderen brauchen das Gericht (``LG Mühlhausen 1 T 5/11``). Ein Gericht
ohne Ort („das OLG“) wird nicht übernommen.
"""
from __future__ import annotations

import datetime
import re
from dataclasses import dataclass, replace

from lexikon.templates import canonical_name

MONTHS = {"Januar": 1, "Jan.": 1, "Februar": 2, "Febr.": 2, "Feb.": 2, "März": 3, "Mrz.": 3,
          "April": 4, "Apr.": 4, "Mai": 5, "Juni": 6, "Jun.": 6, "Juli": 7, "Jul.": 7,
          "August": 8, "Aug.": 8, "September": 9, "Sept.": 9, "Sep.": 9, "Oktober": 10,
          "Okt.": 10, "November": 11, "Nov.": 11, "Dezember": 12, "Dez.": 12}

#: Zeitschriften, deren Fundstellen wie Aktenzeichen aussehen („BtE 1996/97“)
JOURNALS = ["BtE", "NJW", "NJWE", "FPR", "RdLH", "MDR", "NZS", "ZfF", "BtMan", "FamRZ", "BtPrax",
            "FGPrax", "FuR", "JZ", "DNotZ", "Rpfleger", "NZFam", "FF", "ZFE", "RuP", "ZfSH", "NDV"]

#: Adjektivische Gerichtsnamen → Ort (OLG: Sitz; Landesgerichte: Land)
OLG_ADJ = {"Brandenburgisches": "Brandenburg", "Schleswig-Holsteinisches": "Schleswig",
           "Thüringer": "Jena", "Thüringisches": "Jena", "Saarländisches": "Saarbrücken",
           "Pfälzisches": "Zweibrücken", "Hanseatisches": "Hamburg"}
LAND_ADJ = {"Bayerisches": "Bayern", "Bayerischer": "Bayern", "Niedersächsisches": "Niedersachsen",
            "Hessisches": "Hessen", "Hessischer": "Hessen", "Sächsisches": "Sachsen",
            "Sächsischer": "Sachsen", "Thüringer": "Thüringen", "Brandenburgisches": "Brandenburg",
            "Schleswig-Holsteinisches": "Schleswig-Holstein", "Saarländisches": "Saarland",
            "Hanseatisches": "Hamburg"}
PLACE_ALIASES = {"NRW": "Nordrhein-Westfalen"}

_SP = r"[^\S\n]"  # Leerraum ohne Zeilenumbruch
_FEDERAL = r"Kammergericht(?:\sBerlin)?|KG(?:\sBerlin)?|BVerfG|BVerwG|BayObLG|BGH|BSG|BFH|BAG|EuGH|EGMR"
_LOCAL = r"OLG|LG|AG|LSG|SG|VG|OVG|VGH|FG|LAG|ArbG"
_ADJ = "|".join(sorted(set(OLG_ADJ) | set(LAND_ADJ), key=len, reverse=True))
_PLACE = (
    r"(?!(?:vom|v|Beschl|Beschluss|Beschlüsse|Urt|Urteil|Urteile|Az|Entscheidung)\b)"
    r"[A-ZÄÖÜ][\wäöüß-]*\.?(?:/[A-ZÄÖÜ][\wäöüß]*\.?)?"
    r"(?:\s(?:a\.\s?M\.|am\sMain|\([A-ZÄÖÜ][\wäöüß]+\)|I{1,3}\b|i\.\s?Br\.|an\sder\s\w+))?"
)
_COURT = (
    # nicht mitten im Wort; nicht als Teil eines Aktenzeichens („2 OLG 21 Ss 734/14“)
    rf"(?<!\w)(?!(?<=\d\s)(?:OLG|OVG|VG)\s\d)(?:(?P<adj>{_ADJ}){_SP}+)?"
    rf"(?:(?P<fed>{_FEDERAL})|(?P<typ>{_LOCAL})(?:{_SP}(?P<place>{_PLACE}))?)(?![\w-])"
)
_SEPS = r"[\s,;:·|–-]*+"
_SENAT = rf"(?:{_SP}*+\(?\d+\.{_SP}?\w*[Ss]enat\)?)?"
_ART = (
    r"(?P<art>Beschlüsse|Beschluss|Beschl\.?|Urteile|Urteil|Endurteil|Teilurteil|Versäumnisurteil|Urt\.?"
    r"|Gerichtsbescheid|Entscheidung|Verfügung)(?:\sdes\s\w+)?"
)
_DATE = (
    r"(?P<datum>\d{1,2}\.\s?\d{1,2}\.?\s?(?:\d{4}|\d{2})\b"
    rf"|\d{{1,2}}\.\s?(?:{'|'.join(map(re.escape, sorted(MONTHS, key=len, reverse=True)))})\s?\d{{4}})"
)
_LINK = rf"{_SENAT}{_SEPS}(?:{_ART}{_SEPS})?(?:(?:(?:vom|v\.?|V\.)\s*+)?{_DATE}{_SEPS})?(?:Az\.?:?\s*+)?"

_NOT_JOURNAL = rf"(?!(?:{'|'.join(JOURNALS)})\b)"
_AZ = (
    r"(?<![\w/-])(?:"
    # BayObLG: 3Z BR 169/02, 3 Z BR 102/01, 2 ZBR 157/04, 3Z 146/91
    rf"\d{_SP}?Z{_SP}?(?:BR|AR|R)?{_SP}?\d+/\d{{2,4}}"
    # allgemein, mit optionalem Präfix (I-25, 2-12), Gerichtskürzel (OVG 6 M, 2 OLG 21 Ss, 1 St OLG Ss)
    rf"|(?:(?:[A-Z]{{1,2}}|\d+)-)?(?:\d+{_SP})?(?:St{_SP})?(?:(?:OVG|VG|OLG){_SP})?(?:\d+{_SP})?"
    rf"(?:[IVX]+[a-z]?{_SP})?(?:[BLS]{_SP}\d+[a-z]?{_SP})?{_NOT_JOURNAL}[A-Z][A-Za-z]{{0,3}}{_SP}?\d+/\d{{2,4}}"
    rf"(?:{_SP}?R\b)?"
    # Amtsgericht mit römischer Abteilung: 404 XVII 2174/21
    rf"|(?:\d+{_SP})?[IVX]+{_SP}\d+/\d{{2,4}}"
    r")(?![\w/])"
)
_AZ_RE = re.compile(_AZ)
_AZ_LIST = rf"(?P<azs>{_AZ}(?:{_SP}*+(?:,|;|und\b|u\.|sowie\b){_SP}*+{_AZ})*+)"
_PATTERN = re.compile(rf"{_COURT}{_LINK}{_AZ_LIST}")

#: Aktenzeichen, die ihr Gericht selbst erkennen lassen und daher allein eindeutig sind
_SELF_IDENTIFYING = [
    ("BGH", r"[IVX]+[a-z]?\s(?:ZR|ZB|ZA|StR|ARs|AR|BLw|AnwZ|NotZ)\s?\d"),
    ("BFH", r"[IVX]+\s[RBSEK]\s\d"),
    ("BVerfG", r"\d\sBv[A-Z]\s\d"),
    ("BSG", r"B\s\d+[a-z]?\s[A-Z]{1,3}\s\d"),
    ("BAG", r"\d+\s(?:AZR|ABR|AZB)\s\d"),
    ("BayObLG", r"\dZ\s(?:BR\s|AR\s|R\s)?\d"),
]
_STANDALONE = re.compile(
    r"(?<![\w/-])(?:[IVX]+[a-z]?\s(?:ZR|ZB|ZA|StR|ARs|AR|BLw|AnwZ|NotZ)\s?\d+/\d{2}"
    r"|\d\sBv[A-Z]\s\d+/\d{2}|B\s\d+[a-z]?\s[A-Z]{1,3}\s\d+/\d{2}(?:\sR\b)?"
    rf"|\d{_SP}?Z{_SP}?(?:BR|AR){_SP}?\d+/\d{{2}})(?![\w/])"
)
_FUNDSTELLE = re.compile(r"^(?P<slg>[A-Z][A-Za-z-]+)\s\d+,\s?\d+")
SLG_COURT = {"BVerfGE": "BVerfG", "BGHZ": "BGH", "BGHSt": "BGH", "BSGE": "BSG", "BVerwGE": "BVerwG"}


def normalize_az(az: str) -> str:
    az = " ".join(az.split())
    if m := re.match(r"^(\d)\s?Z\s?(BR|AR|R)?\s?(\d+/\d+)$", az):
        return f"{m.group(1)}Z {m.group(2) + ' ' if m.group(2) else ''}{m.group(3)}"
    return az


def court_for_az(az: str) -> str | None:
    for court, pattern in _SELF_IDENTIFYING:
        if re.match(pattern, az):
            return court
    return None


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
            key = re.sub(r"\sR$", "", self.az)
            if court_for_az(self.az) or not self.gericht:
                return key
            return f"{self.gericht} {key}"
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
    if m := re.fullmatch(r"(\d{1,2})\.\s?(\d{1,2})\.?\s?(\d{2}|\d{4})", datum):
        d, mo, y = (int(x) for x in m.groups())
    else:
        d_s, mo_s, y_s = re.fullmatch(r"(\d{1,2})\.\s?(.+?)\s?(\d{4})", datum).groups()
        d, mo, y = int(d_s), MONTHS[mo_s], int(y_s)
    if y < 100:
        y += 2000 if y < 50 else 1900
    try:
        return datetime.date(y, mo, d).isoformat()
    except ValueError:
        return None


def _place(place: str) -> str:
    place = " ".join(place.split())
    if place in PLACE_ALIASES:
        return PLACE_ALIASES[place]
    if place.startswith("Freiburg"):
        return "Freiburg (Breisgau)"
    if place.startswith("Frankfurt"):
        rest = place[len("Frankfurt"):].strip()
        return "Frankfurt (Oder)" if "Oder" in rest else "Frankfurt am Main"
    if place.endswith(".") and "/" not in place:
        place = place[:-1]
    return place


def _court(m: re.Match) -> str | None:
    if fed := m.group("fed"):
        return "KG" if fed.startswith(("Kammergericht", "KG")) else fed
    typ, adj, place = m.group("typ"), m.group("adj"), m.group("place")
    if place:
        return f"{typ} {_place(place)}"
    if adj:
        land = OLG_ADJ.get(adj) if typ == "OLG" else LAND_ADJ.get(adj)
        return f"{typ} {land}" if land else None
    return None  # „das OLG“: Ort unbekannt


def _art(art: str | None) -> str | None:
    if not art:
        return None
    if art.startswith("Beschl"):
        return "Beschluss"
    if art.startswith("Urt") or art.endswith("urteil") or art == "Urteile":
        return "Urteil"
    return art


def parse_decisions(text: str) -> list[DecisionRef]:
    """Entscheidungszitate aus Fließtext, ohne Dubletten, in Reihenfolge des Auftretens."""
    found: dict[str, DecisionRef] = {}
    covered: list[tuple[int, int]] = []
    for m in _PATTERN.finditer(text):
        court, art, datum = _court(m), _art(m.group("art")), _iso(m.group("datum"))
        for a in _AZ_RE.finditer(m.group("azs")):
            az = normalize_az(a.group(0))
            ref = DecisionRef(court or court_for_az(az), art, datum, az)
            found[ref.id] = _fill(found[ref.id], ref) if ref.id in found else ref
        covered.append(m.span())
    for a in _STANDALONE.finditer(text):
        if any(s <= a.start() < e for s, e in covered):
            continue
        az = normalize_az(a.group(0))
        ref = DecisionRef(court_for_az(az), None, None, az)
        found.setdefault(ref.id, ref)
    return list(found.values())


def decisions_from_templates(code) -> list[DecisionRef]:
    """Entscheidungszitate aus ``{{Rspr|…}}``-Vorlagen."""
    found: dict[str, DecisionRef] = {}
    for t in code.filter_templates():
        if canonical_name(str(t.name)) != "Rspr" or not t.has(1):
            continue
        value = " ".join(str(t.get(1).value).split())
        if not value:
            continue
        if "/" not in value and (m := _FUNDSTELLE.match(value)):
            ref = DecisionRef(gericht=SLG_COURT.get(m.group("slg")), fundstelle=m.group(0))
        else:
            az = normalize_az(value)
            ref = DecisionRef(gericht=court_for_az(az), az=az)
        found.setdefault(ref.id, ref)
    return list(found.values())


def _fill(a: DecisionRef, b: DecisionRef) -> DecisionRef:
    return replace(a, **{f: getattr(b, f) for f in ("gericht", "art", "datum")
                         if getattr(a, f) is None and getattr(b, f) is not None})


def merge_decisions(refs: list[DecisionRef]) -> list[DecisionRef]:
    """Führt Zitate derselben Entscheidung zusammen.

    Ein Zitat ohne Gericht (``19 T 529/02``) wird dem Zitat mit Gericht und gleichem
    Aktenzeichen zugeschlagen (``LG Frankfurt (Oder) 19 T 529/02``).
    """
    by_id: dict[str, DecisionRef] = {}
    for r in refs:
        by_id[r.id] = _fill(by_id[r.id], r) if r.id in by_id else r
    with_court = {r.az for r in by_id.values() if r.az and r.id != r.az}
    return [r for r in by_id.values() if not (r.az and r.id == r.az and r.az in with_court)]


def completeness(d: dict) -> int:
    return sum(1 for k in ("gericht", "art", "datum") if d.get(k))
