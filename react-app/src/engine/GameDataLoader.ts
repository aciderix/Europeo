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
 * Build scenes from raw VND data
 */
export function buildScenesFromVnd(vnd: RawVndData, _countryId: string): Scene[] {
  const scenes: Scene[] = [];

  // Get unique scene IDs
  const sceneIds = vnd.scenes.length > 0 ? vnd.scenes : [1];

  // Group commands by type for scene building
  const addbmpCommands = vnd.commands.filter((c) => c.type === 'addbmp');
  const playwavCommands = vnd.commands.filter((c) => c.type === 'playwav');

  for (let i = 0; i < sceneIds.length; i++) {
    const sceneId = sceneIds[i];

    // Find background for this scene
    // Use scene index to pick different backgrounds if available
    const bgIndex = i % Math.max(1, vnd.resources.images.length);
    const rawBackground = vnd.resources.images[bgIndex];
    const background = rawBackground ? bmpToPng(rawBackground) : undefined;

    // Build hotspots from coordinates with improved actions
    const hotspots: Hotspot[] = vnd.hotspots.slice(0, 10).map((coords, index) => {
      // Try to find a playavi command that might be for this hotspot (by position)
      const hotspotRect = { x1: coords.x1, y1: coords.y1, x2: coords.x2, y2: coords.y2 };
      const matchingAvi = vnd.commands.find(
        (c) =>
          c.type === 'playavi' &&
          c.rect &&
          Math.abs((c.rect.x || 0) - hotspotRect.x1) < 50 &&
          Math.abs((c.rect.y || 0) - hotspotRect.y1) < 50
      );

      const onClick: Command[] = [];
      if (matchingAvi) {
        const cmd = rawToCommand(matchingAvi);
        if (cmd) onClick.push(cmd);
      }

      return {
        id: index + 1,
        rect: coords,
        tooltip: matchingAvi ? `🎬 ${matchingAvi.file}` : `Zone ${index + 1}`,
        onClick,
        onEnter: [],
        onLeave: [],
      };
    });

    // Build scene enter commands
    const onEnterCommands: Command[] = [];
    const onExitCommands: Command[] = [];

    // Add background images from addbmp commands
    for (const addbmp of addbmpCommands.slice(0, 3)) {
      const cmd = rawToCommand(addbmp);
      if (cmd) onEnterCommands.push(cmd);
    }

    // Add audio command if available (use playwav from commands or resources)
    const loopAudio = playwavCommands.find((c) => c.mode === 2);
    if (loopAudio) {
      onEnterCommands.push({
        type: 'playwav',
        params: [loopAudio.file || '', '2'],
      });
    } else if (vnd.resources.audio.length > 0) {
      onEnterCommands.push({
        type: 'playwav',
        params: [vnd.resources.audio[0], '2'],
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
