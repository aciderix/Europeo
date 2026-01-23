# Format VND Binaire - Validé par Analyse Empirique

**Date**: 2026-01-23  
**Validation**: danem.vnd, belge.vnd  
**Méthode**: Comparaison pseudo-code (sub_41721D) vs binaire réel

---

## ✅ Structure Header VND (Validée)

### Layout Binaire

```
Offset | Taille | Type    | Description                    | Validé
-------|--------|---------|--------------------------------|--------
0-4    | 5 B    | bytes   | Header mystérieux              | ✓
5-14   | var    | Pascal  | Magic "VNFILE"                 | ✓
15-22  | var    | Pascal  | Version (ex: "2.13")           | ✓
23-?   | var    | Pascal  | Project name                   | ✓
?-?    | var    | Pascal  | Author                         | ✓
?-?    | var    | Pascal  | Serial                         | ✓
78-97  | 20 B   | 5×int32 | Config (width, height, ...)    | ✓
98-99  | 2 B    | Word    | SCENE COUNT                    | ✓
100-101| 2 B    | Word    | EXIT_ID                        | ✓
102-103| 2 B    | Word    | INDEX_ID                       | ✓
104-?  | var    | ...     | File Table / Scenes            | Partiel
```

### Validation Empirique

#### danem.vnd
```
Config offset:    78
Scene Count:      16 ✓ (parser: 16)
EXIT_ID:          0
INDEX_ID:         0
Signature 0xFFFFFFF4 à: 4540
```

#### belge.vnd
```
Config offset:    78
Scene Count:      28 ⚠️ (parser: 27, diff = 1 scène Empty/Toolbar?)
EXIT_ID:          0
INDEX_ID:         0
```

---

## 🔍 Découvertes Majeures

### 1. Magic String = "VNFILE" (Majuscules!)

**Pseudo-code disait**: `"VnFile"`  
**Réalité**: `"VNFILE"` (6 bytes ASCII majuscules)

**Format**: String Pascal (4 bytes length + data)

### 2. Scene Count vs Hotspot Count

**Confusion dans pseudo-code**: Variable appelée "Word" pour "hotspot count"  
**Réalité**: C'est le **nombre total de scènes** dans le VND!

```cpp
// sub_41721D ligne 9950
Word = ipstream::readWord(&v21);  // Nombre de SCÈNES, pas hotspots!

for (i = 0; i < Word; ++i) {
    // Parser scène i
}
```

### 3. EXIT_ID et INDEX_ID - Trouvés!

**Emplacement confirmé**:
- EXIT_ID: Word à offset fixe (config_offset + 22)
- INDEX_ID: Word à offset fixe (config_offset + 24)

**Pseudo-code ligne 9961-9962**:
```cpp
*(_DWORD *)((char *)a1 + 61) = ipstream::readWord(&v21);  // EXIT_ID
*(_DWORD *)((char *)a1 + 65) = ipstream::readWord(&v21);  // INDEX_ID
```

✓ Validé dans danem.vnd et belge.vnd (valeur: 0)

### 4. Config Structure

**5 int32 (20 bytes total)**:
```
Config[0]: Width (640 ou 800)
Config[1]: Height (480 ou 600)
Config[2]: ?? (16)
Config[3]: ?? (1)
Config[4]: ?? (10 pour danem, 19 pour belge)
```

### 5. Scene Markers (Signatures)

**Signature magique**: `0xFFFFFFF4` pour danem/belge

**Format** (observé):
```
[File Table]
[InitScript Commands]
[Config Header]
objCount (2 bytes Word)  ← Nombre de hotspots de cette scène
Signature (4 bytes)      ← 0xFFFFFFF4 ou autre
5 × int32                ← Config scène
[Hotspots...]
```

**Validation**: Signature trouvée à offset 4540 dans danem.vnd

---

## 📊 Comparaison Pseudo-Code vs Réalité

| Aspect | Pseudo-Code | Réalité Binaire | Match |
|--------|-------------|-----------------|-------|
| Magic String | "VnFile" | "VNFILE" | ❌ (casse) |
| Magic Format | `operator>>` (C++ string) | Pascal (length+data) | ⚠️ |
| "Word" variable | Hotspot count | **Scene count** | ❌ |
| EXIT_ID offset | +61 (struct) | config+22 (binaire) | ✓ (logique) |
| INDEX_ID offset | +65 (struct) | config+24 (binaire) | ✓ (logique) |
| Config size | 5 int32 | 5 int32 (20 bytes) | ✓ |
| Scene signature | 0xFFFFFFxx | 0xFFFFFFF4 | ✓ |

**Note**: Les offsets du pseudo-code sont des offsets de **structure C++ en mémoire**, pas des offsets dans le fichier binaire. La correspondance logique est correcte.

---

## 🎯 Impact sur le Parser

### Améliorations Possibles

1. **Lire EXIT_ID et INDEX_ID** depuis header
   - Actuellement ignorés par notre parser
   - Utiles pour navigation (bouton "Quitter")

2. **Validation Scene Count**
   - Vérifier que nombre de scènes parsées == Scene Count du header
   - Aider à détecter erreurs de parsing

3. **Config Header**
   - Extraire width/height depuis config
   - Valider dimensions scènes

4. **Scene Marker Validation**
   - Chercher signature AVANT d'accepter une scène candidate
   - objCount avant signature doit matcher nombre de hotspots

### Problèmes Identifiés

1. **belge.vnd**: Scene count = 28, parser = 27
   - Différence de 1 scène
   - Probablement une scène "Empty" ou "Toolbar" filtrée
   - À investiguer

2. **File Table cryptée**: Non encore analysée
   - Pseudo-code dit: clé "Password"
   - Version >= 0x2000D seulement

---

## 🔬 Prochaines Validations

- [ ] Analyser la file table (cryptée?)
- [ ] Vérifier version code dans header
- [ ] Parser structure Hotspot (153 bytes)
- [ ] Valider commandes (subtype à offset +8)
- [ ] Tester sur couleurs1.vnd (signature 0xFFFFFFDB)
- [ ] Analyser pourquoi belge.vnd a 1 scène de différence

---

**Généré**: 2026-01-23  
**Validation**: danem.vnd ✅ | belge.vnd ⚠️ (1 scène diff)  
**Méthode**: Analyse hex + comparaison JSON parser
