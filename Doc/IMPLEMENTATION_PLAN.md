# Plan d'Implémentation - Europeo React Port

> **Règles strictes** :
> - ✅ 0 Mocks - Toutes les implémentations sont fonctionnelles
> - ✅ 0 Placeholders - Code complet requis
> - ✅ 0 Simulations - Intégrations réelles
> - ✅ 0 TODOs - Pas de "// TODO: implement later"
> - ✅ 0 "En prod il faudrait" - Tout est production-ready dès le départ

---

## État Actuel

### ✅ Fait
- [x] Reverse engineering format VND (polygones découverts)
- [x] Parser Python `vnd_polygon_parser.py`
- [x] Données extraites `game_data_polygons.json`
- [x] Documentation `VND_FORMAT.md`
- [x] Structure React de base (`react-app/`)
- [x] Types TypeScript (`types/game.ts`)
- [x] Composant Hotspot basique (rectangles uniquement)
- [x] GameDataLoader (ancien format)

### ❌ À Faire
- [ ] **Phase 1** : Intégrer les données polygones
- [ ] **Phase 2** : Composant Hotspot avec polygones
- [ ] **Phase 3** : Système de scènes complet
- [ ] **Phase 4** : Images rollover
- [ ] **Phase 5** : Système de variables/conditions
- [ ] **Phase 6** : Lecture vidéo/audio
- [ ] **Phase 7** : Inventaire et barre d'outils
- [ ] **Phase 8** : Navigation inter-pays

---

## Phase 1 : Intégrer les Données Polygones

### 1.1 Copier game_data_polygons.json
```bash
cp Doc/game_data_polygons.json react-app/public/assets/
```

### 1.2 Nouveaux Types TypeScript

**Fichier** : `react-app/src/types/polygon.ts`

```typescript
/**
 * Types pour les hotspots avec polygones
 * Basé sur le reverse engineering du format VND
 */

// Point 2D
export interface Point {
  x: number;
  y: number;
}

// Bounding box
export interface BBox {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

// Zone cliquable (polygone ou rectangle)
export interface ClickableArea {
  type: 'polygon' | 'rectangle';
  points?: Point[];  // Pour polygone
  bbox: BBox;
  center: Point;
}

// Hotspot avec polygone (nouveau format)
export interface PolygonHotspot {
  id: number;
  text: string;
  text_position: Point;
  layer: number;
  clickable_area?: ClickableArea;
  video?: string;
  goto_scene?: number;
}

// Scène avec hotspots polygones
export interface PolygonScene {
  id: number;
  background: string;
  audio?: string;
  hotspots: PolygonHotspot[];
}

// Données d'un pays
export interface CountryData {
  name: string;
  folder: string;
  file: string;
  scenes: PolygonScene[];
}

// Données complètes du jeu
export interface GameDataPolygons {
  game: string;
  version: string;
  resolution: { width: number; height: number };
  countries: Record<string, CountryData>;
}
```

### 1.3 Nouveau GameDataLoader

**Fichier** : `react-app/src/engine/PolygonDataLoader.ts`

```typescript
/**
 * Chargeur de données avec support des polygones
 */

import type { GameDataPolygons, CountryData, PolygonScene } from '../types/polygon';

let cachedData: GameDataPolygons | null = null;

/**
 * Charge les données du jeu (avec polygones)
 */
export async function loadPolygonGameData(): Promise<GameDataPolygons> {
  if (cachedData) {
    return cachedData;
  }

  const response = await fetch('/assets/game_data_polygons.json');
  if (!response.ok) {
    throw new Error(`Échec chargement: ${response.status} ${response.statusText}`);
  }

  cachedData = await response.json();
  return cachedData;
}

/**
 * Récupère les données d'un pays
 */
export async function getCountryData(countryId: string): Promise<CountryData | null> {
  const data = await loadPolygonGameData();
  return data.countries[countryId] || null;
}

/**
 * Récupère une scène spécifique
 */
export async function getScene(countryId: string, sceneId: number): Promise<PolygonScene | null> {
  const country = await getCountryData(countryId);
  if (!country) return null;

  return country.scenes.find(s => s.id === sceneId) || null;
}

/**
 * Liste des pays disponibles
 */
export async function getCountryList(): Promise<Array<{ id: string; name: string }>> {
  const data = await loadPolygonGameData();

  return Object.entries(data.countries).map(([id, country]) => ({
    id,
    name: country.name,
  }));
}

/**
 * Construit le chemin vers un asset
 */
export function getAssetPath(
  countryId: string,
  filename: string,
  type: 'image' | 'video' | 'audio' = 'image'
): string {
  // Nettoyer le nom de fichier (enlever les chemins Windows)
  const cleanName = filename.replace(/^.*[\\\/]/, '').toLowerCase();

  // Convertir BMP en PNG
  const finalName = cleanName.endsWith('.bmp')
    ? cleanName.replace('.bmp', '.png')
    : cleanName;

  const basePath = `/assets/${countryId}`;

  switch (type) {
    case 'image':
      return `${basePath}/img24/${finalName}`;
    case 'video':
      return `${basePath}/movie/${finalName.replace('.avi', '.mp4')}`;
    case 'audio':
      return `${basePath}/digit/${finalName.replace('.wav', '.mp3')}`;
    default:
      return `${basePath}/${finalName}`;
  }
}
```

