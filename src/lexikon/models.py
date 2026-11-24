"""Datenmodell der Rohseiten (siehe GLOSSARY.md)."""
from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class RawPage:
    """Unveränderter Wikitext einer Seite mit Revision und Kategorien."""

    pageid: int
    title: str
    revid: int
    timestamp: str
    wikitext: str
    categories: tuple[str, ...] = ()
    is_redirect: bool = False

    def to_json(self) -> dict:
        d = asdict(self)
        d["categories"] = list(self.categories)
        return d

    @classmethod
    def from_json(cls, d: dict) -> "RawPage":
        return cls(
            pageid=int(d["pageid"]),
            title=d["title"],
            revid=int(d["revid"]),
            timestamp=d["timestamp"],
            wikitext=d["wikitext"],
            categories=tuple(d.get("categories", ())),
            is_redirect=bool(d.get("is_redirect", False)),
        )
