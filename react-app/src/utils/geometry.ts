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
 * Convertit un tableau de tuples [x,y] en tableau de Points {x, y}
 */
export function tuplesToPoints(tuples: Array<[number, number]>): Point[] {
  return tuples.map(([x, y]) => ({ x, y }));
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
    const points = tuplesToPoints(area.points);
    return isPointInPolygon(point, points);
  }

  // Sinon c'est un rectangle, le test bbox suffit
  return true;
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

/**
 * Calcule le centre d'un polygone
 */
export function getPolygonCenter(points: Point[]): Point {
  if (points.length === 0) return { x: 0, y: 0 };

  const sum = points.reduce(
    (acc, p) => ({ x: acc.x + p.x, y: acc.y + p.y }),
    { x: 0, y: 0 }
  );

  return {
    x: Math.round(sum.x / points.length),
    y: Math.round(sum.y / points.length),
  };
}

/**
 * Calcule la bounding box d'un polygone
 */
export function getPolygonBBox(points: Point[]): BBox {
  if (points.length === 0) {
    return { x1: 0, y1: 0, x2: 0, y2: 0 };
  }

  const xs = points.map(p => p.x);
  const ys = points.map(p => p.y);

  return {
    x1: Math.min(...xs),
    y1: Math.min(...ys),
    x2: Math.max(...xs),
    y2: Math.max(...ys),
  };
}
