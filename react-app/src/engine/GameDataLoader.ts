/**
 * Game Data Loader
 * Loads and parses game data from JSON and VND files
 */

import type { Scene, Hotspot, Command, Country, Condition } from '../types/game';

// Type for raw JSON data from extract_all.py
interface RawGameData {
  metadata: {
    title: string;
    developer: string;
    format_version: string;
    resolution: { width: number; height: number };
  };
  countries: Record<string, RawCountryData>;
  special_modules: Record<string, { vnd: RawVndData }>;
  global_variables: string[];
}

interface RawCountryData {
  id: string;
  name: string;
  name_en: string;
  vnd: RawVndData | null;
  vnp: Record<string, string> | null;
  assets: {
    images: string[];
    audio: string[];
    videos: string[];
    html: string[];
  };
}

interface RawVndData {
  file: string;
  path: string;
  variables: string[];
  scenes: number[];
  resources: {
    images: string[];
    audio: string[];
    videos: string[];
    html: string[];
    cursors: string[];
  };
  commands: RawCommand[];
  navigation: { target: string; scene: number }[];
  hotspots: { x1: number; y1: number; x2: number; y2: number }[];
}

interface RawCommand {
  type: string;
  variable: string;
  operator: string;
  value: number;
  action: string;
}

// Cache for loaded game data
let cachedGameData: RawGameData | null = null;

/**
 * Load game data JSON
 */
export async function loadGameData(): Promise<RawGameData> {
  if (cachedGameData) {
    return cachedGameData;
  }

  try {
    const response = await fetch('/data/game_data.json');
    if (!response.ok) {
      throw new Error(`Failed to load game data: ${response.status}`);
    }
    cachedGameData = await response.json();
    return cachedGameData!;
  } catch (error) {
    console.error('Error loading game data:', error);
    throw error;
  }
}

/**
 * Convert raw command to Command object
 */
function convertRawCommand(raw: RawCommand): Command {
  const condition: Condition = {
    variable: raw.variable,
    operator: raw.operator as Condition['operator'],
    value: raw.value,
  };

  return {
    type: raw.type as Command['type'],
    condition,
    params: [raw.action],
  };
}

// Export for potential use
export { convertRawCommand };

/**
 * Build scenes from raw VND data
 */
export function buildScenesFromVnd(vnd: RawVndData, _countryId: string): Scene[] {
  const scenes: Scene[] = [];

  // Get unique scene IDs
  const sceneIds = vnd.scenes.length > 0 ? vnd.scenes : [1];

  for (const sceneId of sceneIds) {
    // Find background for this scene (use first image as default)
    const background = vnd.resources.images[0] || undefined;

    // Build hotspots from coordinates
    const hotspots: Hotspot[] = vnd.hotspots.slice(0, 10).map((coords, index) => ({
      id: index + 1,
      rect: coords,
      tooltip: `Zone ${index + 1}`,
      onClick: [],
      onEnter: [],
      onLeave: [],
    }));

    // Build commands
    const onEnterCommands: Command[] = [];
    const onExitCommands: Command[] = [];

    // Add audio command if available
    if (vnd.resources.audio.length > 0) {
      onEnterCommands.push({
        type: 'playwav',
        params: [vnd.resources.audio[0], '2'], // Loop
      });
    }

    scenes.push({
      id: sceneId,
      name: `Scene ${sceneId}`,
      background,
      hotspots,
      onEnter: onEnterCommands,
      onExit: onExitCommands,
    });
  }

  return scenes;
}

/**
 * Load country data
 */
export async function loadCountry(countryId: string): Promise<Country | null> {
  const gameData = await loadGameData();

  const rawCountry = gameData.countries[countryId];
  if (!rawCountry) {
    console.warn(`Country not found: ${countryId}`);
    return null;
  }

  const scenes = rawCountry.vnd ? buildScenesFromVnd(rawCountry.vnd, countryId) : [];

  return {
    id: rawCountry.id,
    name: rawCountry.name,
    nameEn: rawCountry.name_en,
    scenes,
    assets: rawCountry.assets,
  };
}

/**
 * Get list of available countries
 */
export async function getCountryList(): Promise<{ id: string; name: string }[]> {
  const gameData = await loadGameData();

  return Object.values(gameData.countries).map((country) => ({
    id: country.id,
    name: country.name,
  }));
}

/**
 * Get global variables
 */
export async function getGlobalVariables(): Promise<string[]> {
  const gameData = await loadGameData();
  return gameData.global_variables;
}

/**
 * Asset path builder
 */
export function getAssetPath(
  countryId: string,
  filename: string,
  type: 'img' | 'audio' | 'video' | 'html' = 'img'
): string {
  // Remove any path prefix from filename
  const cleanFilename = filename.replace(/^.*[\\\/]/, '');

  // Convert BMP to PNG for images
  const finalFilename = type === 'img' && cleanFilename.endsWith('.bmp')
    ? cleanFilename.replace('.bmp', '.png')
    : cleanFilename;

  const basePath = `/assets/${countryId}`;

  switch (type) {
    case 'img':
      return `${basePath}/img24/${finalFilename}`;
    case 'audio':
      return `${basePath}/digit/${finalFilename}`;
    case 'video':
      return `${basePath}/movie/${finalFilename}`;
    case 'html':
      return `${basePath}/html/${finalFilename}`;
    default:
      return `${basePath}/${finalFilename}`;
  }
}
