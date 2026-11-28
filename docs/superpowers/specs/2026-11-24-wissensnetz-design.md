# Spec: Wissensnetz aus dem Lexikon Betreuungsrecht

**Status:** Entwurf, wartet auf Freigabe · 2026-11-24
**Vokabular:** siehe `GLOSSARY.md` · **ADRs:** 0001, 0002

## Problem Statement

Das Repo spiegelt das Lexikon täglich als JSON. Die Kopie ist für Archiv und RAG
unbrauchbar:

- Normverweise aus Vorlagen werden gelöscht. In mindestens 66 von 512 Artikeln ist das sichtbar.
- Das Linknetz mischt interne Links mit 1.439 Wikipedia-Links und 296 Bild-Links.
- 564 von 10.462 internen Links zeigen ins Leere, weil Weiterleitungen nicht aufgelöst werden.
- Es gibt weder Revision noch Zeitstempel noch Kategorien.
- Die Tags beruhen auf Worthäufigkeiten und sind wertlos.
- Altes und neues Betreuungsrecht stehen ungekennzeichnet nebeneinander (59 Artikel mit § 1896 BGB, 39 mit § 1814 BGB).
- Zwei Workflows und zwei fast gleiche Skripte schreiben ins selbe Verzeichnis.

## Solution

Eine Pipeline mit drei reproduzierbaren Schichten:

1. **Rohseiten** (`raw/`): Archivwahrheit, inkrementell nach `revid` (ADR 0001).
2. **Artikel** (`articles/`): Abschnitte mit Pfad; Links getrennt nach intern, Wikipedia, Bild und extern; Normzitate und Entscheidungszitate strukturiert.
3. **Wissensnetz** (`graph/graph.json`): graphify-kompatibel (ADR 0002), dazu ein Qualitätsbericht.

Ein einziger GitHub-Workflow führt alle drei Schichten aus. Das RAG ist ein eigenes,
späteres Teilprojekt mit eigener Spec. Es baut auf `articles/` und `graph/` auf.

## User Stories

1. Als Archivar will ich den unveränderten Wikitext jeder Seite sichern, damit ich Parserfehler ohne erneuten Abruf beheben kann.
2. Als Archivar will ich zu jeder Rohseite `revid` und Zeitstempel haben, damit ich den Stand jeder Aussage belegen kann.
3. Als Archivar will ich, dass unveränderte Seiten nicht neu geschrieben werden, damit die Git-Historie nur echte Änderungen zeigt.
4. Als Archivar will ich, dass im Lexikon gelöschte Seiten protokolliert statt stillschweigend entfernt werden, damit nichts unbemerkt verschwindet.
5. Als Archivar will ich Dateinamen ohne Sonderzeichen, damit das Archiv auf jedem Dateisystem funktioniert.
6. Als Pfleger des Repos will ich eine Übersicht aller verwendeten Vorlagen, damit ich für jede festlegen kann, wie sie behandelt wird.
7. Als Leser will ich Normverweise im Artikeltext vollständig sehen, damit Sätze wie „vgl. § 30 Abs. 3 SGB I“ wieder stimmen.
8. Als Leser will ich je Artikel die zitierten Normen als Liste, damit ich die Rechtsgrundlagen sofort sehe.
9. Als Leser will ich je Artikel die zitierte Rechtsprechung mit Gericht, Datum und Aktenzeichen, damit ich Entscheidungen nachschlagen kann.
10. Als Leser will ich erkennen, ob eine Norm zur alten oder zur neuen Fassung gehört, damit ich nicht nach überholtem Recht handle.
11. Als Leser will ich von einer alten Norm zur Nachfolgenorm springen, damit ich die aktuelle Rechtslage finde.
12. Als Leser will ich die Abschnitte eines Artikels mit ihrer Überschriftenhierarchie, damit Fundstellen präzise zitierbar sind.
13. Als Nutzer des Netzes will ich, dass interne Links über Weiterleitungen auf echte Artikel zeigen, damit keine Kante ins Leere führt.
14. Als Nutzer des Netzes will ich Wikipedia-, Bild- und externe Links getrennt von internen Links, damit „verwandt“ wirklich verwandt bedeutet.
15. Als Nutzer des Netzes will ich Kategorien als Knoten, damit ich Themengruppen abfragen kann.
16. Als Nutzer des Netzes will ich fragen „Welche Artikel zitieren § 1831 BGB?“ und die vollständige Antwort bekommen.
17. Als Nutzer des Netzes will ich den Pfad zwischen zwei Begriffen sehen (`graphify path`), damit ich Zusammenhänge verstehe.
18. Als Agent will ich das Netz per MCP abfragen (`graphify-mcp`), damit ich nicht in 500 JSON-Dateien suchen muss.
19. Als Pfleger des Repos will ich nach jedem Lauf einen Qualitätsbericht (Waisen, tote Links, Artikel nur mit altem Recht, meistzitierte Normen), damit ich Lücken im Lexikon erkenne.
20. Als Pfleger des Repos will ich genau einen Workflow, damit keine zwei Jobs gegeneinander arbeiten.
21. Als Pfleger des Repos will ich, dass das alte `artikel/`-Format erst verschwindet, wenn das neue nachweislich alles enthält, damit kein Wissen verloren geht.
22. Als künftiger RAG-Entwickler will ich Abschnitte mit Normen, Kategorien und `revid` als Metadaten, damit ich Chunks ohne Neuberechnung bilden kann.

