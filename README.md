# Lexikon Betreuungsrecht: Archiv und Wissensnetz

Spiegelt das [Lexikon Betreuungsrecht](https://www.lexikon-betreuungsrecht.de) verlustfrei
und baut daraus ein Wissensnetz für Recherche und RAG.

| Verzeichnis | Inhalt |
|---|---|
| `raw/` | Rohseiten: unveränderter Wikitext je Seite mit Revision (Archivwahrheit, ADR 0001) |
| `articles/` | Artikel: Abschnitte mit Pfad, typisierte Links, Normzitate (mit Fassung), Entscheidungen |
| `graph/graph.json` | Wissensnetz, graphify-kompatibel (ADR 0002) |
| `reports/qualitaet.md` | Kennzahlen, Waisen, tote Links, Normen, Entscheidungen, alte/neue Fassung |
| `reports/vorlagen.md` | Inventur der Wiki-Vorlagen |

Das frühere Format `artikel/` wurde am 28.11.2026 entfernt (Ticket 08); die Git-Historie enthält jeden Stand.

## Nutzung

```bash
pip install -e ".[dev]"
pytest
python -m lexikon archive   # braucht Zugriff auf die Wiki-API
python -m lexikon build     # offline aus raw/
```

Der Workflow `.github/workflows/wissensnetz.yml` führt beides täglich aus.

## Abfragen mit graphify

```bash
mkdir -p graphify-out && cp graph/graph.json graphify-out/
graphify cluster-only . --no-label
graphify explain "Betreuungsgericht"
graphify path "Einwilligungsvorbehalt" "Betreuungsgericht"
```

## Planung

Spec `docs/superpowers/specs/`, Pläne `docs/superpowers/plans/`, Tickets `.scratch/wissensnetz/issues/`,
Entscheidungen `docs/adr/`, Vokabular `GLOSSARY.md`.
