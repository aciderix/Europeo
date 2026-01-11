# Liste Exhaustive des Types d'Enregistrements VND

Ce document répertorie tous les types d'enregistrements identifiés dans le format VND, en consolidant les informations provenant de la spécification officielle [2], des analyses de code binaire [3] [4] [5] [6], et des découvertes récentes [8].

## Types d'Enregistrements Documentés et Observés

| Type ID | Hex | Description | Source(s) | Notes |
|---------|-----|-------------|-----------|-------|
| 0       | 0x00 | Métadonnées / Enregistrements vides / Chemins DLL / Noms de variables | [2], [8] | Utilisé pour la structure, le padding, les chemins de DLL et les noms de variables. |
| 1       | 0x01 | Référence de scène primaire | [2] | Numéros de scène courts. |
| 2       | 0x02 | Référence de scène secondaire / variante / **Zone cliquable rectangulaire** | [2], [8] | Numéros de scène courts. **Nouvelle découverte: utilisé pour les zones cliquables rectangulaires.** |
| 3       | 0x03 | Enregistrements de score / valeur | [2] | Valeurs numériques, généralement des scores. |
| 5       | 0x05 | État du jeu ("jeu") | [2] | Références de variables d'état du jeu. |
| 6       | 0x06 | Enregistrements de drapeaux (flags) / Numéros de scène | [2], [8] | Drapeaux d'état booléens. **Observé aussi pour les numéros de scène.** |
| 7       | 0x07 | Définitions de variables | [2] | Structures de variables complexes. |
| 8       | 0x08 | État Annuler/Activer / Audio (WAV, AVI) | [2], [8] | État pour les actions annuler/activer. **Observé aussi pour les fichiers audio.** |
| 9       | 0x09 | État Occupé | [2] | Suivi de l'occupation des slots. |
| 10      | 0x0A | Définitions de curseur / rollover / Audio (WAV, AVI) | [2], [8] | Définitions visuelles de curseur et rollover. **Observé aussi pour les fichiers audio.** |
| 11      | 0x0B | Fichiers audio WAV | [2], [8] | Références de fichiers audio. **Observé aussi pour les fichiers audio.** |
| 12      | 0x0C | Effets sonores secondaires | [2] | Références audio secondaires. |
| 15      | 0x0F | Structure de bloc | [2] | Grand bloc de données (potentiellement bloc de définition de scène). |
| 16      | 0x10 | Inconnu | [8] | Observé dans `couleurs1.vnd` avec une valeur de 500. |
| 17      | 0x11 | Effets sonores (chemin) | [2] | Effets sonores avec chemins de dossiers. |
| 19      | 0x13 | Références de projet | [2] | Liens vers d'autres fichiers de projet VNP. |
| 20      | 0x14 | Chemins multimédia (vidéos AVI - home/museum) | [2] | Références de fichiers vidéo. |
| 21      | 0x15 | Chemins multimédia (vidéos AVI - départ) / Conditionnels | [2], [8] | Références de fichiers vidéo. **Observé aussi pour les commandes conditionnelles.** |
| 22      | 0x16 | Chemins multimédia (vidéos AVI - emplacement secondaire) | [2] | Références de fichiers vidéo. |
| 23      | 0x17 | Chemins multimédia (vidéos AVI - scène spécifique) | [2] | Références de fichiers vidéo. |
| 24      | 0x18 | Chemins multimédia (vidéos AVI - bibliothèque) | [2] | Références de fichiers vidéo. |
| 25+     | 0x19+ | Instructions conditionnelles ("if X then Y") | [2], [8] | Logique conditionnelle avec divers types d'actions. |
| 26      | 0x1A | Définitions de police | [2], [8] | Paramètres de police pour l'affichage du texte. |
| 27      | 0x1B | Action `closewav`, `scene` / `addbmp` | [2], [8] | Actions spécifiques. **Observé aussi pour `addbmp`.** |
| 28      | 0x1C | Action `delbmp`, `dec_var` / `clejaune` | [2], [8] | Actions spécifiques. **Observé aussi pour `clejaune`.** |
| 29      | 0x1D | Action `hotspot enable/disable` | [2] | Activation/désactivation des hotspots. |
| 30      | 0x1E | Action `dec_var` / `etoile` | [2], [8] | Action spécifique. **Observé aussi pour `etoile`.** |
| 31      | 0x1F | Action `rundll` / `runprj` | [2], [8] | Action spécifique. **Observé aussi pour `runprj`.** |
| 32      | 0x20 | Action `set_var`, `playtext` | [2] | Actions spécifiques. |
| 33      | 0x21 | Action `dec_var`, `set_var` | [2] | Actions spécifiques. |
| 34      | 0x22 | Action `rundll`, `delbmp`, `dec_var` | [2] | Actions spécifiques. |
| 35      | 0x23 | Action `playavi`, `playwav` | [2] | Actions spécifiques. |
| 36      | 0x24 | Action `playavi` (avec coordonnées) | [2] | Action spécifique. |
| 37      | 0x25 | Action `set_var`, `playwav` | [2] | Actions spécifiques. |
| 38      | 0x26 | Action `playtext` / **Texte hotspot** | [2], [8] | Action spécifique. **Nouvelle découverte: utilisé pour le texte des hotspots.** |
| 39      | 0x27 | Action `runprj`, `playwav` / **Définitions de police** | [2], [8] | Actions spécifiques. **Observé aussi pour les définitions de police.** |
| 40      | 0x28 | Action `runprj`, `rundll` / Commentaire (`rem`) | [2], [3] | Actions spécifiques. **Observé aussi pour les commentaires.** |
| 41      | 0x29 | Action `playwav`, `runprj` / `addtext` | [2], [3] | Actions spécifiques. **Observé aussi pour `addtext`.** |
| 42      | 0x2A | Action `runprj`, `dec_var` | [2] | Actions spécifiques. |
| 43      | 0x2B | Action `runprj` | [2] | Action spécifique. |
| 44      | 0x2C | Action `runprj` | [2] | Action spécifique. |
| 45      | 0x2D | Action `runprj` | [2] | Action spécifique. |
| 47      | 0x2F | Action `dec_var` | [2] | Action spécifique. |
| 48      | 0x30 | Action `font` | [2] | Action spécifique. |
| 50      | 0x32 | Action `playavi` | [2] | Action spécifique. |
| 51      | 0x33 | Action `playavi` | [2] | Action spécifique. |
| 52      | 0x34 | Action `addbmp` | [2] | Action spécifique. |
| 54      | 0x36 | Action `runprj`, `addbmp` | [2] | Actions spécifiques. |
| 55      | 0x37 | Action `runprj`, `addbmp` | [2] | Actions spécifiques. |
| 56      | 0x38 | Action `runprj`, `addbmp` | [2] | Actions spécifiques. |
| 58-65   | 0x3A-0x41 | Action `addbmp`, `playtext` | [2] | Actions spécifiques. |
| 69      | 0x45 | Inconnu | [8] | Observé dans `couleurs1.vnd`. |
| 70-75   | 0x46-0x4B | Action `playtext`, `addbmp` | [2] | Actions spécifiques. |
| 83      | 0x53 | Inconnu | [8] | Observé dans `couleurs1.vnd`. |
| 89-90   | 0x59-0x5A | Action `playtext` | [2] | Actions spécifiques. |
| 105     | 0x69 | **Zone cliquable polygonale** | [6], [8] | **Nouvelle découverte: utilisé pour les zones cliquables polygonales.** |
| 257     | 0x101 | Signature "VNFILE" (artefact de parsing) | [7] | Mauvaise interprétation de la signature de l'en-tête comme un enregistrement. |
| 280     | 0x118 | Nom de variable (artefact de parsing) | [7] | Mauvaise interprétation du premier nom de variable comme un enregistrement. |
| 620     | 0x26C | Caractère '{' (artefact de parsing) | [7] | Probablement une erreur de parsing ou une donnée non interprétée. |
| 1397563507 | 0x53534133 | Caractère '&' (artefact de parsing) | [7] | Probablement une erreur de parsing ou une donnée non interprétée. |
| 1634296933 | 0x61636965 | Checksum (artefact de parsing) | [7] | Mauvaise interprétation du checksum de l'en-tête comme un enregistrement. |
| 1936747877 | 0x73746f68 | Caractère '&' (artefact de parsing) | [7] | Probablement une erreur de parsing ou une donnée non interprétée. |

