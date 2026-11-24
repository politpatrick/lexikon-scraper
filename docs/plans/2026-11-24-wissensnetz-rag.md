# Wissensnetz & RAG aus dem Lexikon Betreuungsrecht

> Aufbau nach Matt Pococks Flow (`grill-me` → `to-prd` → `to-issues` → `tdd`) und
> dem Superpowers-Format für Umsetzungspläne (`writing-plans` → `executing-plans`).
> Die Skills selbst waren in der Session, in der dieser Plan entstand, nicht installiert;
> die Struktur ist nachgebaut. Für die Umsetzung: Skills installieren und diesen Plan
> mit `/to-issues` bzw. `superpowers:executing-plans` abarbeiten.

**Ziel:** Das Lexikon verlustfrei archivieren und daraus ein typisiertes Wissensnetz
(Artikel, Abschnitte, Normen, Entscheidungen, Kategorien, externe Quellen) erzeugen,
auf dem ein RAG mit Hybrid-Suche und Graph-Expansion läuft.

**Architektur:** Drei Schichten, jede aus der vorherigen reproduzierbar:
`raw/` (Wikitext + Revisions-Metadaten, die Archivwahrheit) → `normalized/` (JSON je
Artikel, Abschnitte als Markdown) → `graph/` (nodes.jsonl / edges.jsonl) → `rag/`
(Chunks + Index). Nur `raw/` braucht Netzwerk; alles andere ist offline neu baubar.

**Tech-Stack:** Python 3.11, `requests`, `mwparserfromhell`, `pytest`, `networkx`,
SQLite (FTS5 für BM25), ein Embedding-Modell mit guter deutscher Abdeckung,
optional `sqlite-vec` oder LanceDB. Kein Neo4j (bei ~500 Artikeln Overkill).

---

## 0. Befund zum Ist-Zustand (Grundlage der Entscheidungen)

Gemessen am Stand von `artikel/` am 24.11.2026:

| Befund | Zahl | Folge |
|---|---|---|
| Artikel | 512 | – |
| Artikel mit sichtbar gelöschten Normverweisen (`vgl.  Abs. 3 SGB-I`) | ≥ 66 | `strip_code()` wirft Vorlagen wie `{{§|…}}` weg → Rechtsquellen gehen verloren |
| `wikipedia:`-Links als „verwandte Artikel“ | 1.439 | externe Links verunreinigen das interne Netz |
| `Bild:`-Links als „verwandte Artikel“ | 296 | dito |
| interne Links ins Leere | 564 von 10.462 | Weiterleitungen/Groß-Kleinschreibung nicht aufgelöst |
| Artikel mit `§ 1896` (alte Rechtslage) / `§ 1814` (neu) | 59 / 39 | Altes und neues Recht gemischt → Zeitbezug muss in den Graph |
| Tags | 3.989 Worthäufigkeits-Tags („jetzt“, „links“, „überprüft“) | wertlos für Retrieval, ersetzen durch Kategorien + Normen |
| Revisions-ID / Zeitstempel / Kategorien | fehlen | keine Änderungserkennung, keine Provenienz |
| Workflows | 2 (`scrape.yml`, `build-tag-index.yml`) schreiben ins selbe Verzeichnis | Race / doppelte Arbeit |

---

## 1. Grill-me: offene Entscheidungen (vor Start klären)

1. **Lizenz/Nutzungsrecht:** Unter welcher Lizenz stehen die Lexikon-Texte, und darfst
   du sie in einem (öffentlichen?) Repo spiegeln und in einem RAG ausliefern?
   Ist das Repo öffentlich?
2. **Wer fragt das RAG?** Nur du (Fachkraft) oder Ehrenamtliche/Betroffene? Davon hängt
   ab, wie hart Antworten mit veraltetem Recht blockiert werden müssen.
3. **Stichtag-Logik:** Soll das RAG Fragen standardmäßig nach Recht ab 01.01.2023
   beantworten und altes Recht nur als „historisch“ markiert liefern?
