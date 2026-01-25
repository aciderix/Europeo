# 🎮 VND Simulator - Guide d'Utilisation

## Description

Simulateur web interactif pour tester les fichiers VND parsés du jeu Europeo. Permet de naviguer entre les scènes, cliquer sur les hotspots, et vérifier que la structure du jeu fonctionne correctement.

## Lancement

```bash
# Ouvrir dans un navigateur
firefox vnd_simulator.html
# ou
google-chrome vnd_simulator.html
# ou
open vnd_simulator.html  # macOS
```

Ou lancer un serveur HTTP local :

```bash
python3 -m http.server 8000
# Puis ouvrir: http://localhost:8000/vnd_simulator.html
```

## Fonctionnalités

### ✅ Implémenté

#### Navigation
- **GOTO_SCENE** (Type 6): Navigation absolue et relative
  - `3` → Aller à la scène 3
  - `+1` → Scène suivante
  - `-2` → Scène précédente

#### Variables
- **SET_VAR** (Type 22): Définir une variable
  - `api 2` → api = 2
- **INC_VAR** (Type 23): Incrémenter
  - `score 10` → score +10
- **DEC_VAR** (Type 24): Décrémenter
  - `score 1` → score -1 (pénalité)

#### Conditions
- **IF-THEN** (Type 21): Logique conditionnelle
  - `api = 2 then set_var miel 1`
  - `score < 0 then runprj couleurs1.vnp 54`
  - Opérateurs: `=`, `!=`, `<`, `>`, `<=`, `>=`

#### Affichage
- **PLAYTEXT** (Type 38): Afficher du texte à l'écran
  - Format: `x y w h flags texte`
  - Texte affiché pendant 3 secondes

#### Items
- **ITEM TRIGGER** (Type 28): Déclencheur d'objet
  - `miel` → Vérifier variable `api`, goto scene #28 si pas de tenue

#### Système
- **QUIT** (Type 0): Quitter (logged)
- **FONT** (Type 39): Ignoré

### 🔄 Non Implémenté (Placeholders)

- Type 9: PLAYAVI (vidéos)
- Type 11: PLAYWAV (sons)
- Type 27: ADDBMP (images)
- Type 31: RUNPRJ (lancer autre VND)
- Type 36, 41: Autres types

## Interface

### Zone de Jeu
- **Canvas 800×600**: Affiche la scène actuelle
- **Hotspots**: Zones cliquables (visibles en mode debug)
- **Textes**: Affichés temporairement (PLAYTEXT)

### Contrôles
- **Sélecteur VND**: Choisir le fichier à charger
- **Charger**: Charger le VND sélectionné
- **Scène**: Numéro de scène (input manuel)
- **Aller**: Naviguer vers la scène
- **Reset**: Réinitialiser le jeu (score = 0, scène 1)

### Sidebar

#### 📍 Scène Actuelle
- ID de la scène
- Type (game, options, toolbar, etc.)
- Fichiers de la scène
- Nombre de hotspots

#### 📊 Variables
- **Score**: Affiché en haut
- **Autres variables**: Liste dynamique (api, miel, etc.)

#### Mode Debug
- **Checkbox**: Afficher/masquer les hotspots
  - ✅ Activé: Hotspots visibles (bordure jaune)
  - ❌ Désactivé: Hotspots invisibles (mais cliquables)

#### 📝 Log
- Historique de toutes les actions
- Types:
  - 🔵 GOTO (navigation)
  - 🟢 VAR (variables)
  - 🟡 TEXT (textes)
  - 🔴 ERROR (erreurs)

## Utilisation

### Exemple: Tester autr.vnd

1. **Charger le VND**
   - Sélectionner "Autriche" dans le menu
   - Cliquer "Charger"
   - La scène #1 s'affiche

2. **Activer le mode debug**
   - Cocher "Mode Debug"
   - Les hotspots apparaissent en jaune

3. **Cliquer sur un hotspot**
   - Le simulateur exécute les commandes
   - Le log affiche les actions
   - Les variables se mettent à jour
   - La scène change si GOTO

4. **Tester la scène #28 (abeille)**
   - Aller à la scène #27 (input: 27 + Aller)
   - Cliquer sur le hotspot ruche (Type 28: miel)
   - Si `api != 2` → Scene #28 s'affiche
   - Score diminue de -1

5. **Vérifier les variables**
   - Sidebar → Variables
   - `api`, `miel`, `cire`, etc.
   - Score affiché en temps réel

