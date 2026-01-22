# Guide d'Implémentation React - Europeo

Ce guide fournit des exemples de code concrets pour implémenter le moteur de jeu Europeo en React.

---

## 1. Architecture Proposée

```
src/
├── engine/
│   ├── GameEngine.ts          # Moteur principal
│   ├── ConditionEvaluator.ts  # Évaluateur de conditions
│   ├── ActionExecutor.ts      # Exécuteur d'actions
│   └── SceneParser.ts         # Parser de scènes
├── components/
│   ├── Game.tsx               # Composant principal
│   ├── Scene.tsx              # Rendu de scène
│   ├── Hotspot.tsx            # Élément cliquable
│   ├── Toolbar.tsx            # Barre d'outils
│   ├── VideoPlayer.tsx        # Lecteur vidéo
│   └── TextDisplay.tsx        # Affichage de texte
├── data/
│   ├── scenes/                # JSON des scènes par pays
│   ├── variables.ts           # Définition des variables
│   └── countries.ts           # Configuration des pays
├── hooks/
│   ├── useGameState.ts        # État du jeu
│   ├── useAudio.ts            # Gestion audio
│   └── useHotspot.ts          # Logique hotspots
└── types/
    └── game.ts                # Types TypeScript
```

---

## 2. Types TypeScript

```typescript
// types/game.ts

export type Operator = '=' | '!=' | '<' | '>';

export interface Condition {
  variable: string;
  operator: Operator;
  value: number;
  then: Action | Action[];
  else?: Action | Action[];
}

export type Action =
  | SceneAction
  | RunProjectAction
  | AddBmpAction
  | DelBmpAction
  | PlayAviAction
  | PlayWavAction
  | PlayTextAction
  | SetVarAction
  | IncVarAction
  | DecVarAction
  | RunDllAction
  | CloseWavAction;

export interface SceneAction {
  type: 'scene';
  target: number;
}

export interface RunProjectAction {
  type: 'runprj';
  project: string;  // ex: "../angl/angleterre.vnp"
  scene: number;
}

export interface AddBmpAction {
  type: 'addbmp';
  id: string;
  image: string;
  layer: number;
  x: number;
  y: number;
}

export interface DelBmpAction {
  type: 'delbmp';
  id: string;
}

export interface PlayAviAction {
  type: 'playavi';
  file: string;
  loop: boolean;
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface PlayWavAction {
  type: 'playwav';
  file: string;
  mode: 'once' | 'loop' | 'ambient';
}

export interface PlayTextAction {
  type: 'playtext';
  text: string;
  x: number;
  y: number;
  width: number;
  height: number;
  style?: TextStyle;
}

export interface TextStyle {
  fontSize: number;
  bold: boolean;
  color: string;
  fontFamily: string;
}

export interface SetVarAction {
  type: 'set_var';
  variable: string;
  value: number;
}

export interface IncVarAction {
  type: 'inc_var';
  variable: string;
  value: number;
}

export interface DecVarAction {
  type: 'dec_var';
  variable: string;
  value: number;
}

export interface RunDllAction {
  type: 'rundll';
  dll: string;
}

export interface CloseWavAction {
  type: 'closewav';
}

// Hotspot
export interface Hotspot {
  id: string;
  image: string;
  x: number;
  y: number;
  layer: number;
  visible: boolean;
  onClick?: Condition[];
  onHover?: Condition[];
}

// Scène
export interface Scene {
  id: number;
  background: string;
  music?: string;
  musicMode?: 'once' | 'loop';
  hotspots: Hotspot[];
  onEnter: Condition[];
  onExit?: Condition[];
  textStyle?: TextStyle;
}

// État du jeu
export interface GameState {
  // Navigation
  currentCountry: string;
  currentScene: number;
  previousScene?: number;

  // Score et progression
  score: number;
  fiole: number;  // 0-12

  // Pays (0=non visité, 1=visité/actif)
  countries: {
    france: number;
    allemagne: number;
    angleterre: number;
    autriche: number;
    belgique: number;
    danemark: number;
    ecosse: number;
    espagne: number;
    finlande: number;
    grece: number;
    irlande: number;
    italie: number;
    paysbas: number;
    portugal: number;
    suede: number;
    euroland: number;
  };

  // Outils (0=inactif, 1=actif)
  tools: {
    calc: number;
    telephone: number;
    sacados: number;
    trans: number;
    active: number;
  };

  // Inventaire - objets (0=inconnu, 1=vu, 2=possédé)
  inventory: Record<string, number>;

  // Variables de quêtes
  quests: Record<string, number>;

  // Bonus collectés
  bonus: Record<string, number>;

  // Sprites dynamiques actifs
  activeSprites: Map<string, Hotspot>;

  // Textes affichés
  displayedTexts: Array<{
    id: string;
    text: string;
    x: number;
    y: number;
    style: TextStyle;
  }>;
}
```

