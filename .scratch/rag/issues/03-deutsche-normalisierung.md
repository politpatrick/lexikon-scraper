# 03: Deutsche Normalisierung

**What to build:** Die Suche versteht Wortformen und Zusammensetzungen. Dafür gibt es Snowball-Stemming (`snowballstemmer`) und eine Zerlegung zusammengesetzter Wörter über die Wortliste des Lexikons. So findet „Wohnungskündigung“ auch „Kündigung der Wohnung“ und „Betreuerbestellung“ auch „Bestellung eines Betreuers“. Die Wirkung wird auf dem Testsatz gemessen.

**Blocked by:** 02

**Status:** ready-for-agent

- [ ] Tests mit echten Beispielen für Wortformen und Komposita
- [ ] Recall@5 und MRR gegen die Baseline aus 02 gemessen; nur übernommen, wenn besser
- [ ] Keine merkliche Verschlechterung bei Normfragen und Aktenzeichen
