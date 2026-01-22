# VND Parser Project - Contexte Persistant

## Qu'est-ce qu'un fichier VND ?

Les fichiers `.vnd` sont des fichiers binaires de Visual Novel Data utilisés par le moteur VnStudio. Ils contiennent:
- Une base de données de scènes (tables de fichiers + scripts + hotspots)
- Des slots vides marqués par "Empty"
- Une signature magique `0xFFFFFFDB` marquant le début des configs de scène

## Structure d'une Scène VND

1. **Table de Fichiers** - Liste de noms de fichiers au format Pascal (4 octets length + string)
2. **InitScript** - Commandes d'initialisation
3. **Config** - Signature `0xFFFFFFDB` + 5 ints
4. **Hotspots** - Zones cliquables avec commandes et géométrie polygonale

## Parser de Référence

Le parser de référence est dans `couleurs-ok-parser/services/vndParser.ts` (TypeScript).
Une copie Python exacte est disponible dans `vnd_parser.py`.

### Fichiers de Test

- `couleurs1/couleurs1.vnd` - Fichier VND de test principal
- `couleurs1.vnd (27).json` - JSON de référence (sortie attendue)

### Validation

```bash
# Parser couleurs1.vnd et comparer avec la référence
python3 vnd_parser.py couleurs1/couleurs1.vnd 100
# Doit produire 55 scènes identiques au JSON de référence
```

## Mapping des Slots de Jeu

Le mapping slot de jeu != ID parsé:
- Les scènes "Toolbar" sont exclues du comptage
- Les slots "Empty" créent des trous dans la numérotation
- Exemple: `fontain2` (ID parsé variable) = slot jeu **39**

### Règles de Mapping

1. Slot commence à 0
2. Exclure les scènes de type `toolbar`
3. Après chaque scène, ajouter +1 au slot
4. Les Empty markers ajoutent des trous dans les slots

## Détection Automatique

### Empty Slots
Pattern binaire: `05 00 00 00 45 6D 70 74 79` (len=5 + "Empty")

### Toolbar
- Scène avec uniquement "Toolbar" comme fichier
- Type de scène détecté automatiquement

## Types de Scènes

- `global_vars` - Scène 0 avec variables globales (>50 fichiers)
- `toolbar` - Barre d'outils persistante
- `options` - Options système (vnoption.dll)
- `credits` - Écran de crédits
- `game_over` - Fin de jeu (perdu/gagné)
- `empty` - Slot vide
- `game` - Scène de jeu normale

## Commandes Importantes

Pour parser un nouveau fichier VND:
```bash
python3 vnd_parser.py chemin/vers/fichier.vnd [max_scenes]
```

## Notes Techniques

- Encodage des strings: Windows-1252 (cp1252)
- Endianness: Little Endian
- Coordonnées hotspots: peuvent dépasser 800x600 pour scènes scrollables
- Le parser gère automatiquement le padding (zéros) et la récupération d'erreurs

---

## Méthodologie de Travail

### Règles Importantes

1. **Un VND à la fois** - Ne passer au fichier suivant que lorsque le fichier en cours est 100% validé ensemble
2. **Une amélioration à la fois** - Plutôt que d'essayer de tout régler d'un coup
3. **Boucles de rétro-action** - Vérifier les VND déjà traités à chaque itération
4. **Automatiser les vérifications** - Scripts de validation automatiques

### Ressources Documentation

En cas de doute, consulter:
- Les dossiers du projet (contiennent infos et pseudo-code du moteur)
- ⚠️ Prendre les infos avec des pincettes - peuvent être obsolètes

### Script de Vérification Automatique

```bash
# Comparer sortie Python avec référence JSON
python3 vnd_parser.py couleurs1/couleurs1.vnd 100
python3 -c "
import json
with open('couleurs1.vnd (27).json') as f: ref = json.load(f)
with open('couleurs1/couleurs1.vnd.parsed.json') as f: out = json.load(f)
assert ref['scenes'] == out['scenes'], 'MISMATCH!'
print('✓ VALIDATION OK')
"
```