---

## 3. Moteur de Conditions

```typescript
// engine/ConditionEvaluator.ts

import { Condition, Operator, GameState } from '../types/game';

export class ConditionEvaluator {

  /**
   * Récupère la valeur d'une variable depuis l'état du jeu
   */
  getVariable(name: string, state: GameState): number {
    const lowerName = name.toLowerCase();

    // Variables spéciales
    if (lowerName === 'score') return state.score;
    if (lowerName === 'fiole') return state.fiole;
    if (lowerName === 'non') return state.quests.non ?? 0;

    // Pays
    if (lowerName in state.countries) {
      return state.countries[lowerName as keyof typeof state.countries];
    }

    // Outils
    if (lowerName in state.tools) {
      return state.tools[lowerName as keyof typeof state.tools];
    }

    // Inventaire
    if (lowerName in state.inventory) {
      return state.inventory[lowerName];
    }

    // Bonus
    if (lowerName.startsWith('bonus')) {
      return state.bonus[lowerName] ?? 0;
    }

    // Variables de quêtes
    return state.quests[lowerName] ?? 0;
  }

  /**
   * Évalue une condition
   */
  evaluate(condition: Condition, state: GameState): boolean {
    const value = this.getVariable(condition.variable, state);

    switch (condition.operator) {
      case '=':
        return value === condition.value;
      case '!=':
        return value !== condition.value;
      case '<':
        return value < condition.value;
      case '>':
        return value > condition.value;
      default:
        console.warn(`Opérateur inconnu: ${condition.operator}`);
        return false;
    }
  }

  /**
   * Évalue une liste de conditions et retourne les actions à exécuter
   */
  evaluateAll(conditions: Condition[], state: GameState): Action[] {
    const actions: Action[] = [];

    for (const condition of conditions) {
      const result = this.evaluate(condition, state);
      const actionList = result ? condition.then : condition.else;

      if (actionList) {
        if (Array.isArray(actionList)) {
          actions.push(...actionList);
        } else {
          actions.push(actionList);
        }
      }
    }

    return actions;
  }
}
```

---

## 4. Exécuteur d'Actions

