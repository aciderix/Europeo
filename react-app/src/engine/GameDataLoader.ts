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

interface RawSceneData {
  id: number;
  background?: string;
  audio?: string;
  commands?: RawCommand[];
}

interface RawHotspotData {
  id: string;
  image: string;
  x: number;
  y: number;
  layer: number;
  actions?: Array<{
    condition_value: number;
    action: RawCommand;
  }>;
}

interface RawVndData {
  file: string;
  path: string;
  variables: string[];
  scenes: RawSceneData[];
  resources: {
    images: string[];
    audio: string[];
    videos: string[];
    html: string[];
    cursors?: string[];
  };
  commands: RawCommand[];
  navigation: { target: string; scene: number }[];
  hotspots: RawHotspotData[];
}

interface RawCommand {
  type: string;
  // For conditional commands
  variable?: string;
  operator?: string;
  value?: number;
  action?: string;
  // For media commands
  file?: string;
  mode?: number;
  rect?: { x: number; y: number; w: number; h: number };
  // For addbmp
  id?: string;
  flags?: number;
  x?: number;
  y?: number;
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
    const response = await fetch('/assets/game_data.json');
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
 * Convert raw conditional command to Command object
 */
function convertRawCommand(raw: RawCommand): Command | null {
  if (raw.type !== 'conditional' || !raw.variable || !raw.operator || raw.value === undefined) {
    return null;
  }

  const condition: Condition = {
    variable: raw.variable,
    operator: raw.operator as Condition['operator'],
    value: raw.value,
  };

  return {
    type: 'scene' as Command['type'], // Most conditional commands lead to scene changes
    condition,
    params: raw.action ? [raw.action] : [],
  };
}

// Export for potential use
export { convertRawCommand };

/**
 * Convert BMP filename to PNG
 */
function bmpToPng(filename: string): string {
  return filename.toLowerCase().endsWith('.bmp')
    ? filename.slice(0, -4) + '.png'
    : filename;
}

/**
 * Convert raw command to game Command
 */
function rawToCommand(raw: RawCommand): Command | null {
  switch (raw.type) {
    case 'playwav':
      return {
        type: 'playwav',
        params: [raw.file || '', String(raw.mode || 1)],
      };
    case 'playavi':
      return {
        type: 'playavi',
        params: [
          raw.file || '',
          String(raw.mode || 1),
          String(raw.rect?.x || 0),
          String(raw.rect?.y || 0),
          String((raw.rect?.x || 0) + (raw.rect?.w || 100)),
          String((raw.rect?.y || 0) + (raw.rect?.h || 100)),
        ],
      };
    case 'playhtml':
      return {
        type: 'playhtml',
        params: [
          raw.file || '',
          String(raw.mode || 1),
          String(raw.rect?.x || 50),
          String(raw.rect?.y || 50),
          String(raw.rect?.w || 500),
          String(raw.rect?.h || 350),
        ],
      };
    case 'addbmp':
      return {
        type: 'addbmp',
        params: [raw.id || '', raw.file || '', String(raw.flags || 0), String(raw.x || 0), String(raw.y || 0)],
      };
    default:
      return null;
  }
}

/**
 * Build scenes from raw VND data (new format with scene objects)
 */
export function buildScenesFromVnd(vnd: RawVndData, _countryId: string): Scene[] {
  const scenes: Scene[] = [];

  // Build hotspots from new format (with id, image, x, y, actions)
  const buildHotspots = (): Hotspot[] => {
    return vnd.hotspots.slice(0, 15).map((h, index) => {
      // Build onClick commands from hotspot actions
      const onClick: Command[] = [];
      if (h.actions) {
        for (const action of h.actions.slice(0, 3)) {
          const cmd = rawToCommand(action.action);
          if (cmd) onClick.push(cmd);
        }
      }

      // Calculate rect from position (hotspot size ~50x50 by default)
      const rect = { x1: h.x, y1: h.y, x2: h.x + 50, y2: h.y + 50 };

      return {
        id: index + 1,
        rect,
        cursor: undefined,
        tooltip: h.id,
        onClick,
        onEnter: [],
        onLeave: [],
      };
    });
  };

  const hotspots = buildHotspots();

  // Process each scene from the new format
  for (const rawScene of vnd.scenes) {
    const onEnterCommands: Command[] = [];

    // Add audio command if scene has audio
    if (rawScene.audio) {
      onEnterCommands.push({
        type: 'playwav',
        params: [rawScene.audio, '2'], // Loop audio
      });
    }

    // Add scene commands
    if (rawScene.commands) {
      for (const cmd of rawScene.commands.slice(0, 5)) {
        const converted = rawToCommand(cmd);
        if (converted) onEnterCommands.push(converted);
      }
    }

    scenes.push({
      id: rawScene.id,
      name: `Scene ${rawScene.id}`,
      background: rawScene.background ? bmpToPng(rawScene.background) : undefined,
      hotspots, // Same hotspots for all scenes (simplification)
      onEnter: onEnterCommands,
      onExit: [],
    });
  }

  // Fallback if no scenes
  if (scenes.length === 0) {
    scenes.push({
      id: 1,
      name: 'Scene 1',
      background: vnd.resources.images[0] ? bmpToPng(vnd.resources.images[0]) : undefined,
      hotspots,
      onEnter: [],
      onExit: [],
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