4. **Zweite Quelle:** Gibt es konkret ein zweites Wiki, das in den nächsten 3 Monaten
   dazukommt? Falls nein: kein generisches Adapter-Framework bauen (YAGNI).
5. **Normtexte selbst:** Sollen die zitierten Paragraphen (BGB, FamFG, SGB …) als
   eigene Knoten mit Volltext geladen werden (gesetze-im-internet.de / Open Legal Data),
   oder reicht der Verweis?
6. **Laufzeitumgebung RAG:** lokal (Ollama/LM Studio) oder Claude-API? Datenschutz
   ist hier unkritisch, solange nur Lexikon-Inhalte, keine Falldaten, im Index liegen.

---

## 2. PRD (to-prd)

### Problem
Der Scraper archiviert das Lexikon verlustbehaftet: Rechtsquellen werden gelöscht,
das Linknetz ist mit externen Links und Bildern verunreinigt, Provenienz fehlt.
Ein RAG auf dieser Basis würde Normen nicht finden und veraltetes Recht als aktuell
ausgeben.

### Lösung
Ein Drei-Schichten-Pipeline (raw → normalized → graph) mit typisierten Kanten,
darauf ein RAG mit Hybrid-Suche (BM25 + Vektor) und 1-Hop-Graph-Expansion über
Links und Normen. Zitierte Normen werden kanonisiert (`BGB §1814 Abs. 1`) und mit
Gültigkeitszeitraum versehen.

### User Stories
1. Als Archivar will ich den Original-Wikitext jeder Seite samt `revid` und Zeitstempel
   sichern, damit ich jederzeit neu parsen kann, ohne die Quelle erneut abzurufen.
2. Als Archivar will ich nur geänderte Seiten neu laden, damit der tägliche Lauf
   schnell ist und die Git-Historie echte Änderungen zeigt.
3. Als Nutzer will ich zu jedem Artikel die zitierten Normen als Liste sehen.
4. Als Nutzer will ich fragen „Welche Artikel behandeln § 1831 BGB?“ und alle finden.
5. Als Nutzer will ich bei Antworten sehen, ob eine Norm altes (vor 2023) oder neues
   Recht ist.
6. Als Nutzer will ich zitierte Rechtsprechung (Gericht, Datum, Aktenzeichen) als
   eigene Knoten haben.
7. Als Nutzer will ich, dass das RAG Antworten mit Artikel- und Abschnittsquelle belegt.
8. Als Nutzer will ich, dass das RAG verwandte Artikel über das Linknetz einbezieht.
9. Als Entwickler will ich Kategorien und Weiterleitungen sauber aufgelöst haben.

### Implementierungsentscheidungen
- **Abruf:** MediaWiki-API mit `generator=allpages` und gebündelten `prop`-Abfragen
  (`revisions|categories|links|extlinks|templates|info`, je 50 Titel), `rvslots=main`,
  plus `list=allredirects`. Kein HTML-Scraping.
- **Archivformat:** Wikitext ist die Wahrheit (`raw/<pageid>.json` mit `wikitext`,
  `revid`, `timestamp`, `title`). Zusätzlich optional ein Voll-Export als MediaWiki-XML
  (`Special:Export`) – das ist das Standard-Archivformat und von MediaWiki re-importierbar.
- **Dateinamen:** `pageid` statt Titel (keine Soft-Hyphens, Doppelpunkte, Kollisionen).
  Der Slug bleibt als Feld erhalten.
- **Normalisiert:** JSON je Artikel; Abschnitte als Markdown mit Hierarchie
  (`h2 > h3`). Vorlagen werden *vor* `strip_code()` in Text + strukturierte Zitate
  übersetzt.
- **Graph:** `nodes.jsonl` / `edges.jsonl`, Knotentypen
  `Article, Section, Category, Norm, Decision, ExternalSource, Image`,
  Kantentypen `LINKS_TO, HAS_SECTION, IN_CATEGORY, CITES_NORM, CITES_DECISION,
  REFERENCES_EXTERNAL, REDIRECTS_TO, SUPERSEDED_BY` (Norm alt → neu).
