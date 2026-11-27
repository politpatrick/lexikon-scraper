# 05: Alte und neue Fassung kennzeichnen

**What to build:** Normzitate des Betreuungsrechts tragen die Fassung `alt` oder `neu`. Alte Normen zeigen per `superseded_by` auf ihre Nachfolger. Der Bericht listet Artikel, die nur altes Recht zitieren, als Prüfliste für die Pflege des Lexikons.

**Blocked by:** 04

**Status:** umgesetzt 27.11.2026 (nach Review überarbeitet), Zuordnungstabelle wartet auf Stichprobenprüfung. Live: alt 449, neu 392, unbestimmt 684; Stichprobe neu 24/25 richtig (1 unklar), alt ohne Fehler im Review

- [ ] Zuordnungstabelle für §§ 1896–1908k BGB a.F. → §§ 1814 ff. BGB n.F. ist fachlich freigegeben
- [x] `§ 1896 BGB` hat `fassung=alt` und eine Kante `superseded_by` → `BGB§1814`
- [x] Der Bericht nennt alle Artikel, die nur altes Recht zitieren

## Entscheidungen (27.11.2026)

- Doppeldeutige Nummern (§§ 1773–1888 BGB ohne „a.F.“): Kontext, sonst `unbestimmt`.
- Ein Abschnitt mit nur alten Bezügen ergibt bewusst NICHT „alt“: Die Stichprobe zeigte
  rund 5/12 Treffer, weil umgestellte Artikel altes Recht zum Vergleich nennen. „alt“ nur
  bei Hinweis am Zitat oder bei Nummern, die es seit 2023 nicht mehr gibt.
- Vermerk „Seite ist an die Rechtslage ab 1.1.23 angepasst“ wird nicht genutzt
  (Stichprobe: rund 8/13 richtig).
- Zuordnung aus der im Lexikon verlinkten Synopse; drei Zeilen ergänzt (§ 1898, § 1899,
  § 1904 a.F.), weil sie im PDF-Auszug fehlen.
- Nach Review: Kettenregel (§§ 1908i …, 1821 BGB → alt), jede Entscheidung vor 2023 blockiert
  „neu“ aus dem Abschnitt, §§ 1858–1881 (im alten Recht weggefallen) → neu, „n.F.“/„neues Recht“
  nur noch als Hinweis am Zitat oder mit Bezug auf die Reform 2023. Bekannte Restfehler:
  „§ 1908 i“ mit Leerzeichen wird nicht als § 1908i erkannt (Genehmigungspflichten § 1829/§ 1831).
