# Spec: RAG über das Lexikon Betreuungsrecht

**Status:** freigegeben 28.11.2026 · Tickets: `.scratch/rag/issues/`
**Vokabular:** `GLOSSARY.md` (neu: Chunk, Treffer, Testsatz) · **ADRs:** 0001, 0002 · **Vorgänger-Spec:** `2026-11-24-wissensnetz-design.md`

## Problem Statement

Das Wissensnetz ist fertig: 317 Artikel in 3.235 Abschnitten, 1.725 Normen (mit Fassung
alt/neu/unbestimmt), 2.565 Entscheidungen, typisierte Links. Fragen wie „Brauche ich für die
Kündigung der Wohnung meiner Betreuten eine Genehmigung?“ lassen sich damit aber noch nicht
beantworten. Das Lexikon hat rund 1,2 Mio. Tokens, zu viel für einen Prompt.

Die Nutzer reichen von dir als Fachkraft über Ehrenamtliche bis zu Betroffenen und Angehörigen,
dazu Agenten wie deine Arbeitshilfen- und Bericht-Skills. Für Laien ist das größte Risiko eine
Antwort, die altes Recht als geltendes ausgibt. Viele Abschnitte zitieren noch die Rechtslage vor
2023, und bei 684 Zitaten ist die Fassung nicht bestimmbar.

## Solution

Ein MCP-Server `lexikon-rag` liefert zu einer Frage die passenden Abschnitte mit Quelle, Stand
und Kennzeichnung der Rechtslage. Claude formuliert daraus die Antwort. Der Server enthält kein
Sprachmodell und braucht keinen API-Schlüssel.

**Suche:** Zuerst BM25-Stichwortsuche. Die Abfrage wird um das Wissensnetz ergänzt: direkte
Treffer für zitierte Normen und Aktenzeichen, dazu verlinkte Artikel. Eine Vektorsuche kommt nur
hinzu, wenn sie auf einem Testsatz messbar besser abschneidet.

**Stufen:**
1. **Stufe 1:** MCP für dich und für Agenten, lokal und in Claude Code.
2. **Stufe 2:** Zugang für Ehrenamtliche und Betroffene, zum Beispiel als entfernter
   MCP-Connector oder als Web-Oberfläche. Blockiert durch die Lizenzfrage und durch
   Haftungshinweise; dafür entsteht eine eigene Spec.

## User Stories

**Fachkraft**
1. Als Fachkraft will ich eine Frage in eigenen Worten stellen und die 5–10 passendsten Abschnitte mit Artikel und Überschriftenpfad bekommen, damit ich die Antwort selbst prüfen kann.
2. Als Fachkraft will ich, dass jeder Treffer auf die Seite im Lexikon verweist, damit ich den vollständigen Kontext lesen kann.
3. Als Fachkraft will ich den Stand jedes Treffers sehen (Revision, Datum), damit ich weiß, wie aktuell er ist.
4. Als Fachkraft will ich, dass Treffer mit alter Fassung ausdrücklich als „Rechtslage vor 2023“ markiert sind, damit ich sie nicht für geltendes Recht halte.
5. Als Fachkraft will ich bei unbestimmter Fassung beide Lesarten genannt bekommen (z. B. § 1821 a.F. Grundstücksgeschäfte / n.F. Wünsche), damit ich selbst entscheiden kann.
6. Als Fachkraft will ich nach einer Norm fragen („§ 1831 BGB“) und alle Artikel und Abschnitte bekommen, die sie zitieren, getrennt nach Fassung.
7. Als Fachkraft will ich nach einem Aktenzeichen fragen („XII ZB 236/05“) und alle Stellen bekommen, die die Entscheidung zitieren.
8. Als Fachkraft will ich zu einer alten Norm den Nachfolger erfahren („§ 1896 a.F. → § 1814“).
9. Als Fachkraft will ich, dass die Suche Wortformen und Zusammensetzungen versteht („Wohnungskündigung“ findet „Kündigung der Wohnung“).
10. Als Fachkraft will ich verwandte Artikel angezeigt bekommen, die nicht im Wortlaut passen, aber im Lexikon verlinkt sind.

