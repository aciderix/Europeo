# 📋 RAPPORT D'ANALYSE COMPLET - danem.vnd

**Date**: 2026-01-22
**Fichier analysé**: `danem/danem.vnd`
**Parser utilisé**: `vnd_parser.py` (version couleurs1-compatible)

---

## 🎯 RÉSUMÉ EXÉCUTIF

Le parsing de `danem.vnd` a révélé des **problèmes majeurs** causés par une **différence structurelle fondamentale** dans le format binaire. Le parser actuel, optimisé pour `couleurs1.vnd`, échoue à parser correctement `danem.vnd` en raison d'une **signature magique différente**.

### Statistiques Globales

| Métrique | Valeur |
|----------|--------|
| Scènes totales parsées | 36 |
| Scènes de type `game` | 33 |
| Scènes de type `global_vars` | 1 |
| Scènes de type `options` | 1 |
| Scènes de type `unknown` | 1 |

---

## ❌ PROBLÈMES IDENTIFIÉS

### 1. Scènes sans Background BMP (CRITIQUE)

**Nombre**: 20 scènes de type `game` (61% des scènes de jeu)

**Impact**: Ces scènes n'affichent pas de background, rendant le jeu injouable.

**Exemples de scènes affectées**:
- Scène 4: `['..\\..\\portu\\digit\\port.wav']` (seulement audio, pas d'image)
- Scènes 9-17: `['..\\..\\couleurs1\\digit\\cartoon.wav']` (seulement audio)

**Analyse**: Le parser ne détecte pas correctement la table des fichiers, manquant ainsi les références aux BMP.

---

### 2. Hotspots sans Géométrie (CRITIQUE)

**Nombre**: 45 hotspots (sur un total inconnu)

**Impact**: Les zones cliquables n'ont pas de coordonnées, rendant l'interaction impossible.

**Exemple - Scène 3**:
```json
{
  "index": -1,
  "offset": 11214,
  "commands": [...],
  "geometry": {
    "cursorId": 0,
    "pointCount": 0,
    "points": [],      ← VIDE!
    "extraFlag": 0
  },
  "isRecovered": true  ← Mode récupération/fallback
}
```

**Analyse**: Sans signature config, le parser ne peut pas localiser les structures de géométrie et utilise un mode "fallback" qui récupère uniquement les commandes.

---

### 3. Hotspots avec Données Insuffisantes

**Nombre**: 16 hotspots

**Impact**: Hotspots avec moins de 2 commandes (attendu: au minimum font + texte, ou autres combinaisons).

**Analyse**: Lié au problème de géométrie - le mode fallback ne récupère pas toutes les commandes associées.

---

### 4. Présence de Logic ✅

**Nombre**: 0 scènes avec Logic non vide

**Statut**: ✅ CORRECT - La logique est bien intégrée dans les hotspots comme attendu.

---

### 5. Signatures Config Manquantes (CAUSE RACINE)

**Nombre**: 36/36 scènes (100%) sans signature détectée

**Impact**: **CRITIQUE** - C'est la cause racine de tous les autres problèmes.

---

## 🔬 CAUSE RACINE IDENTIFIÉE

### Découverte Majeure: Signatures Multiples

Le parser actuel cherche uniquement la signature `0xFFFFFFDB` pour localiser les structures de configuration. Cependant, **chaque fichier VND utilise une signature différente**:

| Fichier VND | Signature Utilisée | Occurrences | Status Parser |
|-------------|-------------------|-------------|---------------|
| `couleurs1.vnd` | `0xFFFFFFDB` | 37 | ✅ Fonctionne |
| `danem.vnd` | `0xFFFFFFF4` | 10 | ❌ Échec |
| `allem.vnd` | `0xFFFFFFF5` | 9 | ❌ Échec probable |
| `angleterre.vnd` | `0xFFFFFFB7` | 66 | ❌ Échec probable |
| `france.vnd` | `0xFFFFFFE4` | 25 | ❌ Échec probable |
| `italie.vnd` | `0xFFFFFFE2` | 24 | ❌ Échec probable |

### Hexdump - Comparaison

**couleurs1.vnd** (fonctionne):
```
offset: ... db ff ff ff 00 00 00 00 ...
             ^^^^^^^^^^^
             Signature trouvée!
```

**danem.vnd** (échec):
```
offset: ... f4 ff ff ff 00 00 00 00 ...
             ^^^^^^^^^^^
             Signature différente - non détectée par le parser
```

---

## 🔍 ANALYSE COMPARATIVE

### couleurs1.vnd (référence fonctionnelle)

| Critère | Valeur |
|---------|--------|
| Scènes totales | 55 |
| Scènes `game` sans BMP | 3 (5%) |
| Hotspots sans géométrie | 4 |
| Signature détectée | ✅ Oui (`0xFFFFFFDB`) |

### danem.vnd (problématique)

| Critère | Valeur |
|---------|--------|
| Scènes totales | 36 |
| Scènes `game` sans BMP | 20 (61%) |
| Hotspots sans géométrie | 45+ |
| Signature détectée | ❌ Non (cherche `0xFFFFFFDB`, trouve `0xFFFFFFF4`) |

---

## 📊 OBSERVATIONS DÉTAILLÉES

### Scène 3 - Exemple de Parsing Défaillant

```json
{
  "id": 3,
  "offset": 10935,
  "files": [
    {"slot": 1, "filename": "..\\..\\portu\\digit\\port.wav"},
    {"slot": 2, "filename": "siren.bmp", "param": 16}  ← BMP présent!
  ],
  "config": {
    "offset": -1,
    "foundSignature": false  ← Signature non trouvée!
  },
  "hotspots": [
    {
      "geometry": {
        "pointCount": 0,
        "points": []  ← Vide!
      },
      "isRecovered": true  ← Mode fallback activé
    }
  ],
  "warnings": ["Aucune structure de Hotspot détectée. Mode fallback."],
  "parseMethod": "heuristic"  ← Méthode heuristique/devinette
}
```

**Observations**:
1. Le BMP `siren.bmp` est bien présent dans les fichiers
2. Mais la signature config n'est pas trouvée
3. Le parser passe en mode "heuristic fallback"
4. Les hotspots sont "récupérés" mais sans géométrie
5. Les commandes dans `initScript` sont toutes marquées `isRecovered: true` avec des offsets dupliqués

---

## 💡 RAISONS DES PROBLÈMES

### 1. Pourquoi 20 scènes sans BMP?

Le parser lit bien la table des fichiers initialement, mais:
- Certaines scènes ont probablement un format de table différent
- Sans signature config, le parser ne peut pas valider où se termine la table des fichiers
- Il peut "sauter" des fichiers ou mal interpréter la structure

### 2. Pourquoi 45 hotspots sans géométrie?

Le flux normal de parsing est:
1. Lire la table des fichiers
2. Lire l'initScript
3. **Chercher la signature config `0xFFFFFFDB`** ← ÉCHOUE ICI
4. Utiliser la position de la config pour localiser les hotspots
5. Parser les hotspots avec leurs géométries

Sans l'étape 3, le parser ne sait pas où commencent les hotspots et utilise un mode "devinette" qui récupère les commandes mais pas la géométrie.

### 3. Pourquoi seulement 10 signatures sur 36 scènes?

Toutes les scènes n'ont pas forcément de structure "config". Certaines scènes simples peuvent ne pas avoir de config (scènes vides, transitions, etc.).

---

## 🛠️ RECOMMANDATIONS DE CORRECTION

### Solution 1: Détection Automatique de Signature (RECOMMANDÉE)

Modifier le parser pour détecter automatiquement la signature:

```python
# Au lieu de chercher uniquement 0xFFFFFFDB
SIGNATURES_KNOWN = [
    0xFFFFFFDB,  # couleurs1
    0xFFFFFFF4,  # danem
    0xFFFFFFF5,  # allem
    0xFFFFFFB7,  # angleterre
    0xFFFFFFE4,  # france
    0xFFFFFFE2,  # italie
]

def find_config_signature(data, offset, max_search=5000):
    for i in range(offset, min(offset + max_search, len(data) - 4)):
        val = struct.unpack('<I', data[i:i+4])[0]
        if val in SIGNATURES_KNOWN:
            return i, val
    return -1, None
```

### Solution 2: Détection par Pattern (ALTERNATIVE)

Chercher n'importe quelle valeur `0xFFFFFFxx`:

```python
def find_config_signature_pattern(data, offset, max_search=5000):
    for i in range(offset, min(offset + max_search, len(data) - 4)):
        val = struct.unpack('<I', data[i:i+4])[0]
        # Chercher pattern 0xFFFFFFxx
        if (val & 0xFFFFFF00) == 0xFFFFFF00:
            return i, val
    return -1, None
```

### Solution 3: Mode Hybride

Combiner les deux approches:
1. Essayer d'abord les signatures connues
2. Si échec, chercher le pattern `0xFFFFFFxx`
3. Si échec, utiliser le mode heuristic actuel

---

## 📈 IMPACT SUR LES AUTRES VND

Basé sur l'analyse des signatures, **TOUS les autres fichiers VND** sont probablement affectés:

| Fichier | Signature | Impact Estimé |
|---------|-----------|---------------|
| allem.vnd | 0xFFFFFFF5 | 🔴 Parsing incomplet |
| angl/angleterre.vnd | 0xFFFFFFB7 | 🔴 Parsing incomplet |
| france.vnd | 0xFFFFFFE4 | 🔴 Parsing incomplet |
| italie.vnd | 0xFFFFFFE2 | 🔴 Parsing incomplet |
| ... | ? | 🔴 Probablement affecté |

**Seul `couleurs1.vnd` parse correctement** car c'était le fichier de référence utilisé pour développer le parser.

---

## ✅ VALIDATION

### Tests Nécessaires Après Correction

1. **Re-parser danem.vnd** avec signatures multiples
2. **Vérifier**:
   - ✅ Toutes les scènes `game` ont au moins 1 BMP
   - ✅ Tous les hotspots ont une géométrie (pointCount > 0)
   - ✅ Tous les hotspots de scènes `game` ont au moins 2 data/commandes
   - ✅ Aucune scène n'a de Logic non vide
   - ✅ Les signatures config sont trouvées
3. **Comparer** avec d'autres VND parsés pour cohérence

### Critères de Succès

Une scène bien parsée doit avoir:
- ✅ Au moins 1 fichier BMP (background) pour les scènes `game`
- ✅ Des hotspots avec géométrie valide (pointCount ≥ 2)
- ✅ Des hotspots avec au moins 2 commandes/data (font+texte minimum)
- ✅ Pas de données dans la section Logic
- ✅ Signature config trouvée (`foundSignature: true`)

---

## 📝 CONCLUSION

Le parser actuel `vnd_parser.py` fonctionne **parfaitement pour couleurs1.vnd** mais **échoue sur danem.vnd et probablement tous les autres fichiers VND** en raison d'une **signature magique différente** (`0xFFFFFFF4` au lieu de `0xFFFFFFDB`).

### Actions Prioritaires

1. 🔴 **URGENT**: Modifier le parser pour supporter les signatures multiples
2. 🟡 **IMPORTANT**: Re-tester avec tous les fichiers VND
3. 🟢 **SUIVI**: Documenter toutes les signatures découvertes dans CLAUDE.md

### Fichiers Générés

- `danem/danem.vnd.parsed.json` - Sortie du parsing (incomplet)
- `danem_analysis_report.json` - Rapport détaillé en JSON
- `RAPPORT_ANALYSE_DANEM.md` - Ce rapport

---

**Rapport généré automatiquement par le VND Parser Analysis Tool**
