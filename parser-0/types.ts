
export interface SceneFile {
  slot: number;
  filename: string;
  param: number;
  offset: number;
}

export interface InitCommand {
  id: number;
  subtype?: number; // Stocke le sous-type pour l'affichage (ex: 27 = Overlay)
  param: string;
  offset: number; 
  isRecovered?: boolean; // Si trouvé par le Gap Scanner
}

export interface InitScript {
  offset: number;
  length: number;
  commands: InitCommand[];
  rawHex?: string; 
}

export interface SceneConfig {
  offset: number;
  flag: number;
  ints: number[];
  foundSignature: boolean;
}

export interface HotspotCommand {
  id: number;
  subtype: number;
  param: string;
}

export interface HotspotGeometry {
  cursorId: number;
  pointCount: number;
  points: { x: number; y: number }[];
  extraFlag: number;
}

export interface Hotspot {
  index: number;
  offset: number;
  commands: HotspotCommand[];
  geometry: HotspotGeometry;
  isRecovered?: boolean;
}

export interface ParsedScene {
  id: number;
  offset: number;
  length: number;
  files: SceneFile[];
  initScript: InitScript;
  config: SceneConfig;
  hotspots: Hotspot[];
  warnings: string[];
  parseMethod: 'signature' | 'heuristic' | 'heuristic_recovered' | 'fallback';
}

export interface ParseResult {
  scenes: ParsedScene[];
  logs: string[];
  totalBytes: number;
}
