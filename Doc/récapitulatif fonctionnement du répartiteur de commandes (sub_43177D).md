Voici un récapitulatif complet du fonctionnement du répartiteur de commandes (**sub_43177D**) du moteur `TVNApplication`, intégrant l'analyse des séquences binaires et le rôle des suffixes.

### 1. Architecture du Répartiteur (`sub_43177D`)
Le répartiteur est le cœur logique du moteur. Il fonctionne comme une **boucle de traitement de flux** (stream) qui lit le fichier `.vnd` octet par octet. Son rôle est de faire la transition entre les données brutes et les fonctions internes de l'exécutable (affichage, son, navigation).

### 2. Le Mécanisme de "Parsing" des Données
Le point crucial pour comprendre le fonctionnement est la manière dont le moteur sépare les **arguments** des **instructions**.

*   **Consommation des données :** Pour les nombres, la fonction **sub_407FE5** utilise la commande C standard **`atol()`**. Cette fonction extrait tous les chiffres d'une chaîne et **s'arrête net dès qu'elle rencontre un caractère non numérique**.
*   **Chaînage séquentiel :** Une fois que la donnée (nombre ou texte) est consommée, le pointeur de lecture du flux binaire se trouve exactement sur l'octet suivant. Le répartiteur interprète alors cet octet comme l'**Opcode** à exécuter immédiatement.
*   **Le cas des suffixes :** Des séquences comme `54h` ne sont pas une seule instruction, mais deux : le paramètre `54` est chargé pour l'action en cours (ex: `runprj`), puis l'Opcode `h` (Opcode 8 : Tooltip) est exécuté sur le champ.

### 3. Analyse du suffixe "j" (Dossier euroj)
Dans la séquence binaire `65 75 72 6f 6a` (euroj), la distinction est purement structurelle pour le répartiteur :
*   **La donnée :** Le moteur lit la chaîne ASCII "euro" (`65 75 72 6f`). Il identifie la fin du champ textuel grâce à des délimiteurs ou à la longueur définie dans le bloc.
*   **L'instruction :** L'octet suivant est `6a`, soit la lettre **"j"**. Selon la table de conversion du moteur (`index = char - 'a' + 1`), **"j" correspond à l'Opcode 10**.
*   **L'action :** L'Opcode 10 déclenche la fonction **`playbmp`** (**sub_4275F6**), qui gère l'affichage des bitmaps, la transparence et les palettes de couleurs. Les octets qui suivent le `j` dans le binaire sont alors lus comme les paramètres de cette fonction (coordonnées, index de palette).

### 4. Table des Opcones Principaux
Le répartiteur utilise un `switch case` basé sur l'index de la lettre :

| Lettre | Index | Fonction | Rôle |
| :--- | :--- | :--- | :--- |
| **f** | 6 | `sub_4268F8` | **Saut de scène** (Navigation interne). |
| **h** | 8 | `sub_426D33` | **Tooltip** (Affichage d'une bulle d'aide). |
| **i** | 9 | `sub_42703A` | **Images** (Chargement d'AVI ou BMP). |
| **j** | 10 | `sub_4275F6` | **Bitmaps** (Gestion technique des couleurs). |
| **u** | 21 | `sub_431721` | **Logic/Callback** (Vérification des conditions). |
| **31 (num)** | - | `sub_42908F` | **Run Project** (Chargement d'un autre fichier `.vnp`). |

### 5. Logique de Navigation et de Calcul
Le répartiteur ne se contente pas d'exécuter des sauts fixes ; il calcule les cibles dynamiquement selon le suffixe rencontré :
*   **Calcul par Index (`i`) :** La cible finale est `INDEX_ID` (lu à l'offset 65 du projet) + `N`.
*   **Saut Relatif (`+` / `-`) :** Le parseur identifie ces signes en début de chaîne pour calculer `Scène_Actuelle +/- N`.
*   **Saut Direct (`d`) :** Utilise la valeur numérique brute comme ID absolu de scène.

### 6. Gestion des Variables et Conditions
Pour les commandes complexes (Opcode 21 'u'), le répartiteur interagit avec un **tableau global de variables** situé à l'adresse **`dword_44ECCE`**. Les opérateurs de comparaison (codes 1 à 6) permettent de valider des conditions comme `score < 0` avant de décider de l'instruction de saut suivante.

**En résumé :** Le répartiteur traite le fichier `.vnd` comme un flux ininterrompu où les données "poussent" les instructions. Le caractère "j" à la fin de "euro" n'est rien d'autre que l'ordre de rendu graphique (**playbmp**) injecté immédiatement après le label textuel dans le binaire.
