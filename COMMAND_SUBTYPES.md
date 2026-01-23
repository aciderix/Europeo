# Command Subtypes Mapping - VnStudio Engine

**Source**: `Infos/Code_Reconstruit_V2/commands.cpp.txt`
**Total subtypes**: 49 (0x00 à 0x30 / 0 à 48)
**Détectés dans VND**: 26 subtypes

## Dispatcher Switch

Le dispatcher utilise `*(_DWORD *)(cmd + 8)` = offset +8 de la structure Command (subtype).

## Mapping Complet (49 Subtypes)

| Dec | Hex | Nom | Description | Détecté |
|-----|-----|-----|-------------|---------|
| 0 | 0x00 | **QUIT** | Quitter l'application (0x111u, 0xA4u) | ✅ 490 |
| 1 | 0x01 | MENU | Ouvrir menu (0x111u, 0x4E29u) | ❌ |
| 2 | 0x02 | OPTIONS | Ouvrir options (0x111u, 0x9Du) | ✅ 2 |
| 3 | 0x03 | UNKNOWN_3 | Message handler type 3 | ✅ 7 |
| 4 | 0x04 | UNKNOWN_4 | Message handler type 4 | ❌ |
| 5 | 0x05 | UNKNOWN_5 | Message handler type 5 | ❌ |
| 6 | 0x06 | **GOTO_SCENE** | Navigation scène / INC_VAR / DEC_VAR | ✅ 114 |
| 7 | 0x07 | UNKNOWN_7 | Message handler type 7 | ✅ 28 |
| 8 | 0x08 | UNKNOWN_8 | Message handler type 8 | ❌ |
| 9 | 0x09 | **VIDEO** | Jouer vidéo AVI | ✅ 59 |
| 10 | 0x0A | UNKNOWN_10 | Message handler type 10 | ✅ 63 |
| 11 | 0x0B | UNKNOWN_11 | Message handler type 11 | ✅ 49 |
| 12 | 0x0C | UNKNOWN_12 | Message handler type 12 | ❌ |
| 13 | 0x0D | UNKNOWN_13 | Message handler type 13 | ❌ |
| 14 | 0x0E | UNKNOWN_14 | Message handler type 14 | ❌ |
| 15 | 0x0F | UNKNOWN_15 | Message handler type 15 | ❌ |
| 16 | 0x10 | **DELAY** | Délai / Pause temporelle | ✅ 31 |
| 17 | 0x11 | UNKNOWN_17 | Message handler type 17 | ❌ |
| 18 | 0x12 | UNKNOWN_18 | Message handler type 18 | ❌ |
| 19 | 0x13 | UNKNOWN_19 | Message handler type 19 | ❌ |
| 20 | 0x14 | UNKNOWN_20 | Message handler type 20 | ❌ |
| 21 | 0x15 | **IF_THEN** | Logique conditionnelle | ✅ **1756** |
| 22 | 0x16 | UNKNOWN_22 | Message handler type 22 | ✅ 49 |
| 23 | 0x17 | UNKNOWN_23 | Message handler type 23 | ✅ 33 |
| 24 | 0x18 | UNKNOWN_24 | Message handler type 24 | ✅ 17 |
| 25 | 0x19 | UNKNOWN_25 | Message handler type 25 (special routing) | ✅ 1 |
| 26 | 0x1A | UNKNOWN_26 | Message handler type 26 | ✅ 1 |
| 27 | 0x1B | **ADDBMP** | Afficher image BMP | ✅ 19 |
| 28 | 0x1C | UNKNOWN_28 | Message handler type 28 | ✅ 24 |
| 29 | 0x1D | UNKNOWN_29 | Message handler type 29 | ❌ |
| 30 | 0x1E | UNKNOWN_30 | Message handler type 30 | ✅ 1 |
| 31 | 0x1F | UNKNOWN_31 | Message handler type 31 | ✅ 25 |
| 32 | 0x20 | UNKNOWN_32 | Message handler type 32 | ✅ 5 |
| 33 | 0x21 | UNKNOWN_33 | Message handler type 33 | ❌ |
| 34 | 0x22 | UNKNOWN_34 | Message handler type 34 | ❌ |
| 35 | 0x23 | UNKNOWN_35 | Message handler type 35 | ❌ |
| 36 | 0x24 | UNKNOWN_36 | Message handler type 36 | ✅ 22 |
| 37 | 0x25 | UNKNOWN_37 | Message handler type 37 | ❌ |
| 38 | 0x26 | **PLAYTEXT** | Afficher texte | ✅ 193 |
| 39 | 0x27 | **FONT** | Définir police | ✅ **246** |
| 40 | 0x28 | UNKNOWN_40 | Message handler type 40 | ✅ 1 |
| 41 | 0x29 | UNKNOWN_41 | Message handler type 41 | ✅ 33 |
| 42 | 0x2A | UNKNOWN_42 | Message handler type 42 | ❌ |
| 43 | 0x2B | UNKNOWN_43 | Message handler type 43 | ❌ |
| 44 | 0x2C | UNKNOWN_44 | Message handler type 44 | ❌ |
| 45 | 0x2D | UNKNOWN_45 | Message handler type 45 | ❌ |
| 46 | 0x2E | UNKNOWN_46 | Message handler type 46 | ❌ |
| 47 | 0x2F | UNKNOWN_47 | Message handler type 47 | ✅ 1 |
| 48 | 0x30 | UNKNOWN_48 | Message handler type 48 | ❌ |

