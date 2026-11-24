# 08: Altformat ablösen

**What to build:** Ein Vollständigkeitsvergleich zeigt, dass `articles/` alle Inhalte aus `artikel/` abdeckt. Danach entfallen die alten Workflows `scrape.yml` und `build-tag-index.yml`, die Skripte `scraper.py` und `scrape_all_articles.py` sowie `tag-index.json`. `artikel/` wird gelöscht oder eingefroren, je nach Entscheidung aus der Spec.

**Blocked by:** 03, 04, 06

**Status:** needs-human (Entscheidung löschen oder einfrieren)

- [ ] Vergleichsbericht: Jeder alte Artikel hat ein neues Gegenstück, die Textabdeckung ist dokumentiert
- [ ] Nur noch ein Workflow im Repo
- [ ] README beschreibt die neue Struktur
