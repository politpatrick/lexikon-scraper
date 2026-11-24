# 07: graphify als Abfrageschicht

**What to build:** Ein dokumentierter Befehl erzeugt aus `graph/graph.json` die graphify-Ausgaben (Report, `graph.html`) ohne LLM-Extraktion. Agenten können das Netz per `graphify-mcp` abfragen. Die README beschreibt die typischen Abfragen (`explain`, `path`).

**Blocked by:** 03

**Status:** ready-for-agent

- [ ] Ein Befehl baut die graphify-Ausgaben reproduzierbar
- [ ] `graphify path` findet einen Pfad zwischen „Einwilligungsvorbehalt“ und „Betreuungsgericht“
- [ ] Die MCP-Konfiguration für Claude Code ist dokumentiert
- [ ] Die graphify-Ausgaben werden nicht automatisch committet (Größe, Rauschen), solange nicht anders entschieden