```typescript
// engine/ActionExecutor.ts

import { Action, GameState, Hotspot } from '../types/game';

export class ActionExecutor {
  private audioManager: AudioManager;
  private videoManager: VideoManager;
  private onSceneChange: (country: string, scene: number) => void;
  private onDllCall: (dll: string) => void;

  constructor(config: {
    audioManager: AudioManager;
    videoManager: VideoManager;
    onSceneChange: (country: string, scene: number) => void;
    onDllCall: (dll: string) => void;
  }) {
    this.audioManager = config.audioManager;
    this.videoManager = config.videoManager;
    this.onSceneChange = config.onSceneChange;
    this.onDllCall = config.onDllCall;
  }

  /**
   * Exécute une action et retourne le nouvel état
   */
  execute(action: Action, state: GameState): GameState {
    switch (action.type) {
      case 'scene':
        return this.executeScene(action, state);

      case 'runprj':
        return this.executeRunProject(action, state);

      case 'addbmp':
        return this.executeAddBmp(action, state);

      case 'delbmp':
        return this.executeDelBmp(action, state);

      case 'set_var':
        return this.executeSetVar(action, state);

      case 'inc_var':
        return this.executeIncVar(action, state);

      case 'dec_var':
        return this.executeDecVar(action, state);

      case 'playwav':
        this.audioManager.play(action.file, action.mode);
        return state;

      case 'closewav':
        this.audioManager.stop();
        return state;

      case 'playavi':
        this.videoManager.play(action);
        return state;

      case 'playtext':
        return this.executePlayText(action, state);

      case 'rundll':
        this.onDllCall(action.dll);
        return state;

      default:
        console.warn('Action inconnue:', action);
        return state;
    }
  }

  private executeScene(action: SceneAction, state: GameState): GameState {
    this.onSceneChange(state.currentCountry, action.target);
    return {
      ...state,
      previousScene: state.currentScene,
      currentScene: action.target,
    };
  }

  private executeRunProject(action: RunProjectAction, state: GameState): GameState {
    // Parser le chemin du projet pour extraire le pays
    // Ex: "../angl/angleterre.vnp" -> "angleterre"
    const match = action.project.match(/([^/\\]+)\.vnp$/i);
    const country = match ? match[1].toLowerCase() : state.currentCountry;

    this.onSceneChange(country, action.scene);
    return {
      ...state,
      previousScene: state.currentScene,
      currentCountry: country,
      currentScene: action.scene,
    };
  }

  private executeAddBmp(action: AddBmpAction, state: GameState): GameState {
    const newSprite: Hotspot = {
      id: action.id,
      image: action.image,
      x: action.x,
      y: action.y,
      layer: action.layer,
      visible: true,
    };

    const newSprites = new Map(state.activeSprites);
    newSprites.set(action.id, newSprite);

    return {
      ...state,
      activeSprites: newSprites,
    };
  }

  private executeDelBmp(action: DelBmpAction, state: GameState): GameState {
    const newSprites = new Map(state.activeSprites);
    newSprites.delete(action.id);

    return {
      ...state,
      activeSprites: newSprites,
    };
  }

  private executeSetVar(action: SetVarAction, state: GameState): GameState {
    return this.updateVariable(state, action.variable, action.value);
  }

  private executeIncVar(action: IncVarAction, state: GameState): GameState {
    const currentValue = this.getVariable(action.variable, state);
    return this.updateVariable(state, action.variable, currentValue + action.value);
  }

  private executeDecVar(action: DecVarAction, state: GameState): GameState {
    const currentValue = this.getVariable(action.variable, state);
    return this.updateVariable(state, action.variable, currentValue - action.value);
  }

  private executePlayText(action: PlayTextAction, state: GameState): GameState {
    const textId = `text_${Date.now()}`;
    return {
      ...state,
      displayedTexts: [
        ...state.displayedTexts,
        {
          id: textId,
          text: action.text,
          x: action.x,
          y: action.y,
          style: action.style || { fontSize: 18, bold: false, color: '#ffffff', fontFamily: 'Comic Sans MS' },
        },
      ],
    };
  }

  private getVariable(name: string, state: GameState): number {
    // Réutilise la logique de ConditionEvaluator
    const evaluator = new ConditionEvaluator();
    return evaluator.getVariable(name, state);
  }

  private updateVariable(state: GameState, name: string, value: number): GameState {
    const lowerName = name.toLowerCase();

    if (lowerName === 'score') {
      return { ...state, score: value };
    }

    if (lowerName === 'fiole') {
      return { ...state, fiole: Math.max(0, Math.min(12, value)) };
    }

    if (lowerName in state.countries) {
      return {
        ...state,
        countries: { ...state.countries, [lowerName]: value },
      };
    }

    if (lowerName in state.tools) {
      return {
        ...state,
        tools: { ...state.tools, [lowerName]: value },
      };
    }

    // Inventaire ou quêtes
    if (state.inventory[lowerName] !== undefined) {
      return {
        ...state,
        inventory: { ...state.inventory, [lowerName]: value },
      };
    }

    // Variable de quête par défaut
    return {
      ...state,
      quests: { ...state.quests, [lowerName]: value },
    };
  }
}
```

