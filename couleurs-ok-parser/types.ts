
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

// Structure tooltip (info-bulle avec rectangle + texte)
export interface TooltipInfo {
  type: number;
  rect: { x1: number; y1: number; x2: number; y2: number };
  flag: number;
  text: string;
}

export interface Hotspot {
  index: number;
  offset: number;
  commands: HotspotCommand[];
  geometry: HotspotGeometry;
  isRecovered?: boolean;
  isTooltip?: boolean;
  tooltip?: TooltipInfo;
  recoveredCmd?: string; // Information auxiliaire pour le debug ou l'affichage
}

// Type de scène (pour distinguer les meta-scènes des vraies scènes de jeu)
export type SceneType =
  | 'game'           // Vraie scène de jeu
  | 'global_vars'    // Scène 0 avec variables globales/ressources
  | 'toolbar'        // Barre d'outils persistante
  | 'options'        // Options/DLL système
  | 'credits'        // Écran de crédits
  | 'game_over'      // Écran de fin (perdu/gagné)
  | 'empty'          // Slot vide (Empty)
  | 'unknown';       // Type non déterminé

export interface ParsedScene {
  id: number;
  offset: number;
  length: number;
  files: SceneFile[];
  initScript: InitScript;
  config: SceneConfig;
  hotspots: Hotspot[];
  warnings: string[];
  parseMethod: 'signature' | 'heuristic' | 'heuristic_recovered' | 'fallback' | 'empty_slot';
  sceneType: SceneType;  // Nouveau: type de scène détecté
  sceneName?: string;    // Titre de la scène (ex: "Le bureau du banquier")
}

export interface ParseResult {
  scenes: ParsedScene[];
  logs: string[];
  totalBytes: number;
}
