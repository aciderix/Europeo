/**
 * Type definitions for Europeo Visual Novel Engine
 */

// Game coordinates (original 640x480 resolution)
export interface Rect {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

// Conditional expression
export interface Condition {
  variable: string;
  operator: '=' | '!=' | '<' | '>' | '<=' | '>=';
  value: number;
}

// Command types from VND DSL
export type CommandType =
  | 'scene'
  | 'runprj'
  | 'hotspot'
  | 'playavi'
  | 'playwav'
  | 'playtext'
  | 'playhtml'
  | 'addbmp'
  | 'delbmp'
  | 'toolbar'
  | 'defcursor'
  | 'rundll'
  | 'closedll'
  | 'closewav'
  | 'set_var'
  | 'inc_var'
  | 'dec_var'
  | 'score';

// A command that can be executed
export interface Command {
  type: CommandType;
  condition?: Condition;
  elseAction?: Command;
  params: string[];
}

// Hotspot (clickable area)
export interface Hotspot {
  id: number;
  rect: Rect;
  cursor?: string;
  onEnter?: Command[];
  onClick?: Command[];
  onLeave?: Command[];
  tooltip?: string;
}

// Scene definition
export interface Scene {
  id: number;
  name?: string;
  background?: string;
  audio?: string;
  toolbar?: boolean;
  hotspots: Hotspot[];
  onEnter: Command[];
  onExit: Command[];
}

// Country/Module data
export interface Country {
  id: string;
  name: string;
  nameEn: string;
  scenes: Scene[];
  assets: {
    images: string[];
    audio: string[];
    videos: string[];
    html: string[];
  };
}

// Game state
export interface GameState {
  // Current position
  currentCountry: string;
  currentScene: number;

  // Variables
  variables: Record<string, number>;

  // Score
  score: number;

  // Inventory (objects collected)
  inventory: string[];

  // Countries visited
  visitedCountries: string[];

  // UI state
  isPlaying: boolean;
  showToolbar: boolean;
}

// Resource paths configuration
export interface ResourceConfig {
  basePath: string;
  imagePath: string;
  audioPath: string;
  videoPath: string;
  htmlPath: string;
}

// Media player state
export interface MediaState {
  currentVideo?: string;
  currentAudio?: string;
  isVideoPlaying: boolean;
  isAudioPlaying: boolean;
  audioLoop: boolean;
}

// Game metadata
export interface GameMetadata {
  title: string;
  developer: string;
  resolution: { width: number; height: number };
  countries: string[];
}
