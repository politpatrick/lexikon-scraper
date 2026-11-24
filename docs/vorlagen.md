# Vorlagen im Lexikon und ihre Behandlung

Stand: Inventur vom 24.11.2026 aus `raw/` (10 Vorlagen, 1.113 Vorkommen). Die aktuelle
Zählung erzeugt jeder Build in `reports/vorlagen.md`. Die Regeln stehen in
`src/lexikon/templates.py` (`RULES`).

Die **Textdarstellung** folgt der Definition der Vorlage im Lexikon. Der Archivtext zeigt also,
was Leser im Wiki sehen. Darüber muss niemand entscheiden. Fachlich festzulegen ist nur die
**strukturierte Auswertung** in Ticket 04 und 06.

| Vorlage | Vorkommen | Definition im Wiki | Text | Strukturiert (Ticket) |
|---|---|---|---|---|
| `Zitat de §` | 793 in 88 Artikeln | `{{Zitat de §\|P\|gesetz}}` → Link „§ P“ auf gesetze-im-internet.de; das Gesetzeskürzel steht dahinter im Text | `§ P` | Normzitat (04): Gesetz aus 2. Parameter (juris-Kürzel, z. B. `bgb`, `sgb_1`, `btog`) |
| `Zitat-dej` | 136 in 19 | `{{Zitat-dej\|§/§§/Art.\|P\|GESETZ}}` → Link auf dejure.org | `§ P`, `§§ P`, `Art. P` | Normzitat (04): Gesetz aus 3. Parameter (dejure-Kürzel) |
| `Zitat Art` | 42 in 19 | `{{Zitat Art\|A\|gesetz}}` → „Art. A“ | `Art. A` | Normzitat (04) |
| `Rspr` / `rspr` | 111 in 36 | `{{Rspr\|Az. oder Fundstelle}}` → Link auf dejure.org | Parameter wörtlich | Entscheidungszitat (06) |
| `Quelle Wikipedia` | 24 in 24 | Quellenhinweis auf übernommene Wikipedia-Texte (die Vorlage selbst ist im Wiki nicht lesbar) | `Quelle: Wikipedia, Artikel „…“, Stand …` | Hinweis auf Lizenz der Wikipedia-Texte (CC BY-SA) |
| `Infobox Publikation` | 1 | Infobox | `feld: wert` je Zeile | – |
| `ISSN` | 1 | ISSN-Link | `ISSN …` | – |
| `PAGENAME` | 1 | Seitentitel | Seitentitel | – |
| `TOC`, `Prettytable-R Gesetz` | je 2 | Layout | verworfen | – |

## Befund zu den verlorenen Normverweisen

Der alte Scraper entfernte alle Vorlagen mit `strip_code()`. Dadurch fehlte jeder über
`Zitat de §`, `Zitat-dej` und `Zitat Art` gesetzte Paragraph. Aus „nach Maßgabe von
{{Zitat de §|37|…}} des Landesgesetzes“ wurde so „nach Maßgabe von  des Landesgesetzes“.
Der neue Build zeigt „nach Maßgabe von § 37 des Landesgesetzes“.

## Hinweis für Ticket 04

Das Gesetz steht in den Vorlagen als **URL-Kürzel** (juris: `bgb`, `sgb_1`, `bgbeg`;
dejure: `BGB`, `SGB_XI`), nicht als Zitierform. Ticket 04 braucht deshalb eine Zuordnung
URL-Kürzel → kanonisches Kürzel (`sgb_1` → `SGBI`). Die Vorlagen sind die verlässlichere
Quelle für Normzitate als Regex auf Fließtext. Regex ist nur für Verweise ohne Vorlage nötig.
