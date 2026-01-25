# Investigation: Problème de Frontières de Scènes

## Contexte

Lors de l'analyse de `danem.vnd`, on observe:
- **Hotspots avec géométrie**: 49/54 (91%)
- **Scènes parfaites**: 8/10 (80%)

Les 5 hotspots sans géométrie sont tous marqués `isRecovered: True` (mode fallback).

---

## Problème Identifié

### Scène 8 (loc4.bmp) à 0x6626

**Données du JSON:**
```json
{
  "offset": "0x6626",
  "length": 261,
  "files": ["a_dan.wav", "loc4.bmp"],
  "signature": "0x6677 (WEAK)",
  "hotspots": 0,  ← PROBLÈME!
  "warnings": ["[WEAK SIG] Signature config trouvée mais validation hotspot partielle"]
}
```

**Analyse binaire:**
- Signature à `0x6677`
- Table hotspots à `0x668f` (signature + 24 bytes)
- **objCount déclaré: 4 hotspots**
- Parser trouve: **0 hotspots**

---

## Cause Racine

### 1. La Scène 9 est FAUSSE

À `0x672b`, le parser détecte une "nouvelle scène":

```
Scène 9:
  offset: 0x672b
  files: ["Voiture.wav"]
  hotspots: 0
  parseMethod: "heuristic"
```

**Mais en réalité:**

Hexdump à `0x672b`:
```
0x672b: 0b 00 00 00 56 6f 69 74 75 72 65 2e 77 61 76 01 00 00 00
        ^^^^^^^^^^^ ^^^^^^^^^^^^^^^^^^^^^^^^^^^ ^^^^^^^^^^^
        len=11      "Voiture.wav"                param=1
```

Contexte (avant `0x672b`):
```
0x6723: ... 01 00 00 00 24 00 00 00 00 00 00 00 0b 00 00 00 ...
                                                 ^^^^^^^^^^^
                                                 string len=11
```

**C'est une COMMANDE hotspot**, pas une table de fichiers!

Structure réelle:
```
Commande précédente...
cmdId=1, subtype=36, str_len=0, ""
cmdId=1, subtype=11, str_len=11, "Voiture.wav"  ← ICI!
```

### 2. Pourquoi `isValidFileTable()` accepte?

`isValidFileTable()` à la ligne 350 vérifie:
1. ✅ String "Voiture.wav" parsable
2. ✅ Extension `.wav` valide
3. ✅ Param=1 semble raisonnable

**MAIS** elle ne vérifie PAS:
- ❌ Si c'est à l'intérieur d'une autre scène
- ❌ Si c'est après une signature déjà trouvée
- ❌ Le contexte (commandes hotspot vs table fichiers)

### 3. Conséquence en Cascade

```
Scène 8:
  Signature: 0x6677
  Hotspot table: 0x668f
  Déclare: 4 hotspots

isValidHotspotTable() validation:
  itemsToCheck = min(4, 3) = 3

  Hotspot 0:
    cmdCount: 8
    pointCount: 2
    Points: (45,24), (201,72)
    Points end: 0x6787

  Limit (scène suivante détectée): 0x672b

  0x6787 > 0x672b → FAIL!
  → Signature acceptée comme WEAK
  → Parsing hotspots échoue
```

La fausse scène 9 à `0x672b` **coupe artificiellement** la scène 8, empêchant le parsing correct des hotspots.

---

## Impact Global

Sur danem.vnd:
- **13 fausses scènes éliminées** par le fix relative paths
- **Mais d'autres fausses scènes persistent**:
  - Scène 9: "Voiture.wav" (paramètre de commande)
  - Potentiellement d'autres...

Ces fausses scènes:
1. Coupent les vraies scènes trop tôt
2. Empêchent la validation des hotspots
3. Créent des signatures "WEAK"
4. Résultent en hotspots sans géométrie (mode fallback)

---

## Solutions Possibles

### Option 1: Ne pas détecter de scènes après une signature

```python
def findSceneOffsets(self):
    last_signature_offset = -1

    # Si on vient de trouver une signature, skip les 5000 prochains bytes
    if last_signature_offset != -1 and ptr < last_signature_offset + 5000:
        continue
```

### Option 2: Validation plus stricte dans isValidFileTable()

Vérifier qu'après le premier fichier, on a vraiment d'autres fichiers ou une signature:
```python
# Après avoir lu 1-2 fichiers, chercher signature dans les 500 prochains bytes
# Si trouvée → vraie table
# Si pas trouvée → probablement faux
```

### Option 3: Utiliser les signatures comme ancres primaires

Au lieu de:
1. Trouver tables de fichiers → délimite scènes
2. Chercher signatures dans chaque scène

Faire:
1. Trouver TOUTES les signatures d'abord
2. Les scènes sont entre deux signatures
3. Parser en arrière pour trouver la table de fichiers

---

## Prochaines Étapes

1. Implémenter une des solutions
2. Re-parser danem.vnd
3. Vérifier que les 10 scènes avec signature ont toutes leurs hotspots
4. Valider que 49/54 → 54/54 hotspots avec géométrie

---

**Date**: 2026-01-22
**Fichier**: danem.vnd
**Parser**: vnd_parser.py
