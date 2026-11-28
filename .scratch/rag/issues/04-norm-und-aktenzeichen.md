# 04: Normen und Aktenzeichen direkt finden

**What to build:** Enthält eine Frage ein Normzitat oder ein Aktenzeichen (erkannt mit `parse_norms` und `parse_decisions`), findet `suche` die zitierenden Chunks direkt, unabhängig vom Wortlaut. Dazu kommen die MCP-Werkzeuge `norm(zitat)` und `entscheidung(aktenzeichen)`. `norm` liefert den Norm-Knoten mit Fassung und Nachfolger sowie die zitierenden Abschnitte, gruppiert nach Fassung. `entscheidung` liefert die Entscheidung mit ihren zitierenden Abschnitten.

**Blocked by:** 02

**Status:** ready-for-agent

- [ ] „§ 1831 BGB“ liefert Abschnitte getrennt nach neu, alt und unbestimmt
- [ ] „§ 1896 BGB a.F.“ nennt den Nachfolger § 1814 (bzw. § 1815)
- [ ] „XII ZB 236/05“ liefert alle zitierenden Stellen
- [ ] Normfragen im Testsatz: Recall@5 gemessen und verbessert
