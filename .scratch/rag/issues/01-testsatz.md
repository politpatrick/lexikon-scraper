# 01: Testsatz und Bewertung

**What to build:** Ein Testsatz `eval/fragen.jsonl` mit mindestens 50 Fragen und erwarteten Artikeln, optional mit Abschnitt. Dazu ein Bewertungsskript, das jede Suchfunktion mit der Signatur `suche(frage) -> Ergebnis` misst: Recall@5, MRR und den Anteil richtig erkannter „nicht beantwortbar“-Fälle. Den Entwurf mit 40 Fragen erstellt der Agent aus den Daten, die Fachkraft prüft ihn und ergänzt 10 Fragen aus der Praxis.

**Blocked by:** None (can start immediately)

**Status:** needs-human (Prüfung und Ergänzung durch die Fachkraft)

- [ ] Mischung: Alltagsfragen in Laiensprache, Fachfragen, Normfragen („§ 1831 BGB“), Aktenzeichen, Fragen zur alten Rechtslage
- [ ] Mindestens 5 Fragen, die das Lexikon nicht beantwortet (erwartet: leeres oder schwaches Ergebnis)
- [ ] Erwartete Artikel sind gegen `articles/` geprüft (Titel existieren)
- [ ] Das Bewertungsskript läuft gegen eine triviale Referenzsuche (Titeltreffer) und gibt die Metriken aus
- [ ] Fachkraft hat den Entwurf freigegeben und 10 eigene Fragen ergänzt
