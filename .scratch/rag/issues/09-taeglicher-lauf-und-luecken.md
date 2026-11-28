# 09: Index im täglichen Lauf und Protokoll schwacher Fragen

**What to build:** Der tägliche Workflow prüft, ob der Index aus den neuen Daten baut und der Testsatz die Baseline hält. Optional protokolliert der Server Fragen ohne guten Treffer lokal, ohne Personenbezug, damit Lücken im Lexikon oder in der Suche sichtbar werden.

**Blocked by:** 02

**Status:** ready-for-agent

- [ ] Workflow schlägt fehl, wenn der Index nicht baut oder Recall@5 unter die Baseline fällt
- [ ] Das Protokoll ist abschaltbar, enthält nur die Frage und die Trefferqualität und wird nicht committet