**Ehrenamtliche (Stufe 2, bei der Antwortgestaltung schon jetzt berücksichtigt)**
11. Als Ehrenamtliche will ich Antworten in einfacher Sprache mit Quelle, damit ich sie verstehe und nachlesen kann.
12. Als Ehrenamtliche will ich bei unsicherer oder alter Rechtslage den Hinweis bekommen, beim Betreuungsgericht oder Betreuungsverein nachzufragen.
13. Als Ehrenamtliche will ich erkennen, wenn das Lexikon meine Frage nicht beantwortet, statt eine erfundene Antwort zu bekommen.

**Betroffene und Angehörige (Stufe 2)**
14. Als Betroffener will ich einen klaren Hinweis, dass die Antwort keine Rechtsberatung ist.
15. Als Angehöriger will ich Antworten, die Fachbegriffe erklären und auf die passende Lexikonseite verweisen.

**Agenten**
16. Als Agent (z. B. Skill für Betreuerberichte) will ich ein Werkzeug mit strukturierter Antwort (Treffer, Normen, Fassung, Quelle), damit ich sie weiterverarbeiten kann.
17. Als Agent will ich eine Norm nachschlagen und ihre Fassung und ihren Nachfolger erhalten.
18. Als Agent will ich die Treffermenge begrenzen (Anzahl, Tokenbudget), damit mein Kontext nicht überläuft.

**Pflege**
19. Als Pfleger des Repos will ich, dass der Suchindex aus `articles/` und `graph/` reproduzierbar entsteht, ohne Binärdateien im Repo.
20. Als Pfleger will ich einen Testsatz mit Fragen und erwarteten Artikeln, damit jede Änderung an der Suche messbar ist (Recall@5, MRR).
21. Als Pfleger will ich, dass der tägliche Lauf neue Lexikoninhalte automatisch in den Index bringt.
22. Als Pfleger will ich Fragen protokollieren können, die keinen guten Treffer haben, damit ich Lücken im Lexikon oder in der Suche erkenne.

## Implementation Decisions

- **Chunks:** abgeleitet aus Abschnitten.
  - Lange Abschnitte werden an Absatzgrenzen geteilt. Zielgröße etwa 250–400 Wörter, Überlappung ein Absatz.
  - Kurze Abschnitte unter etwa 40 Wörtern werden mit dem folgenden Abschnitt desselben Artikels verbunden.
  - Jeder Chunk trägt einen Kontextkopf „Artikel › Pfad“, der mitindexiert wird.
  - Metadaten:
    - Artikel, Pfad, `pageid`, `revid`, Zeitstempel, Kategorien
    - Normen mit Fassung, Entscheidungen
    - Kennzeichen `enthaelt_alte_fassung` und `enthaelt_unbestimmte_fassung`
- **Index:** SQLite FTS5 mit BM25.
  - Für Deutsch wird vor dem Indexieren normalisiert: Kleinschreibung, Snowball-Stemming (`snowballstemmer`, reines Python). Dazu kommt eine einfache Kompositazerlegung über die Wortliste des Lexikons, damit „Wohnungskündigung“ auch „Wohnung“ und „Kündigung“ findet.
  - Der Index wird beim Start aus `articles/` gebaut (wenige Sekunden) oder aus einem Cache geladen. Er wird nicht committet.
- **Abfrage:**
  1. Normzitate und Aktenzeichen in der Frage erkennen, mit `parse_norms` und `parse_decisions`. Chunks, die sie zitieren, werden direkt gefunden, unabhängig vom Wortlaut.
  2. BM25 über Text und Kontextkopf.
  3. Netzerweiterung: Artikel, die von den besten Treffern per `links_to` verlinkt sind, mit Abschlag. Für alte Normen kommt der Nachfolger per `superseded_by` dazu.
  4. Zusammenführung per Reciprocal Rank Fusion. Ergebnis: höchstens k Chunks und ein Tokenbudget.
- **Rechtslage:**
  - Jeder Treffer trägt `rechtslage`: `aktuell`, `vor_2023`, `unbestimmt` oder `ohne_bezug`.
  - Für `unbestimmt` liefert der Server beide Lesarten, bei bekannter Zuordnung mit dem Nachfolger.
  - Die Werkzeugbeschreibung verpflichtet Claude, alte Rechtslage zu kennzeichnen und Quellen zu nennen.
  - Treffer mit alter Fassung werden gefunden, nicht ausgeschlossen; viel Rechtsprechung vor 2023 gilt sinngemäß weiter.