---

## Signatures Multiples VND

**DÉCOUVERTE MAJEURE** : Chaque fichier VND utilise une signature magique différente!

| Fichier | Signature | Statut Parser |
|---------|-----------|---------------|
| couleurs1.vnd | `0xFFFFFFDB` | ✅ Validé |
| danem.vnd | `0xFFFFFFF4` | ✅ Validé |
| allem.vnd | `0xFFFFFFF5` | 🔄 Prêt |
| angleterre.vnd | `0xFFFFFFB7` | 🔄 Prêt |
| france.vnd | `0xFFFFFFE4` | 🔄 Prêt |
| italie.vnd | `0xFFFFFFE2` | 🔄 Prêt |

Le parser supporte maintenant toutes ces signatures via:
- Constante `VND_SIGNATURES` dans `vnd_parser.py`
- Méthode `isValidSignature()` pour vérification flexible
- Système de "weak candidates" pour signatures sans validation stricte

---

## Progression & Historique

### VND Traités

| Fichier | Statut | Scènes | Signatures | Hotspots | Notes |
|---------|--------|--------|------------|----------|-------|
| couleurs1.vnd | ✓ Validé | 55 | 37 × 0xFFFFFFDB | ~100% geom | Référence de base |
| danem.vnd | ✅ **100% Validé** | 15 | 10 × 0xFFFFFFF4 | **66/66 (100%)** | Toutes fausses scènes éliminées |

**Note importante**: Chaque scène déclare un `objCount` (nombre de hotspots attendu) dans sa table hotspots. Le parser doit lire exactement ce nombre pour être 100% correct.

**Fausses scènes éliminées** (danem.vnd):
- 3× "Voiture.wav" - paramètres de commandes hotspot
- 1× "a_dan.wav" isolé - paramètre de commande
- 4× "cling.wav" + score - paramètres de commandes
- **Total: 8 fausses scènes supprimées → 15 scènes légitimes**

### Améliorations du Parser

| Date | Amélioration | Impact |
|------|-------------|--------|
| 2026-01-21 | Parser Python initial | Traduction exacte du TS |
| - | Empty slot detection | Pattern binaire automatique |
| - | Toolbar exclusion | Auto-détection sceneType |
| - | Gap recovery | Récupération commandes orphelines |
| - | Geometry scan | Détection structures désalignées |
| - | Coalescing | Fusion commandes + géométries |
| 2026-01-22 | **Support signatures multiples** | **Déblocage parsing tous VND** |
| - | Weak candidate system | Acceptation signatures validation partielle |
| - | isValidSignature() | Vérification flexible 6 signatures |
| - | **Reject relative paths** | **Fix frontière scènes - jeuloc.bmp 18 hotspots** |
| - | **Reject isolated audio/video** | **100% géométrie - élimination .wav/.avi isolés** |

### Problèmes Résolus

- [x] ~~Vérifier offset 52902 - différence potentielle dans initScript.commands~~
- [x] **Signatures différentes entre VND** - Résolu avec support multi-signatures
- [x] **danem.vnd échouait parsing** - Résolu, 100% des signatures détectées
- [x] **Fausses scènes créées à partir de hotspots** - Paths relatifs rejetés (ex: jeuloc.bmp 18 hotspots)
- [x] ✅ **Fausses scènes à partir de paramètres commandes** - **100% RÉSOLU!**
  - Fix: Filtrage dans `isValidFileTable()` - rejet des .wav/.avi/.mp3 isolés
  - Résultat: danem.vnd passe de 91% à **100% de géométrie** (66/66 hotspots)
  - 8 fausses scènes éliminées (Voiture.wav × 3, a_dan.wav, cling.wav × 4)
  - Scènes validées: 15 scènes légitimes au lieu de 23 fausses

