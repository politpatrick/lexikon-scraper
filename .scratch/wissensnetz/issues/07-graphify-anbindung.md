# 07: graphify als Abfrageschicht

**What to build:** Ein dokumentierter Befehl erzeugt aus `graph/graph.json` die graphify-Ausgaben (Report, `graph.html`) ohne LLM-Extraktion. Agenten können das Netz per `graphify-mcp` abfragen. Die README beschreibt die typischen Abfragen (`explain`, `path`).

**Blocked by:** 03

**Status:** erledigt 28.11.2026. `python -m lexikon graphify` (119 Communities, ohne LLM); `.mcp.json` mit Server `lexikon-wissensnetz` (graphify-mcp auf graph/graph.json), Handshake und Abfragen getestet

- [x] Ein Befehl baut die graphify-Ausgaben reproduzierbar
- [x] `graphify path` findet einen Pfad zwischen „Einwilligungsvorbehalt“ und „Betreuungsgericht“
- [x] Die MCP-Konfiguration für Claude Code ist dokumentiert
- [x] Die graphify-Ausgaben werden nicht automatisch committet (Größe, Rauschen), solange nicht anders entschieden