### 1.4 Statut Phase 1
- [ ] Types créés
- [ ] Loader créé
- [ ] JSON copié
- [ ] Tests passent

---

## Phase 2 : Composant Hotspot avec Polygones

### 2.1 Algorithme Point-in-Polygon

**Fichier** : `react-app/src/utils/geometry.ts`

```typescript
/**
 * Utilitaires géométriques pour la détection de clics
 */

import type { Point, ClickableArea, BBox } from '../types/polygon';

/**
 * Test si un point est dans un polygone (Ray-casting algorithm)
 * https://en.wikipedia.org/wiki/Point_in_polygon
 */
export function isPointInPolygon(point: Point, polygon: Point[]): boolean {
  if (polygon.length < 3) return false;

  let inside = false;
  const n = polygon.length;

  for (let i = 0, j = n - 1; i < n; j = i++) {
    const xi = polygon[i].x;
    const yi = polygon[i].y;
    const xj = polygon[j].x;
    const yj = polygon[j].y;

    const intersect = ((yi > point.y) !== (yj > point.y)) &&
      (point.x < (xj - xi) * (point.y - yi) / (yj - yi) + xi);

    if (intersect) {
      inside = !inside;
    }
  }

  return inside;
}

/**
 * Test si un point est dans un rectangle
 */
export function isPointInRect(point: Point, bbox: BBox): boolean {
  return point.x >= bbox.x1 &&
         point.x <= bbox.x2 &&
         point.y >= bbox.y1 &&
         point.y <= bbox.y2;
}

/**
 * Test si un point est dans une zone cliquable (polygone ou rectangle)
 */
export function isPointInClickableArea(point: Point, area: ClickableArea): boolean {
  // Vérification rapide avec la bounding box
  if (!isPointInRect(point, area.bbox)) {
    return false;
  }

  // Si c'est un polygone, faire le test précis
  if (area.type === 'polygon' && area.points && area.points.length >= 3) {
    return isPointInPolygon(point, area.points);
  }

  // Sinon c'est un rectangle, le test bbox suffit
  return true;
}

/**
 * Convertit un tableau de tuples en tableau de Points
 */
export function tuplesToPoints(tuples: Array<[number, number]>): Point[] {
  return tuples.map(([x, y]) => ({ x, y }));
}

/**
 * Génère un path SVG pour un polygone
 */
export function polygonToSvgPath(points: Point[]): string {
  if (points.length < 3) return '';

  const [first, ...rest] = points;
  const pathParts = [`M ${first.x} ${first.y}`];

  for (const point of rest) {
    pathParts.push(`L ${point.x} ${point.y}`);
  }

  pathParts.push('Z');
  return pathParts.join(' ');
}
```

### 2.2 Composant PolygonHotspot

**Fichier** : `react-app/src/components/Game/PolygonHotspot.tsx`