- **MCP-Server `lexikon-rag`** (stdio, Python, im Paket `lexikon`):
  - `suche(frage, anzahl=8, token_budget=4000)`: Treffer mit Text, Quelle (Artikel, Pfad, Lexikon-URL), Stand, Rechtslage, Normen, Entscheidungen.
  - `norm(zitat)`: Norm-Knoten, Fassung, Nachfolger und zitierende Abschnitte, gruppiert nach Fassung.
  - `entscheidung(aktenzeichen)`: Entscheidung und zitierende Abschnitte.
  - `artikel(titel)`: Abschnitte eines Artikels, gekürzt auf das Budget.
  - Eingerichtet wird der Server in `.mcp.json` neben `lexikon-wissensnetz`.
- **Testsatz** `eval/fragen.jsonl`: mindestens 40 Fragen mit erwarteten Artikeln, optional mit Abschnitt.
  - Gemischt aus Alltagsfragen, Normfragen, Aktenzeichen und Fragen zur alten Rechtslage. Dazu Fragen, die das Lexikon **nicht** beantwortet; erwartet wird dort ein leeres oder schwaches Ergebnis.
  - Ein Entwurf entsteht aus den Daten, du prüfst und ergänzt ihn.
  - Metriken: Recall@5, MRR, Anteil richtiger „nicht beantwortbar“-Fälle. Das Bewertungsskript liegt im Repo.
- **Vektorsuche:** Ein lokales mehrsprachiges Modell (ONNX, z. B. über `fastembed`) wird nur eingebaut, wenn es im Testsatz Recall@5 um mindestens 5 Prozentpunkte über BM25 plus Netz hebt. Embeddings über eine API sind ausgeschlossen.

## Testing Decisions

- **Testnaht:** Die Funktion `suche(frage, …) -> Ergebnis` ist die einzige Naht für das Suchverhalten.
  - Der MCP-Server ist eine dünne Schicht darüber und wird mit einem echten Handshake geprüft, wie `lexikon-wissensnetz` in Ticket 07.
  - Chunking und Normalisierung werden über ihre Ausgaben getestet, nicht über Interna.
- **Fixtures:** Ein kleiner Artikelsatz aus echten Daten, mit langen und kurzen Abschnitten, alter und unbestimmter Fassung sowie Normzitaten.
- **Qualität:** Sie wird mit dem Testsatz gemessen, nicht mit Unit-Tests. Ein Test schlägt fehl, wenn Recall@5 unter die festgehaltene Baseline fällt.
- **Stichproben:** Prüfungen der Treffer müssen groß genug sein, mindestens 25 je Kategorie, und beide Richtungen abdecken: falsche Treffer und fehlende Treffer. Bei den Tickets 04 bis 06 hatten zu kleine Stichproben Fehlerraten von 8–40 % übersehen.
- **Vorbild:** `tests/test_cli.py` für Ende-zu-Ende-Tests mit `tmp_path`, der MCP-Handshake aus Ticket 07.

## Out of Scope

- Stufe 2 (öffentlicher Zugang für Ehrenamtliche und Betroffene): eigene Spec, nach Klärung von Lizenz und Haftung.
- Antwortgenerierung im Server (Claude formuliert).
- Embeddings über externe APIs.
- Hosting, Nutzerverwaltung, Kostenkontrolle.
- Volltexte der Gesetze; nur Verweise auf gesetze-im-internet.de und Open Legal Data.
- Falldaten oder personenbezogene Daten im Index.

## Further Notes

**Offene Fragen:**
1. ~~Wer erstellt den Testsatz?~~ Entschieden: Agent entwirft 40 Fragen, Fachkraft prüft und ergänzt 10 (Ticket 01).
2. ~~Nicht lesbare Seiten?~~ Entschieden: Titel und Weiterleitungsziel werden bekannt (Ticket 08).
3. Stufe 2 setzt die Lizenzklärung voraus. Dazu gehören die 24 Artikel mit `{{Quelle Wikipedia}}`, die unter CC BY-SA stehen und deshalb mit Namensnennung und Weitergabe unter gleicher Lizenz verbunden sind.

**Bekannte Grenzen aus dem Wissensnetz:**
- 684 Zitate mit unbestimmter Fassung, alle gekennzeichnet.
- Restfehler bei „§ 1908 i“ mit Leerzeichen.
- 4,3 % übersehene Aktenzeichen.
