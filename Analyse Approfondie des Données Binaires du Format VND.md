# Analyse Approfondie des Données Binaires du Format VND

## Introduction
Ce document fournit une analyse technique détaillée et exhaustive des structures de données binaires présentes dans les fichiers VND (Virtual Navigator Data), en se basant sur les informations extraites du dépôt GitHub `aciderix/Vndmoteur` [1]. L'accent est mis exclusivement sur les aspects binaires du format, incluant les en-têtes, les types d'enregistrements, les séquences de données et les motifs récurrents.

## Encodage et Conventions
Toutes les valeurs numériques binaires dans les fichiers VND sont encodées en **entiers non signés de 32 bits (uint32)**, en utilisant l'ordre des octets **petit-boutiste (Little Endian)**, sauf indication contraire [2].

## Structure Binaire de Haut Niveau

### 1. En-tête du Fichier (Header)
L'en-tête est la première structure binaire du fichier. Il contient des métadonnées cruciales pour l'interprétation du reste du fichier.

| Offset (Hex) | Taille (octets) | Description | Valeur d'Exemple (de `couleurs1.vnd`) |
|--------------|-----------------|-------------|---------------------------------------|
| `0x00`       | 9               | Magic Number| `3a 01 01 00 00 06 00 00 00`          |
| `0x09`       | 6               | Signature   | `56 4e 46 49 4c 45` ("VNFILE")         |
| `0x0f`       | 4               | Longueur Version| `06 00 00 00` (6)                     |
| `0x13`       | 6               | Version     | `32 2e 31 33 36 00` ("2.136")          |
| `0x21`       | 4               | Longueur Projet | `07 00 00 00` (7)                     |
| `0x25`       | 7               | Nom Projet  | `45 75 72 6f 70 65 6f` ("Europeo")    |
| `0x30`       | 4               | Longueur Créateur| `10 00 00 00` (16)                    |
| `0x34`       | 16              | Créateur    | `53 6f 70 72 61 20 4d ...` ("Sopra Multimedia") |
| `0x48`       | 4               | Longueur Checksum| `08 00 00 00` (8)                     |
| `0x4c`       | 8               | Checksum    | `35 44 35 31 46 32 33 33` ("5D51F233") |
| `0x5c`       | 4               | Largeur Écran| `80 02 00 00` (640)                   |
| `0x60`       | 4               | Hauteur Écran| `e0 01 00 00` (480)                   |
| `0x64`       | 4               | Profondeur Couleur| `10 00 00 00` (16)                    |
| `0x7c`       | 4               | Longueur Chemin DLL| `1c 00 00 00` (28)                    |
| `0x80`       | 28              | Chemin DLL  | `2e 2e 5c 56 6e 53 ...` ("..\\VnStudio\\vnresmod.dll") |

### 2. Table des Variables
Cette section, qui suit l'en-tête, n'est pas strictement binaire dans son contenu (elle contient des noms de variables en texte), mais sa structure est binaire. Chaque entrée est un bloc `[longueur (uint32)][nom (char*)][valeur initiale (uint32)]`.

### 3. Enregistrements de Données (Records)
La structure fondamentale des données dans un fichier VND est l'enregistrement. La grande majorité des enregistrements suit un schéma binaire simple [2]:

`[SÉPARATEUR (uint32)] [LONGUEUR (uint32)] [TYPE (uint32)] [DONNÉES (longueur octets)]`

*   **Séparateur**: Toujours `01 00 00 00`.
*   **Longueur**: Taille en octets des données qui suivent.
*   **Type**: Identifiant numérique du type de données.
*   **Données**: Peuvent être du texte (commandes, chemins) ou des données binaires pures (polygones).

## Analyse Détaillée des Types d'Enregistrements Binaires

### Types d'Enregistrements de Zones Cliquables
Deux types principaux d'enregistrements binaires définissent les zones cliquables (hotspots) [8]:

#### Type 105: Polygones
Cette structure binaire définit des zones cliquables de forme arbitraire.

*   **Identification**: `type_id = 105` (confirmé par `decode_vnd_final.py` [6]).
*   **Structure**:

| Champ | Taille (octets) | Type | Description |
|---|---|---|---|
| Type ID | 4 | uint32 | `69 00 00 00` (105) |
| Point Count | 4 | uint32 | Nombre de sommets du polygone. |
| Coordinates | `Point Count * 8` | array of int32 | Paires de coordonnées (x, y) pour chaque sommet. |

**Exemple d'un polygone de 8 points (extrait de `couleurs1.vnd` à l'offset `0x11f8b`)** [2]:

```
08 00 00 00     - Point count = 8
06 02 00 00     - X1 = 518
c9 01 00 00     - Y1 = 457
08 02 00 00     - X2 = 520
a0 01 00 00     - Y2 = 416
...
```

#### Type 2: Rectangles
Cette structure binaire définit des zones cliquables rectangulaires, souvent utilisées pour des éléments simples comme des boutons de sortie ou des zones d'information textuelle [8].

*   **Identification**: `type_id = 2`.
*   **Structure**:

| Champ | Taille (octets) | Type | Description |
|---|---|---|---|
| Type ID | 4 | uint32 | `02 00 00 00` (2) |
| X1 | 4 | uint32 | Coordonnée X du coin supérieur gauche. |
| Y1 | 4 | uint32 | Coordonnée Y du coin supérieur gauche. |
| X2 | 4 | uint32 | Coordonnée X du coin inférieur droit. |
| Y2 | 4 | uint32 | Coordonnée Y du coin inférieur droit. |

