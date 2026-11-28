# 08: Altformat ablösen

**What to build:** Ein Vollständigkeitsvergleich zeigt, dass `articles/` alle Inhalte aus `artikel/` abdeckt. Danach entfallen die alten Workflows `scrape.yml` und `build-tag-index.yml`, die Skripte `scraper.py` und `scrape_all_articles.py` sowie `tag-index.json`. `artikel/` wird gelöscht oder eingefroren, je nach Entscheidung aus der Spec.

**Blocked by:** 03, 04, 06

**Status:** erledigt 28.11.2026 (Entscheidung: löschen)

- [x] Vergleichsbericht: Jeder alte Artikel hat ein neues Gegenstück, die Textabdeckung ist dokumentiert
- [x] Nur noch ein Workflow im Repo
- [x] README beschreibt die neue Struktur

## Vollständigkeitsvergleich (28.11.2026)

- Alle 512 Titel aus `artikel/` haben eine Rohseite in `raw/`; 195 davon sind Weiterleitungen
  (aufgelöst statt als Artikel geführt), 102 Seiten sind ohne lesbare Revision (`_unreadable.jsonl`,
  konnte auch der alte Scraper nicht lesen).
- Wortabdeckung des alten Textes im neuen (bereinigt um Link-Darstellung): Median 99,3 %,
  5 %-Quantil 96,5 %, Minimum 91,5 %. Die Abweichung kommt daher, dass der alte Scraper bei
  `[[Ziel|Anzeige]]` das Ziel druckte; das neue Format zeigt wie das Wiki den Anzeigetext.
- `index.json` ist durch `articles/` ersetzt, `tag-index.json` (Worthäufigkeiten) entfällt ersatzlos.
