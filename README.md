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

graphify dient nur als Abfrage- und Analyseschicht; das Netz selbst entsteht deterministisch
(ADR 0002). Installation: `uv tool install "graphifyy[mcp]"`.

```bash
python -m lexikon graphify          # graphify-out/: GRAPH_REPORT.md, graph.html (ohne LLM)
graphify explain "Betreuungsgericht"
graphify path "Einwilligungsvorbehalt" "Betreuungsgericht"
graphify path "§ 1896 BGB a.F." "§ 1814 BGB"      # alte Norm → Nachfolger
```

`graphify-out/` wird nicht committet (`.gitignore`).

### Abfrage durch Claude über MCP

`.mcp.json` richtet für Claude Code den Server `lexikon-wissensnetz` ein. Er liest
`graph/graph.json` direkt, ein vorheriger Build ist nicht nötig. Beim ersten Start in diesem
Repo fragt Claude Code, ob der Projektserver zugelassen werden soll.

Nützliche Werkzeuge:

| Frage | Werkzeug | Beispiel |
|---|---|---|
| Wie hängen zwei Begriffe zusammen? | `shortest_path` | `source: "Einwilligungsvorbehalt", target: "Betreuungsgericht"` |
| Was ist dieser Knoten? | `get_node` | `label: "§ 1896 BGB a.F."` |
| Welche Artikel zitieren eine Norm oder Entscheidung? | `get_neighbors` | `label: "§ 1831 BGB"` |
| Überblick | `graph_stats`, `god_nodes` | |

`query_graph` mit einer Frage in natürlicher Sprache ist breit (bei Normen oft tausende
Knoten); für gezielte Fragen sind `get_node` und `get_neighbors` besser.

Knoten-Präfixe: `art:` Artikel, `cat:` Kategorie, `norm:` Norm (`@aF` alte Fassung,
`@unbestimmt` Fassung unklar), `dec:` Entscheidung, `ext:` externe Quelle.

## Planung

Spec `docs/superpowers/specs/`, Pläne `docs/superpowers/plans/`, Tickets `.scratch/wissensnetz/issues/`,
Entscheidungen `docs/adr/`, Vokabular `GLOSSARY.md`.
