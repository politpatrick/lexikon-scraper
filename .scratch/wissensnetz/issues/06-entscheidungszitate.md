# 06: Entscheidungszitate durch alle Schichten

**What to build:** Zitierte Rechtsprechung wird als Entscheidungszitat mit Gericht, Art, Datum und Aktenzeichen erkannt. Am Artikel ist sie gespeichert, im Wissensnetz wird sie zum `decision`-Knoten mit `cites_decision`-Kante. Mehrere Artikel, die dieselbe Entscheidung zitieren, teilen sich einen Knoten.

**Blocked by:** 03 (und 02, falls Entscheidungen per Vorlage zitiert werden)

**Status:** erledigt 27.11.2026 (nach Review überarbeitet). 2.565 Entscheidungen, davon 241 BayObLG; 30/30 Stichproben richtig; 4,3 % der Aktenzeichen-Kandidaten nach Gerichtsnamen unerkannt

- [x] `LG Augsburg, Beschluss vom 30. Januar 2018 – 054 T 161/18` wird vollständig erkannt
- [x] `BGH XII ZB 123/20` ohne Datum wird erkannt
- [x] Identisches Aktenzeichen + Gericht ergibt genau einen Knoten
