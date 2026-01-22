# Rapport d'Analyse du Format VND

## Introduction
Ce rapport détaille la structure et le fonctionnement des fichiers VND (Virtual Navigator Data) basés sur l'analyse du dépôt GitHub `aciderix/Vndmoteur` [1]. L'objectif est d'extraire un maximum d'informations sur la structure, le code binaire et les spécifications, tout en identifiant les éventuelles contradictions entre les différentes sources.

## Vue d'Ensemble du Format VND
Les fichiers VND utilisent un format hybride texte/binaire, avec des entiers de 32 bits (uint32) en petit-boutiste (Little Endian). Chaque enregistrement est séparé par un marqueur binaire spécifique [2].

## Structure du Fichier

### 1. En-tête (Header)
L'en-tête du fichier VND contient des métadonnées essentielles au fonctionnement du moteur de jeu. Sa structure est la suivante [2]:

| Offset | Taille (octets) | Champ           | Description                                                               |
|--------|-----------------|-----------------|---------------------------------------------------------------------------|
| 0x00   | 9               | Magic           | Séquence `3a 01 01 00 00 06 00 00 00`                                     |
| 0x09   | 6               | Signature       | Chaîne de caractères ASCII "VNFILE"                                       |
| 0x0f   | 4               | Longueur Version| Longueur de la chaîne de version (uint32)                                 |
| 0x13   | n               | Version         | Chaîne de version (ex: "2.136" + padding)                                 |
| ...    | 4               | Longueur Projet | Longueur du nom du projet (uint32)                                        |
| ...    | n               | Nom Projet      | Nom du projet (ex: "Europeo")                                             |
| ...    | 4               | Longueur Créateur| Longueur du nom du créateur (uint32)                                      |
| ...    | n               | Créateur        | Nom du créateur (ex: "Sopra Multimedia")                                  |
| ...    | 4               | Longueur Checksum| Longueur du checksum (uint32)                                             |
| ...    | n               | Checksum        | Checksum (ex: "5D51F233")                                                 |
| ...    | 8               | Padding         | Zéros de remplissage                                                      |
| ...    | 4               | Largeur Écran   | Largeur de l'écran (uint32, ex: 640)                                      |
| ...    | 4               | Hauteur Écran   | Hauteur de l'écran (uint32, ex: 480)                                      |
| ...    | 4               | Profondeur Couleur| Profondeur de couleur (uint32, ex: 16)                                    |
| ...    | 4               | Flags           | Indicateurs (uint32)                                                      |
| ...    | 4               | Flags2          | Indicateurs secondaires (uint32)                                          |
| ...    | 4               | Flags3          | Indicateurs tertiaires (uint32)                                           |
| ...    | 4               | Réservé         | Champ réservé (uint32)                                                    |
| ...    | 4               | Longueur Chemin DLL| Longueur du chemin de la DLL (uint32)                                     |
| ...    | n               | Chemin DLL      | Chemin de la DLL principale (ex: "..\\VnStudio\\vnresmod.dll")           |

### 2. Table des Variables
La table des variables suit l'en-tête et contient une liste de variables utilisées par le moteur de jeu. Chaque variable est définie par [2]:

*   **Taille de la section** (uint32)
*   Pour chaque variable:
    *   **Longueur du nom de la variable** (uint32)
    *   **Nom de la variable** (chaîne de caractères, terminée par null, en majuscules)
    *   **Valeur initiale** (uint32)

Exemples de variables trouvées dans `couleurs1.vnd` incluent `SACADOS`, `JEU`, `MILLEEURO`, `TELEPHONE`, etc. [2].

### 3. Structure des Enregistrements (Records)
Les données principales du fichier VND sont organisées en enregistrements. Chaque enregistrement est précédé d'un séparateur et contient une longueur, un type et les données associées [2]:

*   **Séparateur**: `01 00 00 00` (uint32 = 1)
*   **Longueur**: Longueur des données de l'enregistrement (uint32)
*   **Type**: Identifiant du type d'enregistrement (uint32)
*   **Données**: Contenu de l'enregistrement (texte ou binaire)

Une énumération complète des types d'enregistrements est fournie dans la documentation [2]. Les types vont de 0 (métadonnées/vide) à plus de 90 (instructions conditionnelles). Des exemples incluent les références de scène (Type 1-2), les scores (Type 3), l'état du jeu (Type 5), les fichiers audio (Type 11), les vidéos (Type 20-24) et les définitions de police (Type 26) [2].

### 4. Structure des Hotspots et Zones Cliquables
Les hotspots, ou zones cliquables, sont définis par une combinaison de texte et de données binaires. Il existe deux types principaux de zones cliquables [2] [8]:

*   **Format Texte**: `[X1] [Y1] [X2] [Y2] 0 [Nom][Suffixe]`
    *   `X1, Y1, X2, Y2`: Coordonnées de la boîte englobante du texte (pas du polygone).
    *   `0`: Séparateur.
    *   `Nom`: Identifiant du hotspot.
    *   `Suffixe`: Caractère optionnel.

*   **Format Binaire** (immédiatement après le texte):
    *   `[NULL_PADDING: 00 00 00]`
    *   `[POINT_COUNT: u32]`: Nombre de points du polygone.
    *   `[COORDINATES: (u32 x, u32 y) × point_count]`: Liste des coordonnées des points du polygone.

