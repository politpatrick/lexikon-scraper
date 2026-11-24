# ADR 0002: graphify ist Abfrage- und Analyseschicht, nicht Extraktor

**Status:** vorgeschlagen · 2026-11-24

## Kontext
graphify kann Dokumente per LLM in einen Wissensgraph übersetzen. Es kann aber auch
einen fertigen `graph.json` übernehmen (`graphify cluster-only`). Darauf bietet es
Community-Erkennung, `GRAPH_REPORT.md`, `graph.html`, `explain`, `path` und einen
MCP-Server (`graphify-mcp`) für Agenten.

Prototyp am 24.11.2026 mit den vorhandenen `artikel/`-Daten: 1.599 Knoten
(Artikel + per Regex erkannte Normen), 11.092 Kanten, 51 Communities, 0 Tokens
LLM-Kosten. `graphify explain "§ 1814 BGB"` lieferte die 34 zitierenden Artikel.

## Entscheidung
- Das Wissensnetz wird deterministisch aus Links, Kategorien und Zitaten gebaut. Alle
  Kanten tragen `confidence: "EXTRACTED"`.
- Der Export ist graphify-kompatibel: Knoten `{id, label, source_file, file_type}`,
  Kanten `{source, target, relation, confidence, source_file}`.
- graphify wird ohne LLM-Extraktion genutzt, für Clustering, Visualisierung, Report und
  Agentenzugriff per MCP.
- Die semantische LLM-Extraktion von graphify wird höchstens einmal als Vergleich
  eingesetzt, nicht im täglichen Lauf.

## Folgen
- Kein nicht-deterministischer, kostenpflichtiger Schritt im Kernpfad.
- graphify fasst parallele Kanten zwischen denselben Knoten zusammen (13.663 → 11.092 im
  Prototyp). Für Zählungen gilt deshalb unser eigener Export, nicht graphifys `graph.json`.
- Ohne `--no-label` benennt graphify Communities per LLM. Optional; ohne LLM heißen sie
  „Community N“.