```tsx
/**
 * Composant Hotspot avec support des polygones
 */

import React, { useState, useCallback, useMemo } from 'react';
import type { PolygonHotspot as HotspotType, Point } from '../../types/polygon';
import { polygonToSvgPath, tuplesToPoints } from '../../utils/geometry';

interface PolygonHotspotProps {
  hotspot: HotspotType;
  scale: number;
  onHover: (hotspot: HotspotType | null) => void;
  onClick: (hotspot: HotspotType) => void;
  debug?: boolean;
}

export const PolygonHotspot: React.FC<PolygonHotspotProps> = ({
  hotspot,
  scale,
  onHover,
  onClick,
  debug = false,
}) => {
  const [isHovered, setIsHovered] = useState(false);

  const handleMouseEnter = useCallback(() => {
    setIsHovered(true);
    onHover(hotspot);
  }, [hotspot, onHover]);

  const handleMouseLeave = useCallback(() => {
    setIsHovered(false);
    onHover(null);
  }, [onHover]);

  const handleClick = useCallback(() => {
    onClick(hotspot);
  }, [hotspot, onClick]);

  // Pas de zone cliquable = pas de rendu
  if (!hotspot.clickable_area) {
    return null;
  }

  const area = hotspot.clickable_area;
  const { bbox } = area;

  // Calcul des dimensions
  const width = (bbox.x2 - bbox.x1) * scale;
  const height = (bbox.y2 - bbox.y1) * scale;
  const left = bbox.x1 * scale;
  const top = bbox.y1 * scale;

  // Convertir les points du polygone (ils sont stockés comme tuples)
  const points: Point[] = useMemo(() => {
    if (area.type === 'polygon' && area.points) {
      // Les points peuvent être des tuples [x, y] ou des objets {x, y}
      return area.points.map((p: any) => {
        if (Array.isArray(p)) {
          return { x: p[0], y: p[1] };
        }
        return p as Point;
      });
    }
    return [];
  }, [area]);

  // Générer le path SVG pour le polygone (relatif à la bbox)
  const svgPath = useMemo(() => {
    if (points.length < 3) return '';

    // Décaler les points pour qu'ils soient relatifs à la bbox
    const relativePoints = points.map(p => ({
      x: (p.x - bbox.x1) * scale,
      y: (p.y - bbox.y1) * scale,
    }));

    return polygonToSvgPath(relativePoints);
  }, [points, bbox, scale]);

  // Style du conteneur
  const containerStyle: React.CSSProperties = {
    position: 'absolute',
    left,
    top,
    width,
    height,
    cursor: 'pointer',
    pointerEvents: 'none', // Le SVG gère les événements
  };

  // Si pas de polygone, utiliser un rectangle simple
  if (area.type !== 'polygon' || points.length < 3) {
    return (
      <div
        style={{
          ...containerStyle,
          pointerEvents: 'auto',
          backgroundColor: debug
            ? (isHovered ? 'rgba(255, 255, 0, 0.3)' : 'rgba(255, 255, 255, 0.1)')
            : 'transparent',
          border: debug ? '1px solid rgba(255, 255, 255, 0.5)' : 'none',
        }}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        onClick={handleClick}
        role="button"
        tabIndex={0}
        aria-label={hotspot.text}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') handleClick();
        }}
      />
    );
  }

  // Rendu avec SVG pour le polygone
  return (
    <div style={containerStyle}>
      <svg
        width={width}
        height={height}
        style={{ position: 'absolute', top: 0, left: 0 }}
      >
        <path
          d={svgPath}
          fill={debug
            ? (isHovered ? 'rgba(255, 255, 0, 0.3)' : 'rgba(0, 255, 0, 0.1)')
            : 'transparent'
          }
          stroke={debug ? (isHovered ? '#ffff00' : '#00ff00') : 'transparent'}
          strokeWidth={debug ? 2 : 0}
          style={{ cursor: 'pointer', pointerEvents: 'auto' }}
          onMouseEnter={handleMouseEnter}
          onMouseLeave={handleMouseLeave}
          onClick={handleClick}
        />
      </svg>

      {/* Label en mode debug */}
      {debug && isHovered && (
        <div
          style={{
            position: 'absolute',
            left: '50%',
            top: '50%',
            transform: 'translate(-50%, -50%)',
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            color: '#fff',
            padding: '4px 8px',
            borderRadius: 4,
            fontSize: 12,
            whiteSpace: 'nowrap',
            pointerEvents: 'none',
          }}
        >
          {hotspot.text}
        </div>
      )}
    </div>
  );
};

export default PolygonHotspot;
```