---

## 5. Composant Scène

```tsx
// components/Scene.tsx

import React, { useEffect, useMemo } from 'react';
import { Scene as SceneType, Hotspot as HotspotType, GameState } from '../types/game';
import { Hotspot } from './Hotspot';
import { VideoPlayer } from './VideoPlayer';
import { TextDisplay } from './TextDisplay';

interface SceneProps {
  scene: SceneType;
  state: GameState;
  onHotspotClick: (hotspot: HotspotType) => void;
}

export const Scene: React.FC<SceneProps> = ({ scene, state, onHotspotClick }) => {
  // Combiner les hotspots de la scène avec les sprites dynamiques
  const allHotspots = useMemo(() => {
    const sceneHotspots = scene.hotspots.filter(h => h.visible);
    const dynamicSprites = Array.from(state.activeSprites.values());
    return [...sceneHotspots, ...dynamicSprites].sort((a, b) => a.layer - b.layer);
  }, [scene.hotspots, state.activeSprites]);

  // Séparer par couche
  const backgroundLayer = allHotspots.filter(h => h.layer === 0);
  const uiLayer = allHotspots.filter(h => h.layer === 6);

  return (
    <div
      className="scene"
      style={{
        width: 640,
        height: 480,
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Background */}
      <img
        src={`/assets/${state.currentCountry}/img24/${scene.background}`}
        alt="background"
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: 640,
          height: 400,
        }}
      />

      {/* Hotspots layer 0 (jeu) */}
      {backgroundLayer.map(hotspot => (
        <Hotspot
          key={hotspot.id}
          hotspot={hotspot}
          basePath={`/assets/${state.currentCountry}/img24`}
          onClick={() => onHotspotClick(hotspot)}
        />
      ))}

      {/* Textes affichés */}
      {state.displayedTexts.map(text => (
        <TextDisplay
          key={text.id}
          text={text.text}
          x={text.x}
          y={text.y}
          style={text.style}
        />
      ))}

      {/* UI Layer (toolbar) - rendu séparément */}
    </div>
  );
};
```

---

## 6. Composant Hotspot

```tsx
// components/Hotspot.tsx

import React, { useState, useEffect } from 'react';
import { Hotspot as HotspotType } from '../types/game';

interface HotspotProps {
  hotspot: HotspotType;
  basePath: string;
  onClick: () => void;
}

export const Hotspot: React.FC<HotspotProps> = ({ hotspot, basePath, onClick }) => {
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  const [isHovered, setIsHovered] = useState(false);

  // Charger les dimensions de l'image pour définir la zone de clic
  useEffect(() => {
    const img = new Image();
    img.onload = () => {
      setDimensions({ width: img.width, height: img.height });
    };
    img.src = `${basePath}/${hotspot.image.replace(/\\/g, '/')}`;
  }, [basePath, hotspot.image]);

  const imagePath = `${basePath}/${hotspot.image.replace(/\\/g, '/')}`;

  return (
    <div
      style={{
        position: 'absolute',
        left: hotspot.x,
        top: hotspot.y,
        width: dimensions.width,
        height: dimensions.height,
        cursor: 'pointer',
        zIndex: hotspot.layer,
      }}
      onClick={onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <img
        src={imagePath}
        alt={hotspot.id}
        style={{
          width: '100%',
          height: '100%',
          // Effet de survol optionnel
          filter: isHovered ? 'brightness(1.2)' : 'none',
          transition: 'filter 0.2s',
        }}
        draggable={false}
      />
    </div>
  );
};
```