- **Normen-Kanonisierung:** eigener Parser (Regex + Gesetzesabkürzungs-Liste),
  Ausgabe `{gesetz, paragraph, absatz, satz, nr, fassung}`; Mapping-Tabelle
  alt→neu für die Betreuungsrechtsreform 2023 (§§ 1896 ff. a.F. → §§ 1814 ff. n.F.).
- **RAG:** Chunk = Abschnitt (max. ~800 Tokens, sonst Absatz-Split) mit
  Kontext-Kopf `Artikel › Abschnitt`; Metadaten: Normen, Kategorien, `revid`.
  Retrieval: BM25 (SQLite FTS5) + Vektor, Reciprocal Rank Fusion, dann 1-Hop-Expansion
  über `LINKS_TO`/`CITES_NORM` mit Abwertungsfaktor.
- **Workflows:** ein einziger Workflow; `build-tag-index.yml` und `scraper.py`-Duplikat
  entfallen.

### Testentscheidungen
- Tests prüfen externes Verhalten der Module (Eingabe Wikitext → Ausgabe Struktur),
  nicht Interna.
- Fixtures: 5–10 echte Wikitexte aus `raw/` (Betreuungsverfahren, Einwilligungsvorbehalt,
  eine Weiterleitung, ein Artikel mit Rechtsprechung, eine Bundesland-Seite).
- Netzwerkfreie Tests; der API-Client wird über aufgezeichnete JSON-Antworten getestet.
- Golden-Set für RAG: 30 Fragen mit erwarteten Artikeln → Recall@5 als Metrik.

### Außerhalb des Umfangs
- Generischer Multi-Wiki-Adapter (erst bei konkreter zweiter Quelle).
- Graph-Datenbank-Server (Neo4j o. ä.).
- Web-Frontend für das RAG.
- LLM-basierte Entitätsextraktion (inkl. graphify) im Kernpfad – siehe Abschnitt 5.

---

## 3. Issues als vertikale Slices (to-issues)

Jeder Slice ist end-to-end lauffähig. **AFK** = Agent kann allein umsetzen,
**HITL** = braucht deine Entscheidung/Prüfung.

| # | Slice | Typ | Blockiert durch |
|---|---|---|---|
| 1 | Grill-me-Fragen aus Abschnitt 1 beantworten | HITL | – |
| 2 | Raw-Archiv: gebündelter API-Abruf, `raw/<pageid>.json` mit revid/timestamp, inkrementell | AFK | 1 (Lizenz) |
| 3 | Vorlagen-Inventur: alle in `raw/` verwendeten Vorlagen zählen, Bedeutung je Vorlage festlegen | HITL | 2 |
| 4 | Normalizer: Abschnitte, Links typisiert (intern/Wikipedia/Bild/extern), Vorlagen → Text, Weiterleitungen aufgelöst | AFK | 3 |
| 5 | Normen-Parser + Kanonisierung + alt→neu-Mapping | AFK (Mapping: HITL-Review) | 4 |
| 6 | Rechtsprechungs-Parser (Gericht, Datum, Az.) | AFK | 4 |
| 7 | Graph-Export (nodes/edges.jsonl) + Qualitätsbericht (Waisen, tote Links, Top-Normen) | AFK | 5, 6 |
| 8 | Ein Workflow statt zwei; alte Skripte/`tag-index.json` entfernen | AFK | 7 |
| 9 | Chunking + BM25-Index + Golden-Set (30 Fragen) | AFK (Golden-Set: HITL) | 7 |
| 10 | Vektor-Index + RRF + Graph-Expansion, Recall@5 messen | AFK | 9 |
| 11 | Optional: graphify-Lauf als Explorations-Report, Vergleich mit eigenem Graph | HITL | 7 |

---

## 4. Umsetzungsplan (Superpowers `writing-plans`-Format)

Regeln für jede Aufgabe: TDD (Test rot → minimal grün → refaktorieren), kleine Commits,
vor „fertig“ Tests laufen lassen und Ausgabe prüfen (`verification-before-completion`).

