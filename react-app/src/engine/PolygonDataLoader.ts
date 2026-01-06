/**
 * Chargeur de données avec support des polygones
 * Charge et parse les données du jeu depuis game_data_polygons.json
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

  const data: GameDataPolygons = await response.json();
  cachedData = data;
  return data;
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
 * Récupère la première scène d'un pays (scène de départ)
 */
export async function getFirstScene(countryId: string): Promise<PolygonScene | null> {
  const country = await getCountryData(countryId);
  if (!country || country.scenes.length === 0) return null;

  return country.scenes[0];
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
 * Récupère la résolution du jeu
 */
export async function getGameResolution(): Promise<{ width: number; height: number }> {
  const data = await loadPolygonGameData();
  return data.resolution;
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

  // Convertir les extensions pour le web
  let finalName = cleanName;

  switch (type) {
    case 'image':
      // BMP → PNG
      if (finalName.endsWith('.bmp')) {
        finalName = finalName.replace('.bmp', '.png');
      }
      return `/assets/${countryId}/img24/${finalName}`;

    case 'video':
      // AVI → MP4
      if (finalName.endsWith('.avi')) {
        finalName = finalName.replace('.avi', '.mp4');
      }
      return `/assets/${countryId}/movie/${finalName}`;

    case 'audio':
      // WAV → MP3
      if (finalName.endsWith('.wav')) {
        finalName = finalName.replace('.wav', '.mp3');
      }
      return `/assets/${countryId}/digit/${finalName}`;

    default:
      return `/assets/${countryId}/${finalName}`;
  }
}

/**
 * Vérifie si un asset existe (via HEAD request)
 */
export async function assetExists(path: string): Promise<boolean> {
  try {
    const response = await fetch(path, { method: 'HEAD' });
    return response.ok;
  } catch {
    return false;
  }
}
