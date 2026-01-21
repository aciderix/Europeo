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
