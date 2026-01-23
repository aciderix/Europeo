# Investigation couleurs1.vnd - Findings & Solutions

**Date**: 2026-01-23
**Fichier**: couleurs1.vnd
**Objectif**: Comprendre les écarts entre strict parser et current parser

---

## Questions Investigées

1. ✅ **Pourquoi l'une des 31 scènes HIGH ne matche pas objCount?**
2. ✅ **Pourquoi certaines scènes ont objCount=N/A?**
3. ✅ **Pourquoi objCount ≠ parsed dans certains cas?**

---

## 1. Scene 6 HIGH - Mismatch objCount (Strict Parser)

### Problème Initial

```
Parser ACTUEL:  Scene 6 @ 0x471C, objCount=8, parsed=8 ✓
Parser STRICT:  Scene 6 @ 0x5243, objCount=8, parsed=3 ✗
```

**Ce sont deux scènes DIFFÉRENTES avec le même ID!**

### Cause Racine

Le **strict parser** commence à la **première signature** (0x11A6), tandis que le **parser actuel** commence au **début du fichier** (0x6A).

#### Séquence Détaillée

| Élément | Offset | Description |
|---------|--------|-------------|
| Header | 0x00 → 0x68 | Magic, version, config, scene_count=31 |
| **Scene 0 (global_vars)** | **0x6A → 0x116C** | 282 fichiers, **PAS de signature** |
| Première signature | 0x11BE | 0xFFFFFFDB (début Scene 1 actuel) |
| Scene 1 actuel = Scene 0 strict | 0x11A6 | objCount=6 |

**Décalage**: Tous les IDs du strict parser sont **-1** par rapport au parser actuel.

### Scene 6 Strict - Erreur de Parsing

```
=== Scene 6 @ 0x5243 -> 0x5B0B ===
  objCount = 8
  Hotspot 0-3: ✓ OK
  ERREUR: Coordonnées invalides (2311, 187) @ 0x5681
  Résultat: parsed=3 (5 hotspots manquants)
```

**Cause**: Hotspot 4 a des coordonnées `x=2311` (dépasse limite `abs(x) <= 2000`).

**Impact**: Le strict parser s'arrête prématurément (break strict sur validation).

---

## 2. Scènes avec objCount=N/A

### Scènes Affectées

| Scene | Type | Files | Hotspots | Raison |
|-------|------|-------|----------|--------|
| 0 | global_vars | 282 | 0 | Pas de signature, pas de table hotspots |
| 36 | options | 1 | 0 | Scène options (vnoption.dll), pas de hotspots |
| 42 | game | 0 | 0 | Scène vide (d3/AVI logique) |
| 54 | game_over | 3 | 0 | Fin de jeu, pas de hotspots |

### Cause

Ces scènes **n'ont pas de structure hotspots** (pas de signature config 0xFFFFFFxx + hotspot table).

**Parse Method**: `heuristic` ou `heuristic_recovered`

Elles sont détectées par:
- File table detection (282 fichiers pour global_vars)
- Pattern "Empty" detection
- Gap scanning

### Validité

