# 05: Rechtslage je Treffer

**What to build:** Jeder Treffer trägt `rechtslage`: `aktuell`, `vor_2023`, `unbestimmt` oder `ohne_bezug`, abgeleitet aus den Fassungen seiner Normzitate. Bei `unbestimmt` liefert der Server beide Lesarten, bei bekannter Zuordnung mit Nachfolger. Die Werkzeugbeschreibung verpflichtet Claude dazu,
- alte Rechtslage ausdrücklich zu kennzeichnen,
- Quellen zu nennen,
- bei „nicht beantwortbar“ nichts zu erfinden,
- Laien auf das Betreuungsgericht oder den Betreuungsverein zu verweisen.

**Blocked by:** 02

**Status:** ready-for-agent

- [ ] Regeln für `rechtslage` getestet, auch für gemischte Chunks
- [ ] Beide Lesarten mit Inhaltsbeschreibung, z. B. § 1821 a.F. Grundstücksgeschäfte / n.F. Wünsche
- [ ] Stichprobe: 25 Treffer mit `vor_2023` und 25 mit `aktuell` gegen den Text geprüft
- [ ] Werkzeugbeschreibung durch die Fachkraft geprüft (HITL)