**Exemple d'un rectangle (extrait du fichier joint)** [8]:

```
02 00 00 00     - Type ID = 2
00 00 00 00     - X1 = 0
63 01 00 00     - Y1 = 355
7f 02 00 00     - X2 = 639
90 01 00 00     - Y2 = 400
```

### Types d'Enregistrements Textuels avec Structure Binaire Implicite
De nombreux types d'enregistrements contiennent du texte, mais ce texte a une structure qui est ensuite interprétée par le moteur. Les plus importants sont:

*   **Type 38: Hotspot Textuel**: Contient la définition textuelle du hotspot, qui précède le bloc binaire du polygone. Le format est `"X Y W H 0 Nom"` [2].
*   **Type 39: Définitions de Police**: Contient une chaîne de caractères formatée `"TAILLE STYLE #COULEUR NOM_POLICE"`, par exemple `"18 0 #0000ff Comic sans MS"` [2].
*   **Types 21, 25-90+: Commandes Conditionnelles**: Contiennent des chaînes de type `"variable operateur valeur then commande"`, par exemple `"score < 0 then runprj ..\\couleurs1\\couleurs1.vnp 54"` [4].

## Motifs et Séquences Binaires Récurrents
L'analyse statistique du fichier `couleurs1.vnd` révèle des séquences binaires fréquentes qui indiquent des structures logiques [4].

| Séquence (en uint32) | Nombre d'Occurrences | Interprétation Probable |
|---|---|---|
| `(0, 0, 0)` | 798 | Padding ou terminateur nul. |
| `(1, 0, 0)` | 21 | Séparateur de record suivi de zéros. |
| `(0, 39, 26)` | 21 | Enregistrement de police (Type 39, Longueur 26). |
| `(1, 21, 32)` | 17 | Commande conditionnelle (Type 21) de type `set_var` (32). |
| `(1, 6, 2)` | 13 | Référence à une scène de type 2. |
| `(1, 23, 5)` | 9 | Enregistrement d'état de jeu (Type 23, `jeu`). |

## Analyse des Types d'Enregistrements Inconnus ou Ambigus
L'analyse avec `decode_vnd_final.py` et les informations complémentaires ont révélé plusieurs `type_id` qui ne correspondent pas à des commandes de jeu mais plutôt à des métadonnées ou des artefacts de parsing [7] [8]:

*   **Type 257**: Contient la chaîne `"VNFILE"`. Il s'agit d'une mauvaise interprétation du champ "Signature" de l'en-tête comme un enregistrement.
*   **Type 1634296933**: Contient la chaîne `"5D51F233"`. Il s'agit du checksum de l'en-tête.
*   **Type 280**: Contient la chaîne `"SACADOS"`. Il s'agit du premier nom de variable dans la table des variables.
*   **Types 620, 1397563507, 1936747877**: Contiennent des caractères uniques (`{`, `&`). Ce sont probablement des erreurs de parsing ou des données non interprétées.

Ces résultats montrent les limites des décodeurs automatiques et confirment que la structure binaire n'est pas toujours homogène. Les sections comme l'en-tête et la table des variables ont leur propre structure binaire qui peut être incorrectement identifiée comme des enregistrements standards par un scan naïf.

## Conclusion
L'analyse binaire des fichiers VND révèle un format structuré mais hétérogène. Les points clés sont:

1.  **En-tête Fixe**: Une structure binaire bien définie au début de chaque fichier.
2.  **Enregistrements Typés**: La majorité du fichier est constituée d'enregistrements `[séparateur][longueur][type][données]`.
3.  **Zones Cliquables Binaires (Types 2 et 105)**: Les zones interactives sont définies par des polygones (Type 105) ou des rectangles (Type 2).
4.  **Contradiction Documentaire**: La documentation principale omet les `type_id = 2` et `type_id = 105` pour les zones cliquables, ce qui représente la principale divergence découverte.
5.  **Hétérogénéité**: Le format contient des sections (en-tête, table des variables) avec des structures binaires uniques qui ne suivent pas le modèle d'enregistrement standard.

Cette analyse approfondie fournit une base solide pour la création d'outils de lecture/écriture pour le format VND, en tenant compte de ses particularités et de ses contradictions internes.

## Références

[1] [aciderix/Vndmoteur sur GitHub](https://github.com/aciderix/Vndmoteur/tree/claude/decompile-dll-extraction-YN9Iw)
[2] [VND_BINARY_FORMAT.md](https://github.com/aciderix/Vndmoteur/blob/claude/decompile-dll-extraction-YN9Iw/Doc/VND_BINARY_FORMAT.md)
[3] [REVERSE_ENGINEERING_STATUS.md](https://github.com/aciderix/Vndmoteur/blob/claude/decompile-dll-extraction-YN9Iw/Doc/REVERSE_ENGINEERING_STATUS.md)
[4] [vnd_deep_decoder.py](https://github.com/aciderix/Vndmoteur/blob/claude/decompile-dll-extraction-YN9Iw/vnd_deep_decoder.py)
[5] [vnd_polygon_parser.py](https://github.com/aciderix/Vndmoteur/blob/claude/decompile-dll-extraction-YN9Iw/vnd_polygon_parser.py)
[6] [decode_vnd_final.py](https://github.com/aciderix/Vndmoteur/blob/claude/decompile-dll-extraction-YN9Iw/decode_vnd_final.py)
[7] [Analyse des types d'enregistrements de couleurs1.vnd (sortie console)](#) (référence interne)
[8] [Informations complémentaires sur les types de hotspots (fichier joint par l'utilisateur)](#) (référence interne)
