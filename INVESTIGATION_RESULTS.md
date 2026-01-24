# Investigation Manuelle des Scènes Problématiques

## Date: 2026-01-24

---

## Scene #14 @ 0x9A0A (danem.vnd)

### Problème Initial
- Parser rapporte: 9/9 hotspots SANS géométrie
- objCount: Non disponible (pas de signature)
- Fichier principal: `sirene.bmp`

### Investigation Binaire

**Résultat**: Scene #14 est une **FAUSSE SCÈNE** - elle est en réalité INSIDE Scene #13!

**Preuves**:
```
Scene #13 (loc6.bmp):
- Offset: 0x984B
- Signature: 0xFFFFFFF4 @ 0x9893  
- objCount: 1
- Hotspot table: 0x98AF → 0x9948 (1 hotspot × 153 bytes)
- Fin théorique: 0x9948

"Scene #14" @ 0x9A0A:
- Détectée @ 0x9A0A (0x9A0A < 0x9948 ← AVANT la fin de Scene #13!)
- PAS de signature 0xFFFFFFxx trouvée
- Le fichier "sirene.bmp" est en réalité partie des données de Scene #13
```

**Gap entre 0x9948 et 0x9A0A (194 bytes)**:
- Contient: commandes FONT (Type 39), PLAYTEXT (Type 41), IF-THEN (Type 21)
- Ces commandes appartiennent à Scene #13

### Conclusion
✗ Scene #14 n'existe PAS - c'est un artifact de gap recovery  
✓ Scene #13 continue jusqu'à Scene #15 (vraie scène suivante)  
✓ Gap recovery a créé une fausse scène à partir de données internes de Scene #13

---

## Scene #25 @ 0x1005F (belge.vnd)

### Problème Initial
- Parser rapporte: objCount=0, mais 20/20 hotspots SANS géométrie
- Fichiers: `paysliste.bmp`, `cpays 1`

### Investigation Binaire

**Résultat**: Scene #25 est une **SCÈNE PARTIELLE** sans signature - objCount=0 est CORRECT!

**Preuves**:
```
Scene #25:
- Offset: 0x1005F
- File table: paysliste.bmp (fichier valide)
- PAS de signature 0xFFFFFFxx
- objCount: 0 (PAS de hotspots attendus) ✓ CORRECT

Scene #26:
- Offset: 0x11AE9
- Signature: 0xFFFFFFE8 trouvée

Gap: 0x100B0 → 0x11AE9 (6713 bytes)
```

**Contenu du Gap (6713 bytes)**:

#### Type A: Commandes VND Standard
Format:
```
+0x00: [4 bytes] Command subtype (27/26/0a... = Type 39/38/10)
+0x04: [4 bytes] String length
+0x08: [N bytes] String data (paramètre commande)
```

Exemples trouvés:
- Type 39 (0x27): FONT `"18 0 #0000 comic sans ms"` (répété 14x)
- Type 38 (0x26): PLAYTEXT `"115 110 120 120 0 Allemagne"`
- Type 10 (0x0a): ADDBMP `"act\p1.bmp 0 226 160"`

#### Type B: Records avec Marqueurs 01/02/03...
Format:
```
+0x00: [4 bytes] Value/Index
+0x04: [4 bytes] ★ MARQUEUR TYPE ★ (01 00 00 00, 02 00 00 00, etc.)
+0x08: [4 bytes] Value/Parameter  
+0x0C: [4 bytes] String length
+0x10: [N bytes] String data
```

Exemples trouvés:
```
@ 0x100B4: Type 1, value=7, param=22, string="cpays 1"
@ 0x10223: Type 1, value=6, param=22, string="cpays 2"  
@ 0x11155: Type 2, value=15, param=22, string="numpaysscore 0"
```

**Occurrences des marqueurs dans le gap**:
- `01 00 00 00`: 75 records (Type 1)
- `02 00 00 00`: 28 records (Type 2)
- `03 00 00 00`: 2 records (Type 3)
- `06 00 00 00`: 18 records (Type 6)
- `07 00 00 00`: 30 records (Type 7)
- `08 00 00 00`: 8 records (Type 8)