### 2.3 Statut Phase 2
- [ ] geometry.ts créé
- [ ] PolygonHotspot.tsx créé
- [ ] Tests polygones passent
- [ ] Rendu SVG fonctionne

---

## Phase 3 : Système de Scènes Complet

### 3.1 Composant Scene avec Polygones

**Fichier** : `react-app/src/components/Game/PolygonScene.tsx`

```tsx
/**
 * Composant Scène avec hotspots polygones
 */

import React, { useState, useCallback, useEffect } from 'react';
import type { PolygonScene as SceneType, PolygonHotspot as HotspotType } from '../../types/polygon';
import { PolygonHotspot } from './PolygonHotspot';
import { getAssetPath } from '../../engine/PolygonDataLoader';

interface PolygonSceneProps {
  scene: SceneType;
  countryId: string;
  scale: number;
  debug?: boolean;
  onHotspotClick: (hotspot: HotspotType) => void;
}

export const PolygonScene: React.FC<PolygonSceneProps> = ({
  scene,
  countryId,
  scale,
  debug = false,
  onHotspotClick,
}) => {
  const [hoveredHotspot, setHoveredHotspot] = useState<HotspotType | null>(null);
  const [backgroundLoaded, setBackgroundLoaded] = useState(false);
  const [backgroundError, setBackgroundError] = useState(false);

  // Chemin de l'image de fond
  const backgroundPath = getAssetPath(countryId, scene.background, 'image');

  // Reset état au changement de scène
  useEffect(() => {
    setBackgroundLoaded(false);
    setBackgroundError(false);
    setHoveredHotspot(null);
  }, [scene.id, countryId]);

  const handleBackgroundLoad = useCallback(() => {
    setBackgroundLoaded(true);
  }, []);

  const handleBackgroundError = useCallback(() => {
    setBackgroundError(true);
    console.error(`Erreur chargement: ${backgroundPath}`);
  }, [backgroundPath]);

  const handleHover = useCallback((hotspot: HotspotType | null) => {
    setHoveredHotspot(hotspot);
  }, []);

  // Dimensions du jeu
  const gameWidth = 640 * scale;
  const gameHeight = 480 * scale;

  return (
    <div
      className="polygon-scene"
      style={{
        position: 'relative',
        width: gameWidth,
        height: gameHeight,
        backgroundColor: '#000',
        overflow: 'hidden',
      }}
    >
      {/* Image de fond */}
      {!backgroundError ? (
        <img
          src={backgroundPath}
          alt={`Scene ${scene.id}`}
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: gameWidth,
            height: gameHeight,
            objectFit: 'cover',
            opacity: backgroundLoaded ? 1 : 0,
            transition: 'opacity 0.3s ease',
          }}
          onLoad={handleBackgroundLoad}
          onError={handleBackgroundError}
        />
      ) : (
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: gameWidth,
            height: gameHeight,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#666',
            fontSize: 14,
          }}
        >
          Image non trouvée: {scene.background}
        </div>
      )}

      {/* Hotspots */}
      {scene.hotspots.map((hotspot) => (
        <PolygonHotspot
          key={hotspot.id}
          hotspot={hotspot}
          scale={scale}
          onHover={handleHover}
          onClick={onHotspotClick}
          debug={debug}
        />
      ))}

      {/* Tooltip du hotspot survolé */}
      {hoveredHotspot && (
        <div
          style={{
            position: 'absolute',
            left: hoveredHotspot.text_position.x * scale,
            top: hoveredHotspot.text_position.y * scale,
            backgroundColor: 'rgba(0, 0, 0, 0.85)',
            color: '#fff',
            padding: '6px 12px',
            borderRadius: 4,
            fontSize: 14 * scale,
            fontFamily: 'Comic Sans MS, cursive',
            pointerEvents: 'none',
            zIndex: 100,
            maxWidth: 200 * scale,
            textAlign: 'center',
            boxShadow: '2px 2px 8px rgba(0,0,0,0.5)',
          }}
        >
          {hoveredHotspot.text}
        </div>
      )}

      {/* Infos debug */}
      {debug && (
        <div
          style={{
            position: 'absolute',
            bottom: 8,
            left: 8,
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            color: '#0f0',
            padding: '4px 8px',
            fontSize: 11,
            fontFamily: 'monospace',
            borderRadius: 4,
            zIndex: 100,
          }}
        >
          Scene {scene.id} | {scene.hotspots.length} hotspots |{' '}
          {scene.hotspots.filter(h => h.clickable_area).length} avec polygones
        </div>
      )}
    </div>
  );
};

export default PolygonScene;
```

