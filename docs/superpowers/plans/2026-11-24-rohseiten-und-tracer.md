# Rohseiten-Archiv und Wissensnetz-Tracer: Implementierungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Den Wikitext des Lexikons verlustfrei mit Revisionen archivieren und daraus Artikel, ein graphify-kompatibles Wissensnetz und einen Qualitätsbericht erzeugen (Tickets 01 und 03).

**Architecture:** Ein Python-Paket `lexikon` unter `src/`. Nur `api.py` spricht mit dem Netz. `archive.py` schreibt und liest `raw/`. `normalize.py`, `graph.py` und `report.py` arbeiten rein offline auf Rohseiten. Ein neuer Workflow führt `archive` und `build` aus; die alten Workflows laufen bis Ticket 08 unverändert weiter.

**Tech Stack:** Python 3.11, `requests`, `mwparserfromhell`, `pytest`; graphify ≥ 0.9 nur zur Verifikation.

**Spec:** `docs/superpowers/specs/2026-11-24-wissensnetz-design.md` · ADRs `docs/adr/0001`, `0002` · Vokabular `GLOSSARY.md`

## Global Constraints

- Python 3.11. Laufzeitabhängigkeiten nur `requests` und `mwparserfromhell`; dev nur `pytest`.
- Tests greifen nie aufs Netz zu.
- API-Basis `https://www.lexikon-betreuungsrecht.de/api.php`, Header `User-Agent: lexikon-scraper-archiv/1.0`, Parameter `maxlag=5`, mindestens 0,5 s Pause zwischen Anfragen.
- Alle JSON-Ausgaben mit `ensure_ascii=False, indent=2, sort_keys=True` und abschließendem Zeilenumbruch, damit die Diffs stabil bleiben.
- Rohseiten-Dateiname `raw/<pageid>.json`. Der Artikel-Slug ist nur ein Feld, nie ein Dateiname.
- Jede Graph-Kante hat `source`, `target`, `relation`, `confidence="EXTRACTED"`, `source_file`.
- `artikel/`, `scraper.py`, `scrape_all_articles.py` und die alten Workflows bleiben unangetastet (Ticket 08).
- Die Wiki-API ist aus Cloud-Sessions nicht erreichbar. Live-Läufe passieren nur im GitHub-Workflow.

## Review Focus

1. **Titel mit Sonderzeichen** (Soft-Hyphen `e­in­wil­li­gungs­vor­be­halt`, Doppelpunkt `Betreuungsrecht-Lexikon:Haftungsausschluss`, Klammern `Betreuer (Ehrenamt)`): Der Slug ist deterministisch, Soft-Hyphens werden entfernt, und die Datei heißt trotzdem nach `pageid`. → Test in Task 4.
2. **Groß-/Kleinschreibung des ersten Buchstabens:** `[[betreuer]]` und `[[Betreuer]]` zeigen auf denselben Artikel (MediaWiki-Regel). → Test in Task 4.
3. **Ketten und Schleifen von Weiterleitungen:** A→B→C wird zu C aufgelöst, A→B→A bricht ohne Endlosschleife ab und gilt als toter Link. → Test in Task 5.
4. **Abbruch mitten im Abruf** (HTTP-Fehler, `maxlag`, fehlendes `continue`): Der Lauf scheitert laut. Das Lösch-Protokoll wird nur nach vollständiger Auflistung geschrieben, damit nie Seiten fälschlich als gelöscht gelten. → Test in Task 3.
5. **Links mit Anker oder Anzeigetext** (`[[Betreuer#Auswahl|der Betreuer]]`): Ziel ist `betreuer`, der Text bleibt „der Betreuer“. → Test in Task 4.

---

### Task 1: Paketgerüst und Datenmodell

**Files:**
- Create: `pyproject.toml`, `src/lexikon/__init__.py`, `src/lexikon/models.py`, `tests/test_models.py`

**Interfaces:**
- Produces:
  - `RawPage` (frozen dataclass): `pageid: int, title: str, revid: int, timestamp: str, wikitext: str, categories: tuple[str, ...], is_redirect: bool`
  - `RawPage.to_json() -> dict`, `RawPage.from_json(d: dict) -> RawPage`

