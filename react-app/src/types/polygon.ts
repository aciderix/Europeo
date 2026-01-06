/**
 * Types pour les hotspots avec polygones
 * Basé sur le reverse engineering du format VND
 */

/** Point 2D */
export interface Point {
  x: number;
  y: number;
}

/** Bounding box */
export interface BBox {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

/** Zone cliquable (polygone ou rectangle) */
export interface ClickableArea {
  type: 'polygon' | 'rectangle';
  points?: Array<[number, number]>; // Tuples [x, y] depuis le JSON
  bbox: BBox;
  center: Point;
}

/** Hotspot avec polygone (nouveau format) */
export interface PolygonHotspot {
  id: number;
  text: string;
  text_position: Point;
  layer: number;
  clickable_area?: ClickableArea;
  video?: string;
  goto_scene?: number;
}

/** Scène avec hotspots polygones */
export interface PolygonScene {
  id: number;
  background: string;
  audio?: string;
  hotspots: PolygonHotspot[];
}

/** Données d'un pays */
export interface CountryData {
  name: string;
  folder: string;
  file: string;
  scenes: PolygonScene[];
}

/** Données complètes du jeu */
export interface GameDataPolygons {
  game: string;
  version: string;
  resolution: { width: number; height: number };
  countries: Record<string, CountryData>;
}