**Total: ~167 records Type B**

### Conclusion
✓ Scene #25 objCount=0 est CORRECT  
✗ Les 20 "hotspots" sont FAUX - ce sont des commandes Type A (gap recovery)  
✓ Le gap contient InitScript commands + scene parameters (Type B records)  
✓ Scene #25 est une scène spéciale sans hotspots (comme vnoption.dll ou fleche.cur)

---

## Découvertes Majeures

### 1. Format Binaire VND - Deux Types de Records

**Type A: Commandes VND** (déjà documenté)
- Subtype (4B) + Length (4B) + String data (NB)
- Utilisé pour: FONT, PLAYTEXT, ADDBMP, IF-THEN, etc.

**Type B: Records avec Marqueurs** (NOUVEAU!)
- Value + **MARQUEUR** (01/02/03...) + Param + Length + String
- Utilisé pour: scene parameters, variables, config

### 2. Utilité des Marqueurs 01 00 00 00, 02 00 00 00, etc.

**Question**: Peut-on utiliser `01 00 00 00` pour délimiter plus précisément les objets VND?

**Réponse**: **OUI!** Ces marqueurs sont des DÉLIMITEURS de records Type B.

**Applications possibles**:
1. ✓ Identifier le DÉBUT d'un nouveau record Type B
2. ✓ Différencier les types de records (Type 1 vs Type 2, etc.)
3. ✓ Parser les gaps SANS créer de faux hotspots
4. ✓ Classifier correctement:
   - InitScript commands (Type A: subtypes 27/26/10...)
   - Scene parameters (Type B: marqueurs 01/02/06/07...)
   - Vrais hotspots (signature 0xFFFFFFxx + objCount + 153B×N)

**Problème actuel**: Gap recovery ne les utilise PAS → faux hotspots

**Amélioration proposée**: Scanner les gaps en utilisant ces marqueurs pour éviter les false positives.

---

## Recommandations

### Court Terme
1. ✓ Marquer Scene #14 (danem) comme INVALIDE (fausse scène)
2. ✓ Corriger Scene #25 (belge): retirer les 20 faux hotspots
3. ✓ Classifier Scene #25 comme scene type spéciale (InitScript only)

### Moyen Terme  
1. 🔄 Améliorer gap recovery:
   - Détecter marqueurs 01/02/03... pour records Type B
   - Ne PAS créer hotspots à partir de commandes Type A
   - Valider présence signature 0xFFFFFFxx avant création scène

2. 🔄 Parser Type B records correctement:
   - Extraire scene parameters (cpays, numpaysscore, etc.)
   - Les ajouter aux métadonnées de scène
   - Les distinguer des hotspots

### Long Terme
1. 📋 Documenter mapping complet Type B records:
   - Type 1 = ? (75 occurrences)
   - Type 2 = ? (28 occurrences)  
   - Type 6/7 = ? (18/30 occurrences)

2. 📋 Reverse engineering complet format VND Type B

---

## Fichiers Analysés

- `danem/danem.vnd` - Scene #14 @ 0x9A0A
- `belge/belge.vnd` - Scene #25 @ 0x1005F

## Scripts Utilisés

```python
# Hexdump analysis
struct.unpack('<I', data[offset:offset+4])

# Signature search
for probe in range(start, end):
    val = struct.unpack('<I', data[probe:probe+4])[0]
    if (val & 0xFFFFFF00) == 0xFFFFFF00:
        print(f"Signature {hex(val)} @ {hex(probe)}")

# Marker detection  
patterns = {0x01: [], 0x02: [], ...}
for addr in range(gap_start, gap_end):
    val = struct.unpack('<I', data[addr:addr+4])[0]
    if val in patterns:
        patterns[val].append(hex(addr))
```

---

**Statut**: Investigation complète ✓  
**Prochaine étape**: Améliorer gap recovery avec détection marqueurs Type B