- [x] **Step 1: Write the failing test** `test_rawpage_roundtrip`: `RawPage.from_json(p.to_json()) == p` für eine Seite mit Umlauten und Soft-Hyphen im Titel.
- [x] **Step 2:** `pytest tests/test_models.py -v` → FAIL (ImportError)
- [x] **Step 3:** `pyproject.toml` mit src-Layout und `[tool.pytest.ini_options] pythonpath=["src"]`; `RawPage` in `src/lexikon/models.py`.
- [x] **Step 4:** `pytest -v` → PASS
- [x] **Step 5:** Commit `feat: Paketgerüst und RawPage`

### Task 2: API-Client

**Files:**
- Create: `src/lexikon/api.py`, `tests/test_api.py`, `tests/fixtures/api/batch1.json`, `tests/fixtures/api/batch2.json`

**Interfaces:**
- Consumes: `RawPage`
- Produces: `iter_raw_pages(session: requests.Session, base_url: str = BASE_URL, batch_size: int = 50, pause: float = 0.5) -> Iterator[RawPage]`

Die Fixtures bilden die Antwortform von `formatversion=2` nach: `query.pages[]` mit `pageid, title, redirect?, revisions[0].{revid,timestamp,slots.main.content}, categories[].title`. `batch1.json` enthält `continue`, `batch2.json` nicht. Nach dem ersten echten Workflow-Lauf die Fixtures durch aufgezeichnete Antworten ersetzen.

- [x] **Step 1: Failing tests** mit einer Fake-Session, die die Fixtures nacheinander liefert:
  - `test_follows_continue`: 3 Seiten aus 2 Antworten; die zweite Anfrage enthält die `continue`-Parameter der ersten.
  - `test_maps_fields`: `revid`, `timestamp`, `wikitext` und `categories` (ohne Präfix `Kategorie:`) korrekt; `is_redirect=True` bei Seiten mit `redirect`.
  - `test_request_params`: `generator=allpages`, `gaplimit=50`, `prop=revisions|categories|info`, `rvslots=main`, `formatversion=2`, `maxlag=5`.
  - `test_raises_on_api_error`: Antwort mit `{"error": {...}}` → `ApiError`.
- [x] **Step 2:** `pytest tests/test_api.py -v` → FAIL
- [x] **Step 3:** `iter_raw_pages` implementieren. Retry mit Backoff (3 Versuche) nur bei HTTP 5xx und `maxlag`, danach `ApiError`. User-Agent gemäß Global Constraints.
- [x] **Step 4:** `pytest -v` → PASS
- [x] **Step 5:** Commit `feat: MediaWiki-API-Client mit Batch-Abruf`

### Task 3: Rohseiten-Archiv, inkrementell

**Files:**
- Create: `src/lexikon/archive.py`, `tests/test_archive.py`

**Interfaces:**
- Consumes: `RawPage`, `iter_raw_pages`
- Produces:
  - `SyncResult` (dataclass): `written: int, unchanged: int, deleted: list[int]`
  - `sync_raw(pages: Iterable[RawPage], raw_dir: Path) -> SyncResult`
  - `load_raw(raw_dir: Path) -> list[RawPage]`

- [x] **Step 1: Failing tests** (mit `tmp_path`):
  - `test_writes_by_pageid`: Datei `raw/123.json` existiert und enthält den Wikitext byte-genau.
  - `test_unchanged_revid_not_rewritten`: zweiter Sync mit gleicher `revid` → `unchanged == 1` und unveränderte `mtime`.
  - `test_missing_page_logged_not_deleted`: Seite fehlt im zweiten Lauf → `deleted == [123]`, die Datei existiert weiter, `raw/_deleted.jsonl` enthält `{"pageid":123,"title":…,"last_revid":…}`.
  - `test_iterator_error_writes_no_deletions` (Review Focus 4): Der Iterator wirft nach 1 Seite → Exception geht durch, `_deleted.jsonl` bleibt unverändert.
- [x] **Step 2:** `pytest tests/test_archive.py -v` → FAIL
- [x] **Step 3:** Implementieren. Die Lösch-Erkennung läuft erst, nachdem der Iterator vollständig erschöpft ist.
- [x] **Step 4:** `pytest -v` → PASS
- [x] **Step 5:** Commit `feat: inkrementelles Rohseiten-Archiv`

