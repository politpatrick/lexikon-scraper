"""Rohseiten-Archiv in raw/<pageid>.json (ADR 0001)."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from lexikon.models import RawPage

DELETED_LOG = "_deleted.jsonl"


@dataclass
class SyncResult:
    written: int = 0
    unchanged: int = 0
    deleted: list[int] = field(default_factory=list)


def dump_json(data, path: Path) -> None:
    """Schreibt JSON mit stabiler Formatierung (kleine, lesbare Diffs)."""
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _read_log(raw_dir: Path) -> list[dict]:
    f = raw_dir / DELETED_LOG
    if not f.exists():
        return []
    return [json.loads(line) for line in f.read_text(encoding="utf-8").splitlines() if line]


def _write_log(raw_dir: Path, entries: list[dict]) -> None:
    f = raw_dir / DELETED_LOG
    if not entries:
        f.unlink(missing_ok=True)
        return
    f.write_text(
        "".join(json.dumps(e, ensure_ascii=False, sort_keys=True) + "\n" for e in entries),
        encoding="utf-8",
    )


def _read_page(path: Path) -> RawPage:
    return RawPage.from_json(json.loads(path.read_text(encoding="utf-8")))


def sync_raw(pages: Iterable[RawPage], raw_dir: Path) -> SyncResult:
    """Schreibt neue/geänderte Rohseiten und protokolliert verschwundene Seiten.

    Das Lösch-Protokoll wird erst geschrieben, wenn ``pages`` vollständig
    durchlaufen wurde. Bricht der Abruf ab, gilt keine Seite als gelöscht.
    Rohseiten-Dateien werden nie entfernt.
    """
    raw_dir = Path(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    result = SyncResult()
    seen: set[int] = set()
    for page in pages:
        seen.add(page.pageid)
        path = raw_dir / f"{page.pageid}.json"
        if path.exists() and _read_page(path).revid == page.revid:
            result.unchanged += 1
            continue
        dump_json(page.to_json(), path)
        result.written += 1

    log = [e for e in _read_log(raw_dir) if e["pageid"] not in seen]
    logged = {e["pageid"] for e in log}
    for path in sorted(raw_dir.glob("*.json"), key=lambda p: int(p.stem)):
        pageid = int(path.stem)
        if pageid in seen or pageid in logged:
            continue
        old = _read_page(path)
        log.append({"pageid": pageid, "title": old.title, "last_revid": old.revid})
        result.deleted.append(pageid)
    _write_log(raw_dir, log)
    return result


def load_raw(raw_dir: Path, include_deleted: bool = True) -> list[RawPage]:
    """Lädt alle Rohseiten, sortiert nach pageid."""
    raw_dir = Path(raw_dir)
    deleted = set() if include_deleted else {e["pageid"] for e in _read_log(raw_dir)}
    pages = [_read_page(p) for p in raw_dir.glob("*.json")]
    return sorted((p for p in pages if p.pageid not in deleted), key=lambda p: p.pageid)
