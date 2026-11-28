# 07: Werkzeug `artikel` und Tokenbudget für Agenten

**What to build:** Das MCP-Werkzeug `artikel(titel)` liefert die Abschnitte eines Artikels, gekürzt auf ein Budget. Alle Werkzeuge halten `anzahl` und `token_budget` ein und liefern strukturierte Felder, die Agenten weiterverarbeiten können: Treffer, Quelle, Stand, Rechtslage, Normen und Entscheidungen.

**Blocked by:** 02

**Status:** ready-for-agent

- [ ] Kein Werkzeug überschreitet das Tokenbudget, auch nicht beim Abschlussbericht mit 80.000 Wörtern
- [ ] Ausgabe als strukturiertes JSON und als lesbarer Text
- [ ] `artikel` findet auch Weiterleitungen, z. B. „BtPrax“ → „Betreuungsrechtliche Praxis“
