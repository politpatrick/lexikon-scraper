"""Abruf der Rohseiten über die MediaWiki-API. Einziges Modul mit Netzzugriff."""
from __future__ import annotations

import time
from typing import Iterator

import requests

from lexikon.models import RawPage

BASE_URL = "https://www.lexikon-betreuungsrecht.de/api.php"
USER_AGENT = "lexikon-scraper-archiv/1.0"
CATEGORY_PREFIXES = ("Kategorie:", "Category:")
RETRIES = 3


class ApiError(RuntimeError):
    """Die API hat einen Fehler gemeldet oder war nach Wiederholungen nicht erreichbar."""


def _get(session, base_url: str, params: dict, pause: float) -> dict:
    last = None
    for attempt in range(RETRIES):
        resp = session.get(base_url, params=params, headers={"User-Agent": USER_AGENT}, timeout=60)
        if resp.status_code >= 500:
            last = f"HTTP {resp.status_code}"
        else:
            resp.raise_for_status()
            data = resp.json()
            err = data.get("error")
            if not err:
                return data
            if err.get("code") != "maxlag":
                raise ApiError(f"{err.get('code')}: {err.get('info')}")
            last = "maxlag"
        time.sleep(pause * (2 ** attempt) * 4)
    raise ApiError(f"API nach {RETRIES} Versuchen nicht verfügbar ({last})")


def _strip_category(title: str) -> str:
    for prefix in CATEGORY_PREFIXES:
        if title.startswith(prefix):
            return title[len(prefix):]
    return title


def _merge(acc: dict, page: dict) -> None:
    cur = acc.setdefault(page["pageid"], {"categories": []})
    for key, value in page.items():
        if key == "categories":
            cur["categories"].extend(value)
        elif key not in cur or not cur[key]:
            cur[key] = value


def _to_rawpage(page: dict) -> RawPage:
    rev = page["revisions"][0]
    return RawPage(
        pageid=page["pageid"],
        title=page["title"],
        revid=rev["revid"],
        timestamp=rev["timestamp"],
        wikitext=rev["slots"]["main"]["content"],
        categories=tuple(_strip_category(c["title"]) for c in page.get("categories", [])),
        is_redirect=bool(page.get("redirect", False)),
    )


def iter_raw_pages(
    session: requests.Session,
    base_url: str = BASE_URL,
    batch_size: int = 50,
    pause: float = 0.5,
    unreadable: list[dict] | None = None,
) -> Iterator[RawPage]:
    """Liefert alle Seiten des Hauptnamensraums inklusive Weiterleitungen.

    Teilantworten (z. B. Kategorien über mehrere Antworten verteilt) werden
    zusammengeführt; Seiten werden erst ausgegeben, wenn die API das Paket als
    vollständig meldet (``batchcomplete``).

    Manche alte Seiten liefert die API ohne abrufbare Revision. Ist
    ``unreadable`` eine Liste, werden sie dort als ``{pageid, title, lastrevid}``
    gesammelt; sonst bricht der Abruf mit ``ApiError`` ab.
    """
    base = {
        "action": "query",
        "format": "json",
        "formatversion": 2,
        "generator": "allpages",
        "gapnamespace": 0,
        "gaplimit": batch_size,
        "prop": "revisions|categories|info",
        "rvprop": "ids|timestamp|content",
        "rvslots": "main",
        "cllimit": "max",
        "maxlag": 5,
    }
    cont: dict = {}
    acc: dict = {}
    while True:
        data = _get(session, base_url, {**base, **cont}, pause)
        for page in data.get("query", {}).get("pages", []):
            if "missing" in page or "invalid" in page:
                continue
            _merge(acc, page)
        if data.get("batchcomplete"):
            for page in acc.values():
                if page.get("revisions"):
                    yield _to_rawpage(page)
                elif unreadable is not None:
                    unreadable.append({"pageid": page["pageid"], "title": page.get("title"),
                                       "lastrevid": page.get("lastrevid")})
                else:
                    raise ApiError(f"Seite ohne Revision: {page.get('title')!r}")
            acc = {}
        if "continue" not in data:
            break
        cont = data["continue"]
        if pause:
            time.sleep(pause)
    if acc:
        raise ApiError("Abruf endete mit unvollständigem Paket")


def fetch_redirect_targets(
    session: requests.Session,
    titles: list[str],
    base_url: str = BASE_URL,
    pause: float = 0.5,
) -> dict[str, str]:
    """Ziele von Weiterleitungen laut Weiterleitungstabelle (auch ohne lesbare Revision)."""
    result: dict[str, str] = {}
    for i in range(0, len(titles), 50):
        data = _get(session, base_url, {
            "action": "query", "format": "json", "formatversion": 2,
            "titles": "|".join(titles[i:i + 50]), "redirects": 1, "maxlag": 5,
        }, pause)
        for r in data.get("query", {}).get("redirects", []):
            result[r["from"]] = r["to"]
        if pause:
            time.sleep(pause)
    return result