## Top Subtypes par Fréquence

1. **IF_THEN (21)**: 1756 occurrences (53.68%) - Logique conditionnelle dominante
2. **QUIT (0)**: 490 occurrences (14.98%) - Boutons quitter
3. **FONT (39)**: 246 occurrences (7.52%) - Définition polices
4. **PLAYTEXT (38)**: 193 occurrences (5.90%) - Affichage texte
5. **GOTO_SCENE (6)**: 114 occurrences (3.49%) - Navigation
6. **UNKNOWN_10 (10)**: 63 occurrences (1.93%)
7. **VIDEO (9)**: 59 occurrences (1.80%) - Vidéos AVI
8. **UNKNOWN_22 (22)**: 49 occurrences (1.50%)
9. **UNKNOWN_11 (11)**: 49 occurrences (1.50%)
10. **UNKNOWN_41 (41)**: 33 occurrences (1.01%)

## Statistiques Globales

- **Total subtypes théoriques**: 49 (0-48)
- **Subtypes détectés**: 26 (53.1%)
- **Subtypes non utilisés**: 23 (46.9%)
- **Total commandes analysées**: 3271 (danem + belge + couleurs1)

## Subtypes Identifiés (8/49)

| Subtype | Nom | Fonction | Source |
|---------|-----|----------|--------|
| 0 | QUIT | Quitter application | Pseudo-code + validation |
| 6 | GOTO_SCENE | Navigation scènes (+/- pour relatif) | Pseudo-code + validation |
| 9 | VIDEO | Jouer vidéo AVI | Pseudo-code + validation |
| 16 | DELAY | Pause temporelle | Pseudo-code + validation |
| 21 | IF_THEN | Logique conditionnelle | Pseudo-code + validation |
| 27 | ADDBMP | Afficher image BMP | Pseudo-code + validation |
| 38 | PLAYTEXT | Afficher texte | Pseudo-code + validation |
| 39 | FONT | Définir police de caractères | Pseudo-code + validation |

## Notes d'Implémentation

### Type 6 (GOTO_SCENE)
- Préfixe `+` ou `-` dans param → mode relatif (INC_VAR/DEC_VAR)
- Pas de préfixe → mode absolu (goto scene X)
- Exemple: `"+1"` = incrémenter variable, `"5"` = aller scène 5

### Type 21 (IF_THEN)
- Commande de branchement conditionnel
- 53.68% de toutes les commandes!
- Structure: condition + actions if-then

### Type 27 (ADDBMP)
- Param contient le chemin vers fichier .bmp
- Affiche l'image en surimpression

### Type 38 (PLAYTEXT)
- Param contient le texte à afficher
- Utilise la police définie par FONT (39)

### Type 39 (FONT)
- Param contient nom de police (ex: "Comic Sans MS", "Arial")
- Définit la police pour PLAYTEXT suivants

## Prochaines Étapes

1. **Reverse engineering** des 18 subtypes restants par analyse:
   - Patterns dans les paramètres
   - Contexte d'utilisation dans les scènes
   - Corrélation avec fichiers (bmp/wav/avi/htm/dll)

2. **Documentation** subtypes rares (< 10 occurrences):
   - 25, 26, 30, 40, 47 (1 occurrence chacun)
   - Analyser contexte spécifique

3. **Validation** sur fichiers VND restants:
   - allem.vnd, angleterre.vnd, france.vnd, italie.vnd
   - Détecter nouveaux subtypes potentiels
