# ADR 0001: Unveränderter Wikitext ist die Archivwahrheit

**Status:** vorgeschlagen · 2026-11-24

## Kontext
Der bisherige Scraper speichert nur das Ergebnis von `mwparserfromhell.strip_code()`.
Dabei gehen Vorlagen verloren, unter anderem Normverweise: In mindestens 66 von 512
Artikeln stehen Lücken wie „vgl.  Abs. 3 SGB-I“. Revisionsnummer, Zeitstempel und
Kategorien werden nicht gespeichert.

## Entscheidung
- Je Seite wird `raw/<pageid>.json` mit unverändertem Wikitext, `revid`, `timestamp`,
  `title` und Kategorien gespeichert.
- Alle weiteren Schichten (Artikel, Wissensnetz, RAG-Index) werden ausschließlich offline
  aus `raw/` erzeugt.
- Neu geschrieben wird eine Rohseite nur, wenn sich `revid` ändert.
- Dateinamen verwenden `pageid`, nicht den Titel.

## Folgen
- Parserfehler lassen sich ohne neuen Abruf beheben.
- Die Git-Historie zeigt nur echte inhaltliche Änderungen.
- Der Live-Abruf läuft in GitHub Actions, weil die Cloud-Sessions die Wiki-API nicht erreichen.
