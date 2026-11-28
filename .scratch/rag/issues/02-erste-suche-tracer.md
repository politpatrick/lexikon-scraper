# 02: Tracer Bullet: Chunks → BM25 → `suche` → MCP

**What to build:** Durchgehend lauffähige erste Suche.
- Chunks aus `articles/`: lange Abschnitte an Absatzgrenzen geteilt, kurze verbunden, jeder mit Kontextkopf „Artikel › Pfad“ und Metadaten.
- Ein SQLite-FTS5-Index mit BM25, beim Start aus `articles/` gebaut und nicht committet.
- Die Funktion `suche(frage, anzahl, token_budget)` liefert Treffer mit Text, Quelle (Artikel, Pfad, Lexikon-URL) und Stand.
- Der MCP-Server `lexikon-rag` bietet das Werkzeug `suche` an und ist in `.mcp.json` eingetragen.
- Die Baseline ist auf dem Testsatz gemessen und festgehalten.

**Blocked by:** 01 (für die Baseline-Messung; Chunks, Index und Server können vorher entstehen)

**Status:** ready-for-agent

- [ ] Kein Chunk über der Zielgröße; jeder Chunk hat Artikel, Pfad, `pageid`, `revid`
- [ ] Index-Aufbau aus den echten Daten in wenigen Sekunden
- [ ] MCP-Handshake und ein echter `suche`-Aufruf sind getestet
- [ ] Baseline Recall@5 und MRR stehen im Repo; ein Test schlägt fehl, wenn sie unterschritten werden
- [ ] Stichprobe von 25 Fragen geprüft, sowohl auf falsche als auch auf fehlende Treffer