### Task 1 – Projektgerüst
**Dateien:** `pyproject.toml`, `src/lexikon/__init__.py`, `tests/conftest.py`,
`tests/fixtures/`.
1. `pyproject.toml` mit `requests`, `mwparserfromhell`, `networkx`; dev: `pytest`.
2. `pytest -q` → 0 Tests, Exit 0.
3. Commit: `chore: Projektgerüst mit pytest`.

### Task 2 – API-Client mit gebündeltem Abruf (Slice 2)
**Dateien:** `src/lexikon/api.py`, `tests/test_api.py`,
`tests/fixtures/api_batch.json` (aufgezeichnete Antwort).
1. Test: `iter_pages(session)` liefert aus der Fixture Dicts mit
   `pageid, title, revid, timestamp, wikitext, categories, redirect`.
2. Test: Fortsetzung über `continue` wird befolgt (Fixture mit zwei Seiten).
3. Implementierung: `generator=allpages&gaplimit=50&prop=revisions|categories|info&rvprop=ids|timestamp|content&rvslots=main&formatversion=2`,
   `User-Agent` mit generischem Projektnamen, `maxlag=5`, Retry mit Backoff.
4. `pytest tests/test_api.py -q` → grün. Commit.

### Task 3 – Raw-Archiv, inkrementell (Slice 2)
**Dateien:** `src/lexikon/archive.py`, `tests/test_archive.py`, `raw/`.
1. Test: Seite mit unveränderter `revid` wird nicht neu geschrieben.
2. Test: Datei heißt `raw/<pageid>.json`, enthält Wikitext unverändert.
3. Test: gelöschte Seiten landen in `raw/_deleted.jsonl` statt zu verschwinden.
4. CLI: `python -m lexikon archive`. Einmal gegen die Live-API laufen lassen,
   Anzahl mit `siteinfo.statistics.articles` abgleichen.
5. Commit inkl. `raw/`.

### Task 4 – Vorlagen-Inventur (Slice 3, HITL)
**Dateien:** `scripts/template_inventory.py`, `docs/vorlagen.md`.
1. Skript zählt alle Vorlagennamen in `raw/` mit Beispielen.
2. Du legst in `docs/vorlagen.md` je Vorlage fest: *als Text rendern*, *als Norm-Zitat*,
   *als Rechtsprechungs-Zitat*, *verwerfen*.

### Task 5 – Normalizer (Slice 4)
**Dateien:** `src/lexikon/normalize.py`, `tests/test_normalize.py`,
`tests/fixtures/wikitext/*.txt`.
1. Test (Regression zum Befund): Wikitext mit `vgl. {{§|30|SGB I}} Abs. 3` ergibt
   Text `vgl. § 30 Abs. 3 SGB I` **und** ein strukturiertes Zitat. (Vorlagensyntax
   gemäß Task 4 anpassen.)
2. Test: `[[wikipedia:de:Notar]]` → externer Link, nicht in `internal_links`.
3. Test: `[[Bild:Justiz.jpg]]` → `images`, nicht in `internal_links`.
4. Test: `[[Betreuer]]` wird über Weiterleitungstabelle auf Zielseite aufgelöst.
5. Test: Abschnittshierarchie `h2 > h3` bleibt als `path` erhalten.
6. Ausgabe `normalized/<pageid>.json`. Commit.

### Task 6 – Normen-Parser (Slice 5)
**Dateien:** `src/lexikon/norms.py`, `data/gesetze.csv` (Abkürzungen),
`data/reform2023_mapping.csv`, `tests/test_norms.py`.
1. Tests (parametrisiert): `§§ 99, 104 FamFG` → zwei Normen;
   `§ 272 Abs. 2 FamFG`; `§ 1896 BGB a.F.`; `Art. 24 EGBGB`; `§ 15, § 19 RPflG`;
   `§§ 1814 ff. BGB` (Bereich).
2. Test: `BGB §1896` erhält `fassung="alt"` und Kante `SUPERSEDED_BY → BGB §1814`.
3. Mapping-Tabelle von dir prüfen lassen (HITL). Commit.