### Exemple: Test IF-THEN

**Scene #3, Hotspot avec condition:**
```
IF: api = 2 then set_var api -1
```

Si la variable `api` vaut 2, elle passe à -1 au clic.

### Exemple: Test Type 28 (miel)

**Scene #27, Hotspot ruche:**
```
Type 28: miel
```

**Logique:**
- Si `api != 2` → GOTO Scene #28 (abeille attaque)
- Si `api == 2` → Collecte miel normalement

**Test:**
1. Set `api = 0` (via console ou autre hotspot)
2. Cliquer sur hotspot miel
3. → Scene #28 s'affiche
4. Score -1

## Limitations

### Images
- Pas d'affichage réel des BMP/AVI
- Placeholder avec nom de fichier
- Background coloré pour identification

### Sons/Vidéos
- PLAYWAV: ignoré
- PLAYAVI: ignoré
- Pas de lecture multimédia

### Commandes Avancées
- RUNPRJ: logged mais pas exécuté
- ADDBMP: pas d'overlay d'images
- Curseurs personnalisés: non supportés

### Limites Parser IF-THEN
- Parser simple, peut ne pas gérer toutes les syntaxes
- Actions complexes ignorées

## Débogage

### Console JavaScript

Ouvrir la console (F12) pour voir les erreurs:

```javascript
// État du jeu
gameState

// Changer une variable manuellement
gameState.variables.api = 2

// Aller à une scène
gotoScene(28)

// Re-render
renderScene(gameState.currentScene)
```

### Vérifier Structure VND

Si une scène ne fonctionne pas:
1. Vérifier le JSON parsé (ouvrir le .parsed.json)
2. Chercher la scène par ID
3. Vérifier les commandes des hotspots
4. Tester les conditions IF-THEN

### Log Détaillé

Le log affiche:
- Changements de scène
- Modifications de variables
- Textes affichés
- Erreurs de parsing

## Problèmes Connus

### Hotspots Sans Géométrie
- Hotspots système (Type 24, etc.) sans `pointCount`
- Non affichés, mais commandes exécutées lors du InitScript

### IF-THEN Complexes
- Syntaxe: `condition then action`
- Actions multiples sur une ligne: partiellement supporté
- Nested IF: non supporté

### Scènes Empty/Toolbar
- Pas de hotspots visuels
- Peuvent avoir InitScript exécuté automatiquement

## Améliorations Futures

### Court Terme
- [ ] Support ADDBMP (overlay d'images placeholder)
- [ ] Meilleur parser IF-THEN (multiple actions)
- [ ] Affichage durée textes (PLAYTEXT timing)

### Moyen Terme
- [ ] Support RUNPRJ (charger autre VND)
- [ ] Historique navigation (bouton retour)
- [ ] Save/Load état du jeu

### Long Terme
- [ ] Support images BMP réelles
- [ ] Support vidéos AVI (HTML5 video)
- [ ] Support sons WAV
- [ ] Éditeur de scènes intégré

## Tests Recommandés

### Test 1: Navigation Basique
1. Charger autr.vnd
2. Scène 1 → Clic hotspot → Vérifier GOTO
3. Tester +1, -1, absolu

### Test 2: Variables
1. Charger autr.vnd, scène 13
2. Cliquer hotspot quiz
3. Vérifier score augmente

### Test 3: Conditions
1. Charger autr.vnd, scène 3
2. Set `api = 0`
3. Clic sur hotspot avec IF-THEN
4. Vérifier action conditionnelle

### Test 4: Type 28 (Item)
1. Charger autr.vnd, scène 27
2. Set `api = 0`
3. Clic hotspot miel
4. Vérifier → Scene #28
5. Vérifier score -1

### Test 5: Tous les VND
1. Tester chaque VND (15 fichiers)
2. Vérifier scène 0 (global_vars)
3. Tester navigation scènes principales
4. Chercher erreurs de structure

## Contribution

Pour améliorer le simulateur:
1. Ouvrir `vnd_simulator.html`
2. Modifier le JavaScript
3. Tester avec plusieurs VND
4. Documenter les changements

## Support

En cas de problème:
- Vérifier la console JavaScript (F12)
- Vérifier le format JSON du VND parsé
- Vérifier que le fichier existe
- Vérifier les commandes supportées

---

**Créé le**: 2026-01-25
**Version**: 1.0
**Auteur**: VND Parser Project
