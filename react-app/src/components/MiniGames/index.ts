/**
 * Mini-Games Index
 * Exports all faithfully ported mini-games from original DLLs
 */

// Currency conversion game - from francs.dll
// Question: "Combien font 100 francs français en euros ?" → 15,24
export { FrancsGame } from './FrancsGame';

// Tour Eiffel steps game - from pepe.dll
// Question: "Combien de marches pour monter au dernier étage ?" → 1665
export { TourEiffelGame } from './TourEiffelGame';

// Math problem game - from probleme.dll
// Question: "2000 BEF - 48000 ITL = ? EUR" → 25
export { ProblemeGame } from './ProblemeGame';

// Memory card matching game - from Memory.dll
// 4x4 grid = 8 pairs, with timer
export { MemoryGame } from './MemoryGame';

// Wheel of fortune game - from roue.dll
// 9 sectors, jackpot = 1000 points
export { RoueGame } from './RoueGame';

// Legacy game (can be removed later)
export { JustePrix } from './JustePrix';

// Mini-game types for the game engine
export type MiniGameType =
  | 'francs'      // francs.dll
  | 'pepe'        // pepe.dll (Tour Eiffel)
  | 'probleme'    // probleme.dll
  | 'memory'      // Memory.dll
  | 'roue'        // roue.dll
  | 'justeprix';  // Generic price guessing

// Map DLL names to mini-game types
export const DLL_TO_MINIGAME: Record<string, MiniGameType> = {
  'francs.dll': 'francs',
  'pepe.dll': 'pepe',
  'probleme.dll': 'probleme',
  'Memory.dll': 'memory',
  'roue.dll': 'roue',
};