### 3.2 Statut Phase 3
- [ ] PolygonScene.tsx créé
- [ ] Chargement images fonctionne
- [ ] Tooltips fonctionnent
- [ ] Mode debug fonctionne

---

## Phase 4 : Images Rollover

### 4.1 Extraire les Rollover du VND

Mettre à jour le parser Python pour extraire les commandes `addbmp`.

**À ajouter dans** `vnd_polygon_parser.py` :

```python
def find_rollover_images(self) -> List[Dict]:
    """Trouve toutes les images rollover (addbmp)"""
    rollovers = []
    pattern = r'addbmp\s+(\w+)\s+([\w\\/.]+\.bmp)\s+(\d+)\s+(\d+)\s+(\d+)'

    for match in re.finditer(pattern, self.text_content, re.IGNORECASE):
        rollovers.append({
            'name': match.group(1),
            'image': match.group(2),
            'layer': int(match.group(3)),
            'x': int(match.group(4)),
            'y': int(match.group(5)),
            'offset': match.start()
        })

    return rollovers
```

### 4.2 Statut Phase 4
- [ ] Parser mis à jour
- [ ] Données rollover extraites
- [ ] Composant Rollover créé
- [ ] Intégré à PolygonScene

---

## Phase 5 : Système de Variables/Conditions

### 5.1 Store de Variables

**Fichier** : `react-app/src/store/gameStore.ts`

```typescript
/**
 * Store global du jeu (Zustand)
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface GameStore {
  // Position actuelle
  currentCountry: string;
  currentScene: number;

  // Variables du jeu
  variables: Record<string, number>;

  // Score
  score: number;

  // Inventaire
  inventory: string[];

  // Actions
  setScene: (countryId: string, sceneId: number) => void;
  setVariable: (name: string, value: number) => void;
  incrementVariable: (name: string, amount?: number) => void;
  decrementVariable: (name: string, amount?: number) => void;
  addToInventory: (item: string) => void;
  removeFromInventory: (item: string) => void;
  addScore: (points: number) => void;
  resetGame: () => void;
}

const initialState = {
  currentCountry: 'couleurs1',
  currentScene: 1,
  variables: {},
  score: 0,
  inventory: [],
};

export const useGameStore = create<GameStore>()(
  persist(
    (set) => ({
      ...initialState,

      setScene: (countryId, sceneId) => set({
        currentCountry: countryId,
        currentScene: sceneId,
      }),

      setVariable: (name, value) => set((state) => ({
        variables: { ...state.variables, [name]: value },
      })),

      incrementVariable: (name, amount = 1) => set((state) => ({
        variables: {
          ...state.variables,
          [name]: (state.variables[name] || 0) + amount,
        },
      })),

      decrementVariable: (name, amount = 1) => set((state) => ({
        variables: {
          ...state.variables,
          [name]: (state.variables[name] || 0) - amount,
        },
      })),

      addToInventory: (item) => set((state) => ({
        inventory: state.inventory.includes(item)
          ? state.inventory
          : [...state.inventory, item],
      })),

      removeFromInventory: (item) => set((state) => ({
        inventory: state.inventory.filter((i) => i !== item),
      })),

      addScore: (points) => set((state) => ({
        score: state.score + points,
      })),

      resetGame: () => set(initialState),
    }),
    {
      name: 'europeo-game-state',
    }
  )
);

/**
 * Évalue une condition
 */
export function evaluateCondition(
  variable: string,
  operator: string,
  value: number,
  variables: Record<string, number>
): boolean {
  const currentValue = variables[variable] || 0;

  switch (operator) {
    case '=':
    case '==':
      return currentValue === value;
    case '!=':
    case '<>':
      return currentValue !== value;
    case '<':
      return currentValue < value;
    case '>':
      return currentValue > value;
    case '<=':
      return currentValue <= value;
    case '>=':
      return currentValue >= value;
    default:
      console.warn(`Opérateur inconnu: ${operator}`);
      return false;
  }
}
```

