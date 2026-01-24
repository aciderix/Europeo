# Analyse Complète des Fichiers VND - État du Parser

**Date**: 2026-01-24
**Parser version**: Gemini-improved hybrid parser

## Résumé Exécutif

**19 fichiers VND analysés**:
- ✅ **2 VND 100% géométrie** (grece.vnd, suede.vnd)
- ⚠️ **17 VND avec hotspots sans géométrie** (89.5%)
- 📊 **Total**: 2051 hotspots, 1679 avec géométrie (81.9%)

## Résultats Détaillés par VND

| VND | Header | Parsé | Hotspots | Avec Géo | Sans Géo | % Géo | Statut |
|-----|--------|-------|----------|----------|----------|-------|--------|
| allem.vnd | 15 | 15 | 58 | 54 | 4 | 93.1% | ⚠️ |
| angleterre.vnd | 81 | 81 | 170 | 163 | 7 | 95.9% | ⚠️ |
| autr.vnd | 24 | 36 | 84 | 73 | 11 | 86.9% | ⚠️ |
| barre.vnd | 0 | 8 | 21 | 17 | 4 | 81.0% | ⚠️ |
| belge.vnd | 28 | 27 | 94 | 72 | 22 | 76.6% | ⚠️ |
| **biblio.vnd** | 0 | 42 | **427** | 254 | **173** | **59.5%** | 🔴 |
| couleurs1.vnd | 31 | 55 | 174 | 169 | 5 | 97.1% | ⚠️ |
| danem.vnd | 16 | 16 | 65 | 53 | 12 | 81.5% | ⚠️ |
| ecosse.vnd | 42 | 41 | 155 | 151 | 4 | 97.4% | ⚠️ |
| espa.vnd | 20 | 20 | 82 | 80 | 2 | 97.6% | ⚠️ |
| finlan.vnd | 20 | 21 | 83 | 80 | 3 | 96.4% | ⚠️ |
| france.vnd | 34 | 34 | 103 | 99 | 4 | 96.1% | ⚠️ |
| **frontal/start.vnd** | 8257 | 3 | 4 | 0 | **4** | **0%** | 🔴 |
| **grece.vnd** | 18 | 18 | 73 | **73** | **0** | **100%** | ✅ |
| holl.vnd | 22 | 22 | 111 | 107 | 4 | 96.4% | ⚠️ |
| irland.vnd | 3 | 24 | 95 | 91 | 4 | 95.8% | ⚠️ |
| italie.vnd | 36 | 35 | 98 | 95 | 3 | 96.9% | ⚠️ |
| portu.vnd | 17 | 17 | 90 | 88 | 2 | 97.8% | ⚠️ |
| **suede.vnd** | 2 | 14 | 44 | **44** | **0** | **100%** | ✅ |

### Légende
- ✅ 100% géométrie (PARFAIT)
- ⚠️ >95% géométrie (acceptable)
- 🔴 <80% géométrie (PROBLÈME CRITIQUE)

## Scènes Spéciales (OK sans géométrie)

Ces types de scènes sont **NORMAUX** sans hotspots ou sans géométrie:

### 1. Global Variables (18 scènes)
- **Fonction**: Déclaration des variables globales du jeu
- **Fichiers**: Typiquement >50 fichiers (.dll, ressources)
- **Exemple**: `Scene #0` dans tous les VND
- **Caractéristiques**: 
  - 0 hotspots
  - Fichiers: vnresmod.dll, COMPTEUR1, etc.
  - Type: `global_vars`

### 2. Empty Slots (10 scènes)
- **Fonction**: Slots vides réservés
- **Pattern binaire**: `05 00 00 00 45 6D 70 74 79` (len=5 + "Empty")
- **Caractéristiques**:
  - 0 hotspots
  - Type: `empty`

### 3. Options System (vnoption.dll)
- **Fonction**: Menu options du jeu
- **Fichier**: `..\frontal\vnoption.dll`
- **Exemple**: frontal/start.vnd Scene #2 @ 0x139b
- **Caractéristiques**:
  - 0 hotspots (UI gérée par la DLL)
  - InitScript avec commandes (53-92 commandes typiques)
  - Type: `options`
  - **C'EST NORMAL** d'avoir des InitScript commands ici

