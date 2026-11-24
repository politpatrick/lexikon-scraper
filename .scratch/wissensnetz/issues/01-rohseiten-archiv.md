# 01: Rohseiten-Archiv mit Revisionen

**What to build:** Der tägliche Lauf sichert jede Seite des Lexikons als Rohseite mit unverändertem Wikitext, `revid`, Zeitstempel und Kategorien. Unveränderte Seiten bleiben unangetastet. Gelöschte Seiten werden protokolliert. Der Lauf läuft in einem neuen, eigenen GitHub-Workflow parallel zum alten.

**Blocked by:** None (can start immediately). Die Lizenzfrage aus der Spec muss vor dem ersten Push von `raw/` geklärt sein.

**Status:** ready-for-agent

- [ ] Anzahl der Rohseiten entspricht `siteinfo.statistics.articles` (± Weiterleitungen, im Log ausgewiesen)
- [ ] Zweiter Lauf ohne Änderungen im Lexikon erzeugt keinen Commit
- [ ] Dateinamen sind `pageid`-basiert; keine Soft-Hyphens oder Doppelpunkte
- [ ] API-Client ist mit aufgezeichneten Antworten getestet, inklusive Fortsetzung (`continue`)
- [ ] User-Agent enthält keine persönlichen Daten
