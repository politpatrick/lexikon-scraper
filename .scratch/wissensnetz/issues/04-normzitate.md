# 04: Normzitate durch alle Schichten

**What to build:** Normverweise erscheinen im Artikeltext wieder vollständig und stehen zusätzlich als strukturierte Normzitate am Artikel und am Abschnitt. Im Wissensnetz werden sie zu `norm`-Knoten mit `cites_norm`-Kanten. Der Bericht listet die meistzitierten Normen. Die Frage „Welche Artikel zitieren § 1831 BGB?“ ist mit `graphify explain` beantwortbar.

**Blocked by:** 02, 03

**Status:** ready-for-agent

- [ ] Regression: Der Satz aus „Betreuungsverfahren“ mit „vgl.  Abs. 3 SGB-I“ enthält wieder die Paragraphennummer
- [ ] Tabellentests: `§§ 99, 104 FamFG`, `§ 272 Abs. 2 FamFG`, `Art. 24 EGBGB`, `§ 15, § 19 RPflG`, `§§ 1814 ff. BGB`, `§ 1896 BGB a.F.`
- [ ] Abkürzungen sind normalisiert (`SGB-I`, `SGB I` → `SGBI`)
- [ ] Kein Artikel mehr mit sichtbar gelöschtem Normverweis (Prüfskript im Bericht)
