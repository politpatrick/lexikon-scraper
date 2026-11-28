# 10: Experiment Vektorsuche

**What to build:** Ein lokales mehrsprachiges Embedding-Modell (ONNX, z. B. über `fastembed`) als zusätzliche Rangfolge in der Fusion. Übernommen wird es nur, wenn es Recall@5 auf dem Testsatz um mindestens 5 Prozentpunkte gegenüber BM25 plus Netz hebt. Andernfalls wird das Ergebnis dokumentiert und das Experiment verworfen.

**Blocked by:** 06

**Status:** ready-for-agent

- [ ] Messung mit und ohne Vektorsuche, einschließlich Laufzeit und Speicherbedarf
- [ ] Entscheidung nach der festen Regel (+5 Prozentpunkte), dokumentiert in ADR 0003
- [ ] Keine externen APIs