*   **Zones Cliquables Rectangulaires (Type 2)**:
    Certains hotspots utilisent une définition rectangulaire simple au lieu d'un polygone. Ces zones sont identifiées par le `type_id = 2` et contiennent les coordonnées de la boîte englobante [8].
    *   `[TYPE: u32]`: `02 00 00 00` (2)
    *   `[X1: u32] [Y1: u32] [X2: u32] [Y2: u32]`: Coordonnées du rectangle.

### 5. Structure des Scènes
Une scène est une unité logique du jeu, contenant des références audio, des images de fond, des définitions de hotspots et des commandes conditionnelles [2].

## Analyse du Code Binaire et des DLLs
Le moteur Virtual Navigator s'appuie sur plusieurs DLLs et un exécutable principal (`europeo.exe`) [3].

### `europeo.exe` - Exécutable Principal
Cet exécutable gère le système de dispatch des commandes. Il contient une table de commandes complète (49 entrées) avec des gestionnaires pour des actions telles que `quit`, `about`, `scene`, `playavi`, `playwav`, `set_var`, `addbmp`, `runprj`, `rundll`, `msgbox`, `playtext`, `font`, etc. [3].

### `vndllapi.dll` - API de Gestion des Variables
Cette DLL exporte des fonctions pour la gestion des variables, notamment `InitVNCommandMessage()`, `VNDLLVarFind()`, `VNDLLVarAddModify()`, et `DirectDrawEnabled()`. La structure `VNDLLVar` est définie comme suit [3]:

```c
typedef struct VNDLLVar {
    char name[256];        // 0x000: Nom de la variable (majuscules)
    int value;             // 0x100: Valeur
    struct VNDLLVar* next; // 0x104: Pointeur vers le prochain élément de la liste chaînée
} VNDLLVar;                // Taille totale: 0x108 (264 octets)
```

### `vnresmod.dll` - Module de Ressources
Cette DLL est responsable de la logique de chargement et d'analyse des fichiers VND. Elle utilise les bibliothèques Borland C++ 1996 et TLS (Thread Local Storage) [3].

### `OWL52t.dll` / `bds52t.dll` - Bibliothèques Borland
Ces DLLs sont des bibliothèques Borland standard: `OWL52t.dll` pour l'interface graphique (ObjectWindows Library) et `bds52t.dll` pour l'entrée/sortie de données binaires (Data Streaming) [3].

## Contradictions et Discrépances

Une contradiction majeure a été identifiée concernant l'identification et la typologie des zones cliquables:

*   **`VND_BINARY_FORMAT.md` et scripts Python (`vnd_deep_decoder.py`, `vnd_polygon_parser.py`)**: Ces sources décrivent la structure binaire des polygones comme suivant immédiatement la définition textuelle du hotspot, sans mentionner un `type_id` distinct pour le polygone lui-même. Le parsing se base sur la position et le `POINT_COUNT` [2] [4] [5].

*   **`decode_vnd_final.py` et nouvelles découvertes**: Ce script Python, présenté comme un décodeur final, identifie spécifiquement les polygones par un `type_id` de `105` [6]. L'analyse des types d'enregistrements dans `couleurs1.vnd` a confirmé la présence de 34 enregistrements avec `type_id: 105`, dont les données sont des listes de coordonnées `{'x': x, 'y': y}` [7]. De plus, une analyse plus approfondie a révélé que les zones cliquables rectangulaires sont identifiées par un `type_id = 2` [8].

Cette divergence suggère que le `type_id = 105` pour les polygones et `type_id = 2` pour les rectangles sont des conventions internes non documentées dans `VND_BINARY_FORMAT.md`, ou des heuristiques de détection utilisées par les décodeurs. Il est probable que ces types soient *toujours* précédés d'un enregistrement de type 105 ou 2 dans la pratique, même si la spécification formelle ne le décrit pas ainsi. Cela représente une incohérence entre la documentation et une implémentation de décodeur, mais clarifie la distinction entre les deux types de zones cliquables.

## Conclusion
Le format VND est un format hybride complexe, bien documenté dans ses grandes lignes, mais présentant des subtilités dans l'implémentation, notamment concernant l'identification des polygones. L'analyse des différents scripts Python a permis de confirmer la plupart des spécifications et de mettre en lumière une potentielle divergence dans la manière dont les polygones sont identifiés au niveau des types d'enregistrements.

## Références

[1] [aciderix/Vndmoteur sur GitHub](https://github.com/aciderix/Vndmoteur/tree/claude/decompile-dll-extraction-YN9Iw)
[2] [VND_BINARY_FORMAT.md](https://github.com/aciderix/Vndmoteur/blob/claude/decompile-dll-extraction-YN9Iw/Doc/VND_BINARY_FORMAT.md)
[3] [REVERSE_ENGINEERING_STATUS.md](https://github.com/aciderix/Vndmoteur/blob/claude/decompile-dll-extraction-YN9Iw/Doc/REVERSE_ENGINEERING_STATUS.md)
[4] [vnd_deep_decoder.py](https://github.com/aciderix/Vndmoteur/blob/claude/decompile-dll-extraction-YN9Iw/vnd_deep_decoder.py)
[5] [vnd_polygon_parser.py](https://github.com/aciderix/Vndmoteur/blob/claude/decompile-dll-extraction-YN9Iw/vnd_polygon_parser.py)
[6] [decode_vnd_final.py](https://github.com/aciderix/Vndmoteur/blob/claude/decompile-dll-extraction-YN9Iw/decode_vnd_final.py)
[7] [Analyse des types d'enregistrements de couleurs1.vnd (sortie console)](#) (référence interne)
[8] [Informations complémentaires sur les types de hotspots (fichier joint par l'utilisateur)](#) (référence interne)]