---

## 7. Hook useGameState

```typescript
// hooks/useGameState.ts

import { useReducer, useCallback } from 'react';
import { GameState, Action, Condition } from '../types/game';
import { ConditionEvaluator } from '../engine/ConditionEvaluator';
import { ActionExecutor } from '../engine/ActionExecutor';

const initialState: GameState = {
  currentCountry: 'france',
  currentScene: 1,
  score: 100,  // Score de départ
  fiole: 0,

  countries: {
    france: 0,
    allemagne: 0,
    angleterre: 0,
    autriche: 0,
    belgique: 0,
    danemark: 0,
    ecosse: 0,
    espagne: 0,
    finlande: 0,
    grece: 0,
    irlande: 0,
    italie: 0,
    paysbas: 0,
    portugal: 0,
    suede: 0,
    euroland: 0,
  },

  tools: {
    calc: 1,       // Calculatrice active par défaut
    telephone: 1,
    sacados: 1,
    trans: 1,
    active: 0,
  },

  inventory: {},
  quests: {},
  bonus: {},
  activeSprites: new Map(),
  displayedTexts: [],
};

type GameAction =
  | { type: 'EXECUTE_ACTION'; action: Action }
  | { type: 'EXECUTE_CONDITIONS'; conditions: Condition[] }
  | { type: 'CLEAR_TEXTS' }
  | { type: 'RESET' };

function gameReducer(state: GameState, gameAction: GameAction): GameState {
  switch (gameAction.type) {
    case 'EXECUTE_ACTION':
      // Sera géré par ActionExecutor
      return state;

    case 'CLEAR_TEXTS':
      return { ...state, displayedTexts: [] };

    case 'RESET':
      return initialState;

    default:
      return state;
  }
}

export function useGameState() {
  const [state, dispatch] = useReducer(gameReducer, initialState);

  const evaluator = new ConditionEvaluator();

  const executeConditions = useCallback((conditions: Condition[]) => {
    const actions = evaluator.evaluateAll(conditions, state);
    // Exécuter les actions via ActionExecutor
    // (à connecter avec le contexte du jeu)
  }, [state]);

  const getVariable = useCallback((name: string) => {
    return evaluator.getVariable(name, state);
  }, [state]);

  return {
    state,
    dispatch,
    executeConditions,
    getVariable,
  };
}
```

---

## 8. Exemple de données de scène (JSON)

```json
{
  "country": "france",
  "scenes": [
    {
      "id": 1,
      "background": "paris2.bmp",
      "music": "france.wav",
      "musicMode": "loop",
      "textStyle": {
        "fontSize": 18,
        "bold": false,
        "color": "#ffffff",
        "fontFamily": "Comic Sans MS"
      },
      "onEnter": [
        {
          "variable": "score",
          "operator": "<",
          "value": 0,
          "then": {
            "type": "runprj",
            "project": "../couleurs1/couleurs1.vnp",
            "scene": 54
          }
        },
        {
          "variable": "france",
          "operator": "=",
          "value": 0,
          "then": {
            "type": "set_var",
            "variable": "france",
            "value": 1
          }
        }
      ],
      "hotspots": [
        {
          "id": "parfumerie",
          "image": "hotspot_parfum.png",
          "x": 450,
          "y": 200,
          "layer": 0,
          "visible": true,
          "onClick": [
            {
              "variable": "true",
              "operator": "=",
              "value": 1,
              "then": [
                {
                  "type": "playtext",
                  "text": "Une parfumerie de luxe",
                  "x": 780,
                  "y": 370,
                  "width": 375,
                  "height": 365
                },
                {
                  "type": "scene",
                  "target": 5
                }
              ]
            }
          ]
        },
        {
          "id": "tour_eiffel",
          "image": "hotspot_tour.png",
          "x": 550,
          "y": 100,
          "layer": 0,
          "visible": true,
          "onClick": [
            {
              "variable": "ticket",
              "operator": "=",
              "value": 1,
              "then": {
                "type": "scene",
                "target": 13
              },
              "else": {
                "type": "playtext",
                "text": "Il faut un ticket pour entrer !",
                "x": 100,
                "y": 280,
                "width": 365,
                "height": 365
              }
            }
          ]
        }
      ]
    }
  ]
}
```