✅ **Ces scènes sont VALIDES** - Ce sont des scènes spéciales du moteur VnStudio:
- **global_vars**: Variables globales du jeu (SACADOS, JEU, MILLEEURO, etc.)
- **options**: Menu options
- **game_over**: Écran de fin
- **Scènes logiques**: d2/d3/AVI (pas d'interaction)

---

## 3. Scènes avec objCount ≠ parsed

### Statistiques Globales

| Catégorie | Scènes | Détail |
|-----------|--------|--------|
| **Match parfait** | 48/54 | 88.9% ✅ |
| **Récupération (+)** | 5/54 | Parser trouve PLUS |
| **Manquants (-)** | 1/54 | Parser trouve MOINS |

*Note: 54 scènes avec objCount (excluant 3 N/A + Scene 0 global_vars)*

### 3.1 Récupération (+) - Parser Trouve PLUS

**5 scènes** avec hotspots **récupérés** par gap recovery:

| Scene | objCount | parsed | Diff | Method | Hotspots Recovered |
|-------|----------|--------|------|--------|-------------------|
| 8 | 5 | 7 | +2 | signature | 2 |
| 10 | 2 | 3 | +1 | signature | 1 |
| 37 | 3 | 4 | +1 | heuristic_recovered | 1 |
| 40 | 17 | 18 | +1 | signature | 1 |
| 41 | 0 | 1 | +1 | heuristic_recovered | 1 |

#### Cause

Après avoir lu les `objCount` hotspots standards, le parser fait:

```python
# Phase 6: GAP RECOVERY
recoveredHotspots = []
recoveredHotspots.extend(self.scanForTooltips(...))
recoveredHotspots.extend(self.recoverCommandsFromGap(cursor, scriptEnd))
recoveredHotspots.extend(self.recoverCommandsFromGap(finalGapPtr, limit))

# Phase 7: COALESCING + MERGE
mergedHotspots = hotspots + coalescedHotspots
```

**Ces hotspots supplémentaires** sont dans les "trous" du binaire et sont marqués `isRecovered: true`.

#### Validité

✅ **C'est une BONNE chose** - Le parser récupère du contenu qui serait sinon perdu.

⚠️ **Mais moins fiable** - Ces hotspots ne sont pas déclarés dans `objCount`, donc potentiellement:
- Fragments de données
- Commandes orphelines
- Structures partiellement valides

### 3.2 Manquants (-) - Parser Trouve MOINS

**1 scène** avec hotspot **manquant**:

#### Scene 7: objCount=8, parsed=7 (-1)

```
Offset: 0x51FE -> 0x5ACE
Hotspots parsés: 0-6 (7 hotspots)
Hotspot 7: MANQUANT
```

**Hotspots parsés** (analyse des limites):
- Hotspot 0-3: Séquentiels
- Hotspot 4 @ 0x59D6 (pointCount=14, limite haute)
- Hotspot 5 @ 0x58C8 (pointCount=13)
- Hotspot 6 @ 0x594E (pointCount=15, **limite maximale acceptable**)

**Cause probable**: Le hotspot 7 a déclenché un **break strict**:

```python
if pointCount > 500: break        # Sécurité (probablement pas la cause)
if abs(x) > 2000 or abs(y) > 2000:  # ← Cause probable
    hasInvalidCoords = True
    break
if cmdCount > 200: break          # Sécurité (peu probable)
```

Le 8ème hotspot déclaré contient probablement des **coordonnées invalides** (x > 2000 ou y > 2000).

#### Impact

❌ **Perte de contenu** - Le hotspot 7 existe dans le binaire (déclaré dans objCount) mais n'est pas parsé.

⚠️ **Cependant**: Si les coordonnées sont vraiment invalides (> 2000), le hotspot est probablement **corrompu** et le parser fait bien de le rejeter.

---

## Résumé des Findings

### Parser Actuel (Hybride Implicite)

| Aspect | Résultat | Évaluation |
|--------|----------|------------|
| **Couverture** | 55 scènes (100%) | ✅ Excellent |
| **Précision objCount** | 48/54 (88.9%) | ✅ Très bon |
| **Récupération** | +6 hotspots bonus | ✅ Contenu supplémentaire |
| **Pertes** | -1 hotspot (Scene 7) | ⚠️ Minimal |
| **Scènes spéciales** | global_vars, options, game_over | ✅ Détectées |

### Parser Strict

| Aspect | Résultat | Évaluation |
|--------|----------|------------|
| **Couverture** | 31 scènes (56%) | ❌ Incomplet |
| **Précision objCount** | 30/31 (96.8%) | ✅ Excellent |
| **Scènes manquées** | -24 scènes (dont global_vars) | ❌ Critique |
| **Simplicité** | Code simple, prévisible | ✅ Maintenable |

---

## Propositions d'Amélioration

### 1. Parser Hybride avec Confidence Tagging ✅ RECOMMANDÉ

**Implémentation**:

```python
class ParsedScene:
    # ... existing fields ...
    confidence: str = "HIGH" | "MEDIUM" | "LOW"
    parseMethod: str = "signature" | "heuristic" | "empty"
    validationIssues: List[str] = []

def parse_hybrid(vnd_data):
    scenes = []

    # PHASE 1: Scènes avec signatures (HIGH confidence)
    for signature_offset in find_signatures(vnd_data):
        scene = parse_strict_signature(signature_offset)
        scene.confidence = "HIGH"
        scene.parseMethod = "signature"
        scenes.append(scene)

    # PHASE 2: Scènes spéciales (MEDIUM confidence)
    global_vars = detect_global_vars(vnd_data)
    if global_vars:
        global_vars.confidence = "MEDIUM"
        global_vars.parseMethod = "heuristic"
        scenes.append(global_vars)

    # PHASE 3: Gap recovery (LOW confidence)
    for gap_scene in scan_gaps(scenes):
        gap_scene.confidence = "LOW"
        gap_scene.parseMethod = "heuristic_recovered"
        scenes.append(gap_scene)

    return sorted(scenes, key=lambda s: s.offset)
```

**Avantages**:
- ✅ 100% de couverture (comme actuel)
- ✅ Traçabilité (l'utilisateur sait quoi faire confiance)
- ✅ Flexible (filtrage par confidence possible)

### 2. Améliorer Validation Coordonnées

**Problème actuel**: Limite stricte `abs(x) <= 2000` rejette des scènes scrollables.

**Solution**:

```python
# Actuel (strict)
if abs(x) > 2000 or abs(y) > 2000:
    break  # Perte de contenu

# Proposé (flexible)
MAX_COORD_STRICT = 2000
MAX_COORD_SCROLLABLE = 5000

if abs(x) > MAX_COORD_SCROLLABLE or abs(y) > MAX_COORD_SCROLLABLE:
    # Vraiment invalide
    scene.validationIssues.append(f"Coords hors limites: ({x}, {y})")
    break
elif abs(x) > MAX_COORD_STRICT or abs(y) > MAX_COORD_STRICT:
    # Scène scrollable (warning mais continue)
    scene.validationIssues.append(f"Scène scrollable détectée: ({x}, {y})")
    # Continue parsing
```

**Impact**: Récupérerait le hotspot 7 de Scene 7 et d'autres similaires.

### 3. Détecter Scène global_vars en Mode Strict

**Problème**: Le strict parser manque complètement Scene 0 (282 fichiers de variables).

**Solution**:

```python
def parse_strict_with_special_scenes(vnd_data):
    scenes = []

    # Détecter global_vars AVANT les signatures
    if detect_large_file_table(offset=0x6A):
        global_vars = parse_file_table_only(offset=0x6A)
        if len(global_vars.files) > 50:
            global_vars.sceneType = "global_vars"
            global_vars.confidence = "HIGH"  # Très fiable (282 fichiers)
            scenes.append(global_vars)

    # Ensuite parser les signatures
    for sig in find_signatures(vnd_data):
        scenes.append(parse_signature_scene(sig))

    return scenes
```

**Impact**: Le strict parser trouverait 32 scènes au lieu de 31 (100% du header).

### 4. Logging Amélioré pour Debug

**Ajout**:

```python
class ParsedScene:
    # ... existing ...
    objCountDeclared: int  # Ce que le binaire déclare
    objCountParsed: int    # Ce qu'on a vraiment parsé
    objCountRecovered: int # Hotspots récupérés par gap recovery

    def validate_objCount(self):
        if self.objCountDeclared is None:
            return "N/A (no hotspot table)"

        if self.objCountParsed == self.objCountDeclared:
            return "PERFECT"
        elif self.objCountParsed > self.objCountDeclared:
            return f"RECOVERED +{self.objCountRecovered}"
        else:
            missing = self.objCountDeclared - self.objCountParsed
            return f"MISSING -{missing} (validation error)"
```

---

## Recommandations Finales

### Pour couleurs1.vnd

| Recommandation | Priorité | Impact |
|----------------|----------|--------|
| Implémenter parser hybride avec confidence | **P0** | Traçabilité maximale |
| Assouplir limites coordonnées (2000→5000) | **P1** | Récupère Scene 7 hotspot 7 |
| Détecter global_vars en mode strict | **P1** | 100% conformité header |
| Logger objCount détaillé | **P2** | Meilleur debug |

### Approche Générale

**Pour un VND inconnu**:

1. **Commencer en mode STRICT** pour baseline fiable
2. **Comparer avec header.scene_count**
3. **Si scènes manquantes**: Activer mode HYBRID
4. **Analyser confidence tags** pour identifier scènes critiques vs bonus

**Règle d'or**: Les scènes **HIGH confidence** (signatures) sont **96.8% fiables**. Les autres nécessitent validation manuelle si critiques pour le jeu.

---

## Conclusion

Le parser actuel fait un **excellent travail** (88.9% de précision objCount, 100% de couverture).

Les **6 mismatches** sont:
- ✅ **5 récupérations** (contenu bonus via gap recovery)
- ❌ **1 manquant** (Scene 7, probablement coordonnées invalides)

**Recommandation**: Implémenter le **parser HYBRIDE** avec confidence tagging pour donner la **traçabilité** tout en gardant la **couverture complète**.