### 5.2 Statut Phase 5
- [ ] gameStore créé
- [ ] Persistence localStorage
- [ ] evaluateCondition fonctionne
- [ ] Intégré aux hotspots

---

## Phase 6 : Lecture Vidéo/Audio

### 6.1 Composant VideoPlayer

**Fichier** : `react-app/src/components/Media/VideoPlayer.tsx`

```tsx
/**
 * Lecteur vidéo pour les animations du jeu
 */

import React, { useRef, useEffect, useCallback } from 'react';

interface VideoPlayerProps {
  src: string;
  onEnded: () => void;
  onError: (error: string) => void;
  style?: React.CSSProperties;
}

export const VideoPlayer: React.FC<VideoPlayerProps> = ({
  src,
  onEnded,
  onError,
  style,
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    video.play().catch((err) => {
      console.error('Erreur lecture vidéo:', err);
      onError(err.message);
    });
  }, [src, onError]);

  const handleEnded = useCallback(() => {
    onEnded();
  }, [onEnded]);

  const handleError = useCallback(() => {
    onError(`Impossible de lire: ${src}`);
  }, [src, onError]);

  return (
    <video
      ref={videoRef}
      src={src}
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        objectFit: 'contain',
        backgroundColor: '#000',
        ...style,
      }}
      onEnded={handleEnded}
      onError={handleError}
      playsInline
      muted={false}
    />
  );
};

export default VideoPlayer;
```

### 6.2 Hook useAudio

**Fichier** : `react-app/src/hooks/useAudio.ts`

```typescript
/**
 * Hook pour la gestion audio
 */

import { useRef, useCallback, useEffect } from 'react';

interface UseAudioOptions {
  loop?: boolean;
  volume?: number;
}

export function useAudio(options: UseAudioOptions = {}) {
  const { loop = false, volume = 1 } = options;
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const play = useCallback((src: string) => {
    // Arrêter l'audio précédent
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }

    const audio = new Audio(src);
    audio.loop = loop;
    audio.volume = volume;
    audioRef.current = audio;

    audio.play().catch((err) => {
      console.warn('Erreur lecture audio:', err);
    });
  }, [loop, volume]);

  const stop = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      audioRef.current = null;
    }
  }, []);

  const pause = useCallback(() => {
    audioRef.current?.pause();
  }, []);

  const resume = useCallback(() => {
    audioRef.current?.play();
  }, []);

  // Cleanup au démontage
  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);

  return { play, stop, pause, resume };
}
```

### 6.3 Statut Phase 6
- [ ] VideoPlayer créé
- [ ] useAudio créé
- [ ] Conversion AVI → MP4 faite
- [ ] Conversion WAV → MP3 faite

---

## Phase 7 : Inventaire et Barre d'Outils

### 7.1 Composant Toolbar

**Fichier** : `react-app/src/components/UI/GameToolbar.tsx`