### Task 7 – Rechtsprechungs-Parser (Slice 6)
**Dateien:** `src/lexikon/decisions.py`, `tests/test_decisions.py`.
1. Test: `LG Augsburg, Beschluss vom 30. Januar 2018 – 054 T 161/18` →
   `{gericht, art, datum, az}`.
2. Test: `BGH XII ZB 123/20` ohne Datum wird erkannt.
3. Optional später: Abgleich mit Open Legal Data für Volltext/ECLI. Commit.

### Task 8 – Graph-Export + Qualitätsbericht (Slice 7)
**Dateien:** `src/lexikon/graph.py`, `tests/test_graph.py`, `graph/`,
`reports/graph_report.md`.
1. Test: jede Kante referenziert existierende Knoten-IDs.
2. Test: keine `LINKS_TO`-Kante auf Wikipedia/Bild.
3. Bericht: Knoten/Kanten je Typ, Waisen-Artikel, tote Links, meistzitierte Normen,
   Artikel mit nur altem Recht, Communities (networkx Louvain).
4. Commit.

### Task 9 – Ein Workflow (Slice 8)
**Dateien:** `.github/workflows/build.yml`; entfernen: `scrape.yml`,
`build-tag-index.yml`, `scraper.py`, `scrape_all_articles.py`, `artikel/tag-index.json`.
1. Workflow: archive → normalize → graph → Report; Commit nur bei Änderungen.
2. `artikel/` erst entfernen, wenn `normalized/` alle Inhalte abdeckt (Vergleichsskript).

### Task 10 – Chunks + BM25 + Golden-Set (Slice 9)
**Dateien:** `src/lexikon/rag/chunk.py`, `src/lexikon/rag/bm25.py`,
`eval/golden.jsonl`, `tests/test_chunk.py`, `eval/run_eval.py`.
1. Test: kein Chunk > Limit; jeder Chunk hat `article_id, section_path, norms, revid`.
2. 30 Fragen mit erwarteten Artikeln (HITL), z. B. „Wann braucht der Betreuer eine
   Genehmigung für eine Wohnungskündigung?“ → `wohnungskündigung`, `genehmigungen-von-a-bis-z`.
3. Recall@5 mit BM25 messen und als Baseline festhalten.

### Task 11 – Vektor + Fusion + Graph-Expansion (Slice 10)
**Dateien:** `src/lexikon/rag/vector.py`, `src/lexikon/rag/retrieve.py`.
1. Recall@5 gegen Baseline: Vektor allein, BM25+Vektor (RRF), RRF + 1-Hop-Expansion.
2. Nur behalten, was messbar besser ist.
3. Antwort-Prompt: Quellen mit Artikel › Abschnitt; Normen mit `fassung="alt"`
   explizit als „Rechtslage vor 01.01.2023“ kennzeichnen.

### Task 12 – Optional: graphify-Vergleich (Slice 11)
1. graphify einmal auf `normalized/` laufen lassen (zeitlich begrenzt, z. B. 1 Stunde).
2. Vergleichen: findet es Zusammenhänge, die im expliziten Graph fehlen?
   Nur wenn ja, gezielt diese Kantenart in den eigenen Parser übernehmen.

---

## 5. Warum graphify nicht im Kernpfad

- Ein Wiki hat seinen Graph bereits explizit (Links, Kategorien, Vorlagen). graphify
  würde ihn für Prosa per LLM *schätzen* – nicht deterministisch, kostet Tokens, und
  jede Kante ist eine Vermutung, wo du ein Faktum hast.
- graphify ist auf Code-Repos optimiert (AST-Parsing ist der deterministische Teil);
  für Rechtszitate gibt es keinen Parser – genau dort liegt dein Mehrwert.
- Was es gut kann (Clustering, Visualisierung, Report), liefert networkx auf dem
  expliziten Graph reproduzierbar.
- Sinnvoller Einsatz: als einmalige Explorationslinse, um unentdeckte Zusammenhänge
  oder Waisen zu finden (Task 12).