### Task 4: Links klassifizieren und Slugs

**Files:**
- Create: `src/lexikon/links.py`, `tests/test_links.py`

**Interfaces:**
- Produces:
  - `slug(title: str) -> str`: Soft-Hyphens (`­`) entfernen, erster Buchstabe großschreiben (MediaWiki-Regel), dann klein schreiben, Leerzeichen/Unterstriche → `-`
  - `LinkKind = Literal["internal", "wikipedia", "image", "category", "interwiki"]`
  - `classify(target: str) -> tuple[LinkKind, str]`: gibt Art und bereinigtes Ziel zurück (Anker entfernt)

- [x] **Step 1: Failing tests** (parametrisiert):
  - `slug("Betreuer (Ehrenamt)") == "betreuer-(ehrenamt)"`; `slug("e­in­wil­li­gungs­vor­be­halt") == "einwilligungsvorbehalt"`; `slug("betreuer") == slug("Betreuer")`
  - `classify("Betreuer#Auswahl") == ("internal", "Betreuer")`
  - `classify("wikipedia:de:Notar") == ("wikipedia", "de:Notar")`
  - `classify("Bild:Justiz.jpg")`, `classify("Datei:x.png")`, `classify("File:x.png")` → `"image"`
  - `classify("Kategorie:Verfahren") == ("category", "Verfahren")`
- [x] **Step 2:** `pytest tests/test_links.py -v` → FAIL
- [x] **Step 3:** Implementieren. Die Präfixe stehen als Konstanten in `links.py`.
- [x] **Step 4:** `pytest -v` → PASS
- [x] **Step 5:** Commit `feat: Linkklassifikation und Slugs`

### Task 5: Normalizer Rohseite → Artikel

**Files:**
- Create: `src/lexikon/normalize.py`, `tests/test_normalize.py`, `tests/fixtures/wikitext/verfahren.txt`, `tests/fixtures/wikitext/weiterleitung.txt`

**Interfaces:**
- Consumes: `RawPage`, `slug`, `classify`
- Produces:
  - `Section` (dataclass): `path: tuple[str, ...], text: str`
  - `Article` (dataclass): `pageid, title, slug, revid, timestamp, categories: list[str], sections: list[Section], internal_links: list[str]` (Slugs, aufgelöst, sortiert, eindeutig), `wikipedia_links: list[str], images: list[str], external_links: list[str], dead_links: list[str]`; dazu `to_json() -> dict`
  - `build_redirect_map(pages: list[RawPage]) -> dict[str, str]` (Slug → Slug, Ketten aufgelöst)
  - `normalize(page: RawPage, redirects: dict[str, str], known: set[str]) -> Article`

Die Fixture `verfahren.txt` ist ein gekürzter Wikitext mit `== Zuständigkeit ==`, `=== International zuständig ===`, einem internen Link mit Anker, einem Wikipedia-Link, einem Bild und einem `[http://… Text]`-Link. Nach dem ersten Workflow-Lauf durch echten Wikitext aus `raw/` ersetzen.

- [x] **Step 1: Failing tests:**
  - `test_section_paths`: Pfade `("Einleitung",)`, `("Zuständigkeit",)`, `("Zuständigkeit", "International zuständig")`.
  - `test_links_typed`: Wikipedia-Ziel steht in `wikipedia_links`, nicht in `internal_links`; Bild in `images`; `http`-Link in `external_links`.
  - `test_link_text_kept`: `[[Betreuer#Auswahl|der Betreuer]]` → Text enthält „der Betreuer“, `internal_links` enthält `"betreuer"`.
  - `test_redirect_resolved`: Mit `{"betreuerin": "betreuer"}` wird `[[Betreuerin]]` zu `"betreuer"`.
  - `test_redirect_chain_and_loop` (Review Focus 3): A→B→C ergibt C; A→B→A ergibt einen toten Link, ohne Endlosschleife.
  - `test_dead_link`: Ziel nicht in `known` → `dead_links`.
- [x] **Step 2:** `pytest tests/test_normalize.py -v` → FAIL
- [x] **Step 3:** Implementieren mit `mwparserfromhell`. Weiterleitungen haben Wikitext `#WEITERLEITUNG [[X]]` oder `#REDIRECT [[X]]`. Vorlagen bleiben in diesem Ticket unbehandelt (Ticket 04), werden aber nicht stumm gelöscht, sondern als `{{…}}` im Text belassen.
- [x] **Step 4:** `pytest -v` → PASS
- [x] **Step 5:** Commit `feat: Normalizer mit Abschnitten und typisierten Links`

