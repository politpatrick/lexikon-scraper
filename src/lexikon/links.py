"""Linkziele klassifizieren und Seitentitel in Slugs übersetzen."""
from __future__ import annotations

from typing import Literal

LinkKind = Literal["internal", "wikipedia", "image", "category", "category-link"]

WIKIPEDIA_PREFIXES = ("wikipedia:",)
IMAGE_PREFIXES = ("bild:", "datei:", "file:", "image:")
CATEGORY_PREFIXES = ("kategorie:", "category:")


def slug(title: str) -> str:
    """Stabiler Schlüssel für einen Seitentitel.

    Entfernt Soft-Hyphens, schreibt alles klein (deckt die MediaWiki-Regel ab,
    dass der erste Buchstabe nicht unterscheidet) und ersetzt Leerzeichen und
    Unterstriche durch Bindestriche.
    """
    s = title.replace("\u00ad", "").replace("_", " ")
    return "-".join(s.split()).lower()


def _strip_prefix(target: str, prefixes: tuple[str, ...]) -> str | None:
    low = target.lower()
    for prefix in prefixes:
        if low.startswith(prefix):
            return target[len(prefix):].strip()
    return None


def classify(target: str) -> tuple[LinkKind, str]:
    """Liefert Art des Links und das bereinigte Ziel (ohne Anker)."""
    t = target.strip()
    leading_colon = t.startswith(":")
    if leading_colon:
        t = t[1:].strip()
    if (rest := _strip_prefix(t, CATEGORY_PREFIXES)) is not None:
        return ("category-link" if leading_colon else "category"), rest
    if (rest := _strip_prefix(t, IMAGE_PREFIXES)) is not None:
        return "image", rest
    if (rest := _strip_prefix(t, WIKIPEDIA_PREFIXES)) is not None:
        return "wikipedia", rest
    return "internal", t.split("#", 1)[0].strip()
