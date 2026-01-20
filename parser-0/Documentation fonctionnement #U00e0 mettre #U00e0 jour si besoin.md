Voici la documentation technique détaillée du fonctionnement actuel du parser (services/vndParser.ts) tel qu'il est implémenté dans l'application.
Documentation Technique : VND Sequential Parser (v2.0)
1. Architecture Globale
Le parser est conçu comme une machine à états séquentielle qui analyse un tampon binaire brut (ArrayBuffer) pour en extraire une structure JSON cohérente. Contrairement aux parsers basés uniquement sur des pointeurs absolus (qui échouent souvent si le fichier est décalé), ce parser utilise une approche hybride : Séquentielle + Heuristique.
Flux de Données
Input : Fichier binaire .vnd (chargé en mémoire via DataView et Uint8Array).
Traitement : Analyse en 3 passes (Cartographie, Extraction, Récupération).
Output : Structure JSON typée (ParsedScene[]).
Encodage
Le parser force le décodage de texte en Windows-1252 (ANSI), ce qui est critique pour préserver les accents et caractères spéciaux des jeux Visual Novel anciens.
2. Primitives de Lecture (Niveau Bas)
Pour éviter les crashs dus à des lectures hors-limites, le parser utilise des wrappers sécurisés :
Lecture d'Entiers : readU8, readU32 (Little Endian), readI32. Si l'offset est hors du fichier, retourne 0 au lieu de lever une exception.
Strings Pascal (tryReadString) :
Lit la taille (4 octets) puis les caractères.
Validation Sanitaire : Calcule le ratio de caractères "bizarres" (non-imprimables, < ASCII 32, sauf tab/retours à la ligne). Si plus de 10% de la chaîne est binaire, la chaîne est rejetée. C'est le filtre principal contre la lecture de code machine comme du texte.
3. Algorithme de Parsing (Les 3 Passes)
Phase 1 : Cartographie (Scanning)
Le parser ne suppose pas savoir où commence la première scène.
Il scanne le fichier octet par octet (ou par blocs optimisés).
Il cherche une Table de Fichiers valide via isValidFileTable().
Critère de validité : Une suite de slots (nom de fichier + paramètre) où au moins un fichier porte une extension connue (.bmp, .wav, .avi, .dll) ou est marqué "empty".
Résultat : Une liste d'offsets (startOffsets) indiquant le début probable de chaque scène.
Phase 2 : Extraction Séquentielle (Analyse de Scène)
Pour chaque scène détectée, le parser tente de suivre la structure standard du format VND :
Table de Fichiers (Slots 1-8) :
Lit jusqu'à 8 noms de fichiers.
S'arrête si une signature de fin (0xFFFFFFDB) ou un mot-clé de script (if, =) est rencontré prématurément.
Recherche de l'Ancre (Config) :
Le parser cherche la signature magique 0xFFFFFFDB qui marque généralement la fin du script d'initialisation et le début de la configuration de la scène.
Il vérifie si cette signature est suivie d'une table de Hotspots valide.
Extraction du Script d'Initialisation (InitScript) :
Zone située entre la fin des fichiers et le début de la Config.
Lit des commandes sous forme ID (u32) + Subtype (u32) + Paramètre (String).
Gère les cas particuliers (ID 1 et 2) qui ont des paramètres entiers au lieu de chaînes.
Extraction des Hotspots (Objets Interactifs) :
Lit le nombre d'objets.
Pour chaque objet :
Lit ses commandes (scripts associés).
Lit sa géométrie (Cursor ID, nombre de points, tableau de coordonnées X/Y).
Anti-Desync : Si le nombre de commandes ou de points est aberrant (> 200), le parser arrête la lecture de cet objet pour éviter de lire tout le fichier comme un seul objet.
Phase 3 : Gap Recovery (Heuristique & Réparation)
C'est la fonctionnalité "intelligente" du parser. Si la structure séquentielle est corrompue ou si des données se trouvent entre les blocs standards (le "Gap") :
Scan de la zone morte : Le parser examine les octets non traités entre la fin du script et le début de la config, ou après les hotspots.
Recherche de Mots-clés : Il cherche des chaînes ASCII correspondant à des commandes connues (playwave, addbmp, if, set_var, noms de fichiers .bmp, etc.).
Reconstruction d'Objet :
Si une chaîne est trouvée, il tente de déduire l'ID de la commande (ex: .wav -> ID 1/Sub 11).
Il regarde immédiatement après la chaîne pour voir s'il y a une structure de géométrie (points X/Y).
Classification :
Si l'élément récupéré a une géométrie -> Ajouté aux Hotspots.
Si l'élément est purement logique (ex: var = 1) -> Ajouté à l'Init Script.
4. Structures de Données Clés (Types)
InitCommand & HotspotCommand
code
TypeScript
interface Command {
  id: number;      // Catégorie (0=Graphique, 1=Audio, 3=Logique)
  subtype: number; // Action précise (ex: 24=Zone Image, 21=Script Logic)
  param: string;   // La donnée (nom de fichier, instruction script)
}
Geometry
Représente la zone cliquable (Hitbox).
code
TypeScript
interface Geometry {
  cursorId: number; // ID du curseur à afficher au survol
  points: {x, y}[]; // Polygone de la zone
}
5. Gestion des Erreurs et Santé du Fichier
Le parser attribue un statut à chaque scène :
Signature (CheckCircle) : La structure 0xFFFFFFDB a été trouvée, le parsing est fiable.
Heuristic Recovered (Sparkles) : La structure était cassée, mais le Gap Scanner a reconstruit des données (Hotspots ou Scripts) basés sur des motifs.
Heuristic (Warning) : Aucune structure fiable trouvée, tentative de lecture brute.
6. Différences avec l'approche "Dump brut"
Ce parser ne se contente pas de lire des offsets fixes. Il "surfe" sur les données : si une chaîne est plus longue que prévu, le curseur s'adapte. Si un bloc est manquant, il saute au suivant via la détection de signature. Cela le rend résilient aux modifications manuelles (hex editing) ou aux versions différentes du moteur VND.
