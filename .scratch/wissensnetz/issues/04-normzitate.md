# 04: Normzitate durch alle Schichten

**What to build:** Normverweise erscheinen im Artikeltext wieder vollständig und stehen zusätzlich als strukturierte Normzitate am Artikel und am Abschnitt. Im Wissensnetz werden sie zu `norm`-Knoten mit `cites_norm`-Kanten. Der Bericht listet die meistzitierten Normen. Die Frage „Welche Artikel zitieren § 1831 BGB?“ ist mit `graphify explain` beantwortbar.

**Blocked by:** 02, 03

**Status:** erledigt 24.11.2026. 1.449 Normen in 272 von 317 Artikeln, 4.825 cites_norm-Kanten; die zwei Lücken-Verdachtsfälle stehen so im Original

- [x] Regression: Der Satz aus „Betreuungsverfahren“ mit „vgl.  Abs. 3 SGB-I“ enthält wieder die Paragraphennummer
- [x] Tabellentests: `§§ 99, 104 FamFG`, `§ 272 Abs. 2 FamFG`, `Art. 24 EGBGB`, `§ 15, § 19 RPflG`, `§§ 1814 ff. BGB`, `§ 1896 BGB a.F.`
- [x] Abkürzungen sind normalisiert (`SGB-I`, `SGB I` → `SGBI`)
- [x] Kein Artikel mehr mit sichtbar gelöschtem Normverweis (Prüfskript im Bericht)