```tsx
/**
 * Barre d'outils du jeu (80px en bas)
 */

import React from 'react';
import { useGameStore } from '../../store/gameStore';

interface GameToolbarProps {
  scale: number;
  onItemClick: (item: string) => void;
}

// Items de la toolbar avec leurs positions
const TOOLBAR_ITEMS = [
  { id: 'active', x: 163, image: 'trans.bmp' },
  { id: 'calc', x: 246, image: 'calc1.bmp' },
  { id: 'telep', x: 316, image: 'telep.bmp' },
  { id: 'sac', x: 384, image: 'sac.bmp' },
  { id: 'info', x: 452, image: 'p_euroland.bmp' },
];

export const GameToolbar: React.FC<GameToolbarProps> = ({ scale, onItemClick }) => {
  const { score, inventory } = useGameStore();

  const toolbarHeight = 80 * scale;

  return (
    <div
      className="game-toolbar"
      style={{
        position: 'absolute',
        bottom: 0,
        left: 0,
        width: 640 * scale,
        height: toolbarHeight,
        backgroundColor: '#333',
        display: 'flex',
        alignItems: 'center',
        padding: `0 ${10 * scale}px`,
        boxSizing: 'border-box',
      }}
    >
      {/* Score */}
      <div
        style={{
          color: '#fff',
          fontFamily: 'Comic Sans MS, cursive',
          fontSize: 16 * scale,
          marginRight: 20 * scale,
        }}
      >
        Score: {score}
      </div>

      {/* Items toolbar */}
      <div style={{ display: 'flex', gap: 8 * scale }}>
        {TOOLBAR_ITEMS.map((item) => (
          <button
            key={item.id}
            onClick={() => onItemClick(item.id)}
            style={{
              width: 48 * scale,
              height: 48 * scale,
              border: inventory.includes(item.id) ? '2px solid #ff0' : '1px solid #666',
              borderRadius: 4,
              backgroundColor: '#222',
              cursor: 'pointer',
              opacity: inventory.includes(item.id) ? 1 : 0.5,
            }}
            title={item.id}
          >
            {/* Image de l'item */}
            <img
              src={`/assets/barre/images/${item.image.replace('.bmp', '.png')}`}
              alt={item.id}
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'contain',
              }}
              onError={(e) => {
                (e.target as HTMLImageElement).style.display = 'none';
              }}
            />
          </button>
        ))}
      </div>

      {/* Inventaire */}
      <div
        style={{
          marginLeft: 'auto',
          display: 'flex',
          gap: 4 * scale,
        }}
      >
        {inventory.slice(0, 5).map((item) => (
          <div
            key={item}
            style={{
              width: 32 * scale,
              height: 32 * scale,
              backgroundColor: '#444',
              borderRadius: 4,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff',
              fontSize: 10 * scale,
            }}
          >
            {item.slice(0, 3)}
          </div>
        ))}
      </div>
    </div>
  );
};

export default GameToolbar;
```

### 7.2 Statut Phase 7
- [ ] GameToolbar créé
- [ ] Images toolbar converties
- [ ] Inventaire fonctionne
- [ ] Score affiché

---

## Phase 8 : Navigation Inter-Pays

### 8.1 GameContainer Principal

**Fichier** : `react-app/src/components/Game/GameContainer.tsx` (mise à jour)

```tsx
/**
 * Conteneur principal du jeu
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useGameStore } from '../../store/gameStore';
import { getScene, getAssetPath } from '../../engine/PolygonDataLoader';
import { PolygonScene } from './PolygonScene';
import { GameToolbar } from '../UI/GameToolbar';
import { VideoPlayer } from '../Media/VideoPlayer';
import { useAudio } from '../../hooks/useAudio';
import type { PolygonScene as SceneType, PolygonHotspot } from '../../types/polygon';

interface GameContainerProps {
  initialCountry?: string;
  initialScene?: number;
  debug?: boolean;
}

export const GameContainer: React.FC<GameContainerProps> = ({
  initialCountry = 'couleurs1',
  initialScene = 1,
  debug = false,
}) => {
  const { currentCountry, currentScene, setScene, variables } = useGameStore();
  const [scene, setSceneData] = useState<SceneType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentVideo, setCurrentVideo] = useState<string | null>(null);

  const { play: playAudio, stop: stopAudio } = useAudio({ loop: true });

  // Calculer l'échelle
  const scale = Math.min(
    window.innerWidth / 640,
    window.innerHeight / 480
  );

  // Charger la scène
  useEffect(() => {
    let mounted = true;

    async function loadScene() {
      setLoading(true);
      setError(null);

      try {
        const sceneData = await getScene(currentCountry, currentScene);
        if (!mounted) return;

        if (sceneData) {
          setSceneData(sceneData);

          // Jouer l'audio de la scène
          if (sceneData.audio) {
            playAudio(getAssetPath(currentCountry, sceneData.audio, 'audio'));
          } else {
            stopAudio();
          }
        } else {
          setError(`Scène ${currentScene} non trouvée dans ${currentCountry}`);
        }
      } catch (err) {
        if (!mounted) return;
        setError(err instanceof Error ? err.message : 'Erreur de chargement');
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    loadScene();

    return () => {
      mounted = false;
    };
  }, [currentCountry, currentScene, playAudio, stopAudio]);

  // Initialisation
  useEffect(() => {
    setScene(initialCountry, initialScene);
  }, [initialCountry, initialScene, setScene]);

  // Gestion des clics sur hotspot
  const handleHotspotClick = useCallback((hotspot: PolygonHotspot) => {
    // Si vidéo associée, la jouer
    if (hotspot.video) {
      const videoPath = getAssetPath(currentCountry, hotspot.video, 'video');
      setCurrentVideo(videoPath);
      return;
    }

    // Si navigation vers une autre scène
    if (hotspot.goto_scene) {
      setScene(currentCountry, hotspot.goto_scene);
    }
  }, [currentCountry, setScene]);

  // Fin de vidéo
  const handleVideoEnded = useCallback(() => {
    setCurrentVideo(null);
  }, []);

  // Erreur vidéo
  const handleVideoError = useCallback((error: string) => {
    console.error('Erreur vidéo:', error);
    setCurrentVideo(null);
  }, []);

  // Clic sur item toolbar
  const handleToolbarItemClick = useCallback((item: string) => {
    console.log('Toolbar item clicked:', item);
    // Implémenter les actions des items
  }, []);

  if (loading) {
    return (
      <div
        style={{
          width: 640 * scale,
          height: 480 * scale,
          backgroundColor: '#000',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#fff',
        }}
      >
        Chargement...
      </div>
    );
  }

  if (error) {
    return (
      <div
        style={{
          width: 640 * scale,
          height: 480 * scale,
          backgroundColor: '#300',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#fff',
          padding: 20,
          textAlign: 'center',
        }}
      >
        Erreur: {error}
      </div>
    );
  }

  return (
    <div
      className="game-container"
      style={{
        position: 'relative',
        width: 640 * scale,
        height: 480 * scale,
        margin: '0 auto',
        backgroundColor: '#000',
      }}
    >
      {/* Scène */}
      {scene && (
        <PolygonScene
          scene={scene}
          countryId={currentCountry}
          scale={scale}
          debug={debug}
          onHotspotClick={handleHotspotClick}
        />
      )}

      {/* Barre d'outils */}
      <GameToolbar scale={scale} onItemClick={handleToolbarItemClick} />

      {/* Lecteur vidéo (overlay) */}
      {currentVideo && (
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            zIndex: 200,
          }}
        >
          <VideoPlayer
            src={currentVideo}
            onEnded={handleVideoEnded}
            onError={handleVideoError}
          />
        </div>
      )}
    </div>
  );
};

export default GameContainer;
```

