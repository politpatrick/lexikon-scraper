# 03: Tracer Bullet: Rohseite → Artikel → Wissensnetz → Bericht

**What to build:** Aus `raw/` entstehen Artikel mit Abschnittspfaden und typisierten Links (intern, Wikipedia, Bild, extern). Weiterleitungen sind aufgelöst. Daraus entsteht ein graphify-kompatibles `graph/graph.json` mit Artikel- und Kategorieknoten sowie `links_to`, `in_category` und `references_external`. Ein Qualitätsbericht nennt Waisen und tote Links. Alles läuft im neuen Workflow.

**Blocked by:** 01

**Status:** implementiert, wartet auf ersten Live-Lauf im Workflow (Kriterien mit echten Daten prüfen)

- [ ] Kein Wikipedia- oder Bild-Link erscheint als `links_to`
- [ ] Tote interne Links sinken deutlich unter die heutigen 564 (Restliste im Bericht)
- [ ] Jede Kante referenziert existierende Knoten und hat `confidence` und `source_file`
- [ ] `graphify cluster-only` läuft auf dem Export ohne Pflichtfeld-Warnungen
- [ ] Abschnittspfade bilden die Überschriftenhierarchie ab (`Zuständigkeit › International zuständig`)
