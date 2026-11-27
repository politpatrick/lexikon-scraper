# 06: Entscheidungszitate durch alle Schichten

**What to build:** Zitierte Rechtsprechung wird als Entscheidungszitat mit Gericht, Art, Datum und Aktenzeichen erkannt. Am Artikel ist sie gespeichert, im Wissensnetz wird sie zum `decision`-Knoten mit `cites_decision`-Kante. Mehrere Artikel, die dieselbe Entscheidung zitieren, teilen sich einen Knoten.

**Blocked by:** 03 (und 02, falls Entscheidungen per Vorlage zitiert werden)

**Status:** erledigt 27.11.2026. 1.915 Entscheidungen in 159 Artikeln, 2.667 cites_decision-Kanten

- [x] `LG Augsburg, Beschluss vom 30. Januar 2018 – 054 T 161/18` wird vollständig erkannt
- [x] `BGH XII ZB 123/20` ohne Datum wird erkannt
- [x] Identisches Aktenzeichen + Gericht ergibt genau einen Knoten
