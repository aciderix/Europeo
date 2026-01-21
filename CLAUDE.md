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

## Progression & Historique

### VND Traités

| Fichier | Statut | Scènes | Notes |
|---------|--------|--------|-------|
| couleurs1.vnd | ✓ Validé | 55 | Référence de base |

### Améliorations du Parser

| Date | Amélioration | Impact |
|------|-------------|--------|
| 2026-01-21 | Parser Python initial | Traduction exacte du TS |
| - | Empty slot detection | Pattern binaire automatique |
| - | Toolbar exclusion | Auto-détection sceneType |
| - | Gap recovery | Récupération commandes orphelines |
| - | Geometry scan | Détection structures désalignées |
| - | Coalescing | Fusion commandes + géométries |

### Problèmes Connus / À Investiguer

- [ ] Vérifier offset 52902 - différence potentielle dans initScript.commands