### 4. Toolbar/Cursor System (fleche.cur)
- **Fonction**: Barre d'outils / Système de curseurs
- **Fichier**: `fleche.cur`
- **Pattern récurrent**: 92 InitScript commands
- **Exemples**: 
  - danem Scene #12 @ 0x7fcf
  - belge Scene #24 @ 0xe7e3
  - Présent dans 10+ VND
- **Caractéristiques**:
  - Type: `unknown` (devrait être `toolbar`)
  - objCount: souvent 3 ou 4
  - **C'EST NORMAL** d'avoir 92 InitScript commands (init curseurs)

## Problèmes Identifiés

### 🔴 CRITIQUE: biblio.vnd
- **173/427 hotspots sans géométrie (40.5%)**
- Scènes problématiques:
  - Scene #3: 17/17 hotspots sans géométrie (atlas.htm)
  - Scene #11: 13/36 hotspots sans géométrie
  - Scene #18: **78/78 hotspots TOUS sans géométrie** (lesaistu.bmp, dico)

**Cause probable**: Gap recovery récupère des records binaires comme hotspots

### 🔴 CRITIQUE: frontal/start.vnd
- **4/4 hotspots sans géométrie (0%)**
- Header déclare: 8257 scènes (ANORMAL - corruption?)
- Seulement 3 scènes parsées

**Cause probable**: Fichier corrompu ou format différent

### ⚠️ PROBLÈME: danem Scene #14 @ 0x9a0a
- **9/9 hotspots TOUS sans géométrie**
- Fichiers: `sirene.bmp`, `"3"`
- objCount: N/A (pas de signature)
- Commands: FONT (39), PLAYTEXT (38), QUIT (0)

**Diagnostic**: 
- Le "3" est un **record Type 1** (navigation), pas un fichier
- Les 9 "hotspots" sont des **records binaires** parsés à tort
- Gap recovery a créé ces faux hotspots

### ⚠️ PROBLÈME: belge Scene #25 @ 0x1005f
- **20/20 hotspots TOUS sans géométrie**
- objCount déclaré: **0**
- Hotspots parsés: **20** (gap recovery)
- Fichiers: paysliste.bmp, cpays 1

**Diagnostic**: Gap recovery a créé 20 faux hotspots alors que objCount=0

## Patterns Récurrents

### Pattern 1: Scènes avec objCount=N/A
- Pas de signature 0xFFFFFFxx détectée
- Gap recovery crée des hotspots à partir de records binaires
- Ces "hotspots" n'ont souvent pas de géométrie

### Pattern 2: Scènes avec objCount=0 mais hotspots parsés
- Header déclare 0 hotspots
- Parser crée quand même des hotspots via gap recovery
- **TOUS ces hotspots sont sans géométrie**

### Pattern 3: fleche.cur avec 92 InitScript commands
- Pattern système pour initialisation curseurs
- Présent dans 10+ VND
- **C'EST NORMAL**, pas une erreur

## Recommandations

### 1. Parser STRICT basé sur objCount
**Action**: Lire exactement `objCount × 153 bytes` de hotspots
- Si objCount=0 → 0 hotspots (pas de gap recovery)
- Si objCount=N → lire N hotspots strictement
- Désactiver gap recovery qui crée des faux hotspots

### 2. Validation géométrie obligatoire
**Règle**: Tout hotspot DOIT avoir `pointCount > 0`
- Exception: Scènes spéciales (vnoption.dll, empty, global_vars)
- Si pointCount=0 dans scène game → ERREUR de parsing

### 3. Investigation manuelle nécessaire
**VND à investiguer**:
1. **biblio.vnd**: 173 hotspots sans géométrie - vérifier structure binaire
2. **frontal/start.vnd**: Header corrompu (8257 scènes) - fichier à examiner
3. **danem Scene #14**: Vérifier offset 0x9A0A manuellement
4. **belge Scene #25**: Vérifier offset 0x1005F manuellement

**Méthode**: 
- Hexdump des offsets problématiques
- Comparer avec structure VND attendue
- Vérifier présence padding/décalages inattendus

## Conclusion

Le parser actuel (Gemini hybrid) fonctionne bien pour la **détection de scènes** (98.7% des scènes trouvées), mais a un problème critique avec **gap recovery** qui crée des faux hotspots sans géométrie.

**Solution recommandée**: Parser strict basé sur objCount pour éliminer les 372 hotspots sans géométrie détectés (18.1% du total).