---

## 9. Gestion des DLLs (Mini-jeux)

```typescript
// components/MiniGameManager.tsx

import React from 'react';
import { EuroCalculator } from './tools/EuroCalculator';
import { Inventory } from './tools/Inventory';
// Autres mini-jeux...

interface MiniGameManagerProps {
  activeDll: string | null;
  onClose: () => void;
  gameState: GameState;
  onStateChange: (state: GameState) => void;
}

export const MiniGameManager: React.FC<MiniGameManagerProps> = ({
  activeDll,
  onClose,
  gameState,
  onStateChange,
}) => {
  if (!activeDll) return null;

  const renderMiniGame = () => {
    switch (activeDll.toLowerCase()) {
      case 'euro32.dll':
        return <EuroCalculator onClose={onClose} />;

      case 'inv.dll':
        return (
          <Inventory
            items={gameState.inventory}
            onClose={onClose}
            onUseItem={(item) => {
              // Logique d'utilisation d'objet
            }}
          />
        );

      case 'pepe.dll':
        return <PepeGame onClose={onClose} onScore={(s) => {
          onStateChange({ ...gameState, score: gameState.score + s });
        }} />;

      // Autres mini-jeux...

      default:
        console.warn(`DLL non implémentée: ${activeDll}`);
        return null;
    }
  };

  return (
    <div className="mini-game-overlay">
      {renderMiniGame()}
    </div>
  );
};
```

---

## 10. Conversion des assets

### Script de conversion BMP → PNG

```bash
#!/bin/bash
# convert_assets.sh

# Convertir tous les BMP en PNG avec gestion de la transparence magenta
find . -name "*.bmp" -type f | while read file; do
    output="${file%.bmp}.png"
    # Convertir et remplacer magenta (#FF00FF) par transparent
    convert "$file" -transparent "#FF00FF" "$output"
    echo "Converti: $file -> $output"
done
```

### Structure des assets pour React

```
public/
└── assets/
    ├── france/
    │   ├── img24/
    │   │   ├── paris2.png
    │   │   ├── roll/
    │   │   │   ├── ticket.png
    │   │   │   └── ...
    │   ├── movie/
    │   │   └── *.mp4
    │   └── digit/
    │       └── *.mp3
    ├── allemagne/
    │   └── ...
    └── barre/
        └── images/
            ├── barre.png
            ├── calc1.png
            └── ...
```

---

## 11. Checklist d'implémentation

### Phase 1 : Infrastructure
- [ ] Types TypeScript complets
- [ ] ConditionEvaluator
- [ ] ActionExecutor
- [ ] GameState management (Context/Redux)

### Phase 2 : Composants de base
- [ ] Scene renderer
- [ ] Hotspot component
- [ ] Toolbar component
- [ ] TextDisplay component
- [ ] VideoPlayer component

### Phase 3 : Parser et données
- [ ] Parser VND → JSON
- [ ] Convertir assets (BMP→PNG, AVI→MP4, WAV→MP3)
- [ ] Structurer les fichiers JSON par pays

### Phase 4 : Mini-jeux
- [x] Calculatrice Euro (fait!)
- [ ] Inventaire
- [ ] Mini-jeux spécifiques

### Phase 5 : Polish
- [ ] Transitions entre scènes
- [ ] Gestion audio complète
- [ ] Sauvegarde/chargement
- [ ] Responsive design

---

*Guide d'implémentation React pour Europeo*
*Version 1.0 - Janvier 2025*