## Références

[1] [aciderix/Vndmoteur sur GitHub](https://github.com/aciderix/Vndmoteur/tree/claude/decompile-dll-extraction-YN9Iw)
[2] [VND_BINARY_FORMAT.md](https://github.com/aciderix/Vndmoteur/blob/claude/decompile-dll-extraction-YN9Iw/Doc/VND_BINARY_FORMAT.md)
[3] [REVERSE_ENGINEERING_STATUS.md](https://github.com/aciderix/Vndmoteur/blob/claude/decompile-dll-extraction-YN9Iw/Doc/REVERSE_ENGINEERING_STATUS.md)
[4] [vnd_deep_decoder.py](https://github.com/aciderix/Vndmoteur/blob/claude/decompile-dll-extraction-YN9Iw/vnd_deep_decoder.py)
[5] [vnd_polygon_parser.py](https://github.com/aciderix/Vndmoteur/blob/claude/decompile-dll-extraction-YN9Iw/vnd_polygon_parser.py)
[6] [decode_vnd_final.py](https://github.com/aciderix/Vndmoteur/blob/claude/decompile-dll-extraction-YN9Iw/decode_vnd_final.py)
[7] [Analyse des types d'enregistrements de couleurs1.vnd (sortie console)](#) (référence interne)
[8] [Informations complémentaires sur les types de hotspots (fichier joint par l'utilisateur)](#) (référence interne)
