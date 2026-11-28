# 06: Netzerweiterung und Rangfolge

**What to build:** `suche` bezieht das Wissensnetz ein: per `links_to` verlinkte Artikel der besten Treffer (mit Abschlag) und für alte Normen den Nachfolger per `superseded_by`. Die Rangfolgen werden per Reciprocal Rank Fusion zusammengeführt. Übernommen wird nur, was auf dem Testsatz messbar besser ist.

**Blocked by:** 03, 04

**Status:** ready-for-agent

- [ ] Recall@5 und MRR für jede Variante gemessen (ohne Netz, mit Links, mit Nachfolgern, mit beidem)
- [ ] Nur messbar bessere Varianten bleiben; das Ergebnis steht im Ticket
- [ ] Die Baseline im Test ist auf den neuen Stand angehoben