### Task 6: Graph-Export und Qualitätsbericht

**Files:**
- Create: `src/lexikon/graph.py`, `src/lexikon/report.py`, `tests/test_graph.py`

**Interfaces:**
- Consumes: `Article`
- Produces:
  - `build_graph(articles: list[Article]) -> dict`: graphify-Form `{"directed": false, "multigraph": false, "graph": {}, "nodes": [...], "links": [...]}`. Knoten-IDs `art:<slug>`, `cat:<name>`, `ext:<host>`. Relationen `links_to`, `in_category`, `references_external`. `directed: false` folgt der graphify-Konvention: Die Richtung steckt in der Reihenfolge `source` → `target`.
  - `quality_report(articles: list[Article], graph: dict) -> str` (Markdown)

- [x] **Step 1: Failing tests:**
  - `test_edges_reference_existing_nodes`: Jede `source`/`target` existiert unter `nodes[].id`.
  - `test_edge_fields`: Jede Kante hat `confidence == "EXTRACTED"` und ein nichtleeres `source_file`.
  - `test_no_wikipedia_in_links_to`: Kein `links_to`-Ziel beginnt mit etwas anderem als `art:`.
  - `test_report_sections`: Der Bericht enthält die Überschriften `## Waisen`, `## Tote Links`, `## Kennzahlen`.
- [x] **Step 2:** `pytest tests/test_graph.py -v` → FAIL
- [x] **Step 3:** Implementieren. Waisen sind Artikel ohne eingehende `links_to`-Kante.
- [x] **Step 4:** `pytest -v` → PASS
- [x] **Step 5: Verifikation mit graphify** (lokal, nicht in CI): Graph aus einem Test-Artikelsatz schreiben, dann `graphify cluster-only <dir> --no-label` → Ausgabe ohne `missing required field`.
- [x] **Step 6:** Commit `feat: graphify-kompatibler Graph-Export und Qualitätsbericht`

### Task 7: CLI und Workflow

**Files:**
- Create: `src/lexikon/__main__.py`, `tests/test_cli.py`, `.github/workflows/wissensnetz.yml`
- Modify: `requirements.txt` (bleibt für die alten Workflows; `pyproject.toml` ist die Quelle für den neuen)

**Interfaces:**
- Consumes: `iter_raw_pages`, `sync_raw`, `load_raw`, `build_redirect_map`, `normalize`, `build_graph`, `quality_report`
- Produces:
  - `python -m lexikon archive --raw raw/`
  - `python -m lexikon build --raw raw/ --articles articles/ --graph graph/graph.json --report reports/qualitaet.md`

- [x] **Step 1: Failing test** `test_build_end_to_end`: zwei Rohseiten (eine davon eine Weiterleitung) in `tmp_path/raw` → `build` erzeugt genau 1 Datei in `articles/`, `graph.json` und den Bericht; Rückgabecode 0.
- [x] **Step 2:** `pytest tests/test_cli.py -v` → FAIL
- [x] **Step 3:** CLI mit `argparse` implementieren; Artikeldateien als `articles/<pageid>.json`.
- [x] **Step 4:** `pytest -v` → alle PASS
- [x] **Step 5:** Workflow `wissensnetz.yml`: `workflow_dispatch` plus täglich `0 5 * * *`; Python 3.11; `pip install -e . pytest`; `pytest`; `python -m lexikon archive`; `python -m lexikon build`; Commit von `raw/ articles/ graph/ reports/` nur bei Änderungen. `permissions: contents: write`, `concurrency: wissensnetz`.
- [x] **Step 6:** Commit `feat: CLI und Workflow für das Wissensnetz`
- [ ] **Step 7 (HITL, offen):** Workflow manuell starten. Danach prüfen: Anzahl `raw/*.json` gegen die Seitenzahl im Lexikon, und ob ein zweiter Lauf ohne Änderungen keinen Commit erzeugt. Anschließend die Fixtures aus Task 2 und Task 5 durch echte Daten ersetzen.