### 8.2 Statut Phase 8
- [ ] GameContainer mis à jour
- [ ] Navigation fonctionne
- [ ] Vidéos jouent
- [ ] Audio joue

---

## Scripts de Conversion d'Assets

### Conversion BMP → PNG
```bash
#!/bin/bash
# convert_images.sh

find . -name "*.bmp" -type f | while read file; do
  output="${file%.bmp}.png"
  if [ ! -f "$output" ]; then
    convert "$file" "$output"
    echo "Converti: $file → $output"
  fi
done
```

### Conversion AVI → MP4
```bash
#!/bin/bash
# convert_videos.sh

find . -name "*.avi" -type f | while read file; do
  output="${file%.avi}.mp4"
  if [ ! -f "$output" ]; then
    ffmpeg -i "$file" -c:v libx264 -crf 23 -preset medium -c:a aac -b:a 128k "$output"
    echo "Converti: $file → $output"
  fi
done
```

### Conversion WAV → MP3
```bash
#!/bin/bash
# convert_audio.sh

find . -name "*.wav" -type f | while read file; do
  output="${file%.wav}.mp3"
  if [ ! -f "$output" ]; then
    ffmpeg -i "$file" -codec:a libmp3lame -qscale:a 2 "$output"
    echo "Converti: $file → $output"
  fi
done
```

---

## Checklist Finale

- [ ] Phase 1 complète
- [ ] Phase 2 complète
- [ ] Phase 3 complète
- [ ] Phase 4 complète
- [ ] Phase 5 complète
- [ ] Phase 6 complète
- [ ] Phase 7 complète
- [ ] Phase 8 complète
- [ ] Assets convertis
- [ ] Tests manuels OK
- [ ] Build production OK

---

## Commandes Utiles

```bash
# Développement
cd react-app && npm run dev

# Build production
cd react-app && npm run build

# Copier les assets
cp -r couleurs1/img24 react-app/public/assets/couleurs1/

# Lancer le parser
python3 tools/vnd_polygon_parser.py
```

---

*Document créé le 2025-01-06*
*Dernière mise à jour : 2025-01-06*