## Implementation Decisions

- **Module:** API-Client, Rohseiten-Archiv, Vorlagen-Behandlung, Normen-Parser, Entscheidungs-Parser, Normalizer, Graph-Export, CLI. Jedes Modul hat eine schmale Schnittstelle. Nur der API-Client spricht mit dem Netz.
- **Abruf:** MediaWiki-API mit `generator=allpages`, Paketen zu 50 Seiten, `prop=revisions|categories|info`, `rvslots=main`, `formatversion=2`, `maxlag`. Weiterleitungen über `list=allredirects` bzw. `redirects`-Auflösung. Generischer User-Agent ohne persönliche Daten.
- **Inkrementell:** Rohseite schreiben nur bei neuer `revid`. Fehlende Seiten in ein Lösch-Protokoll.
- **Vorlagen:** Die Behandlung jeder Vorlage steht in einer Konfigurationstabelle, die aus der Vorlagen-Inventur entsteht: als Text rendern, als Normzitat, als Entscheidungszitat oder verwerfen. Vorlagen werden vor dem Entfernen des Markups verarbeitet.
- **Normzitat-Form:** `{gesetz, paragraph, absatz?, satz?, fassung?}`, kanonische ID `GESETZ§PARAGRAPH` (Abkürzungen normalisiert: „SGB-I“ → `SGBI`). Mehrfachzitate (`§§ 99, 104 FamFG`) ergeben mehrere Zitate; Bereiche (`§§ 1814 ff.`) ergeben ein Zitat mit Bereichsmarke.
- **Fassung:** Eine Zuordnungstabelle alt→neu für die Reform 2023, fachlich geprüft. `a.F.` im Text oder eine Norm aus dem alten Bereich ergibt `fassung=alt` und eine Kante `superseded_by`.
- **Wissensnetz-Schema (graphify-kompatibel):** Knotentypen `article`, `category`, `norm`, `decision`, `external`. Kantenrelationen `links_to`, `in_category`, `cites_norm`, `cites_decision`, `references_external`, `superseded_by`. Jede Kante hat `confidence: "EXTRACTED"` und `source_file`.
- **graphify:** wird nur als Abfrageschicht genutzt (`cluster-only`, `explain`, `path`, MCP), ohne LLM-Extraktion (ADR 0002).
- **Ablage:** `raw/`, `articles/`, `graph/`, `reports/`. `artikel/` bleibt bis zum Vollständigkeitsnachweis erhalten.
- **Workflow:** Ein Job: Abruf → Normalisierung → Graph → Bericht → Commit nur bei Änderungen. Die alten Workflows und Skripte entfallen.

## Testing Decisions

- Tests prüfen nur äußeres Verhalten: Wikitext rein, Artikel oder Zitate raus; API-Antwort rein, Rohseiten raus.
- **Testschnittstelle:** möglichst eine, nämlich die Funktion „Rohseite → Artikel“ mit echten Wikitext-Fixtures. Dazu kommen Tabellentests für die Normen- und Entscheidungs-Parser und ein Test für den Graph-Export.
- Fixtures sind echte Wikitexte aus dem ersten `raw/`-Lauf: Betreuungsverfahren, Einwilligungsvorbehalt, eine Weiterleitung, eine Bundesland-Seite und ein Artikel mit viel Rechtsprechung.
- Keine Netzwerkzugriffe in Tests. Der API-Client wird mit aufgezeichneten JSON-Antworten getestet.
- Bisher gibt es keine Tests im Repo, also auch keine Vorlage. Eingeführt wird `pytest`.

## Out of Scope

- RAG (Chunking, Embeddings, Retrieval, Golden-Set): eigene Spec, sobald `articles/` und `graph/` stehen.
- Generischer Adapter für mehrere Wikis (YAGNI, bis eine zweite Quelle konkret ist).
- Graphdatenbank-Server.
- Volltexte der Gesetze als Knoteninhalt (spätere Erweiterung über Open Legal Data oder gesetze-im-internet.de).
- LLM-basierte Extraktion im täglichen Lauf.

## Further Notes

**Offene Fragen, die die Freigabe blockieren:**
1. Unter welcher Lizenz steht das Lexikon, und ist dieses Repo öffentlich? Davon hängt ab, ob die Spiegelung zulässig ist.
2. Wer prüft die Zuordnungstabelle alt→neu fachlich?
3. ~~Soll `artikel/` nach dem Vollständigkeitsnachweis gelöscht werden oder als Altformat eingefroren bleiben?~~ Entschieden 28.11.2026: gelöscht (Ticket 08).

**Annahmen:** Tickets liegen als lokale Markdown-Dateien in `.scratch/` (Standard von
`/setup-matt-pocock-skills`). Es werden keine GitHub-Issues angelegt, solange du das nicht bestätigst.
