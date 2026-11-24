# Glossar

Fachvokabular dieses Repos. Code, Tickets und Specs verwenden genau diese Begriffe.

| Begriff | Bedeutung | Nicht verwechseln mit |
|---|---|---|
| **Lexikon** | Die Quelle: das MediaWiki unter lexikon-betreuungsrecht.de | Wissensnetz |
| **Seite** | Eine MediaWiki-Seite im Hauptnamensraum, identifiziert über `pageid` | Artikel |
| **Revision** | Ein Bearbeitungsstand einer Seite (`revid`, `timestamp`) | – |
| **Rohseite** (`RawPage`) | Unveränderter Wikitext einer Seite plus Revision und Kategorien; die Archivwahrheit | Artikel |
| **Weiterleitung** | Seite, die nur auf eine andere Seite verweist; wird nie zum Artikel, sondern aufgelöst | – |
| **Artikel** | Normalisierte Fassung einer Rohseite: Abschnitte, typisierte Links, Zitate | Seite |
| **Abschnitt** | Teil eines Artikels unter einer Überschrift; trägt einen `pfad` (`Zuständigkeit › International`) | Chunk |
| **Normzitat** (`NormRef`) | Verweis auf eine Rechtsnorm, kanonisiert als `GESETZ§NUMMER` bzw. `GESETZArt.NUMMER` ohne Leerzeichen (z. B. `BGB§1814`, `SGBXII§42`, `EGBGBArt.24`, `EGBGBArt.229§54`); Absatz und Satz gehören nicht zur ID. Die alte Fassung ist Teil der ID: `BGB§1822@aF` ist ein anderer Knoten als `BGB§1822` | Norm |
| **Norm** | Knoten im Wissensnetz für einen Paragraphen/Artikel eines Gesetzes | Normzitat |
| **Fassung** | `alt` (vor 01.01.2023) oder `neu` (ab 01.01.2023) bei betreuungsrechtlichen Normen | – |
| **Entscheidungszitat** (`DecisionRef`) | Verweis auf Rechtsprechung: Gericht, Art, Datum, Aktenzeichen | – |
| **Wissensnetz** | Die Menge aller Knoten und Kanten, exportiert als `graph/graph.json` | graphify-Ausgabe |
| **Kante** | Typisierte Beziehung: `links_to`, `in_category`, `cites_norm`, `cites_decision`, `references_external`, `superseded_by` | – |
| **Chunk** | Retrieval-Einheit des RAG, abgeleitet aus einem Abschnitt | Abschnitt |
