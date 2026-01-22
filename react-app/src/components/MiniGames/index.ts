/**
 * Mini-Games Index
 * Exports all faithfully ported mini-games from original DLLs
 */

// Currency conversion game - from francs.dll
// Question: "Combien font 100 francs français en euros ?" → 15,24
export { FrancsGame } from './FrancsGame';

// Tour Eiffel steps game - from pepe.dll
// Question: "Combien de marches pour monter au dernier étage ?" → 1652
export { TourEiffelGame } from './TourEiffelGame';

// Math problem game - from probleme.dll
// Question: "2000 BEF - 48000 ITL = ? EUR" → 26
export { ProblemeGame } from './ProblemeGame';

// Memory card matching game - from Memory.dll
// 4x4 grid = 8 pairs, with timer
export { MemoryGame } from './MemoryGame';

// Combination lock game - from roue.dll (NOT a wheel!)
// 4-digit combination lock, solution: 2002 (year of Euro)
export { CoffreGame } from './CoffreGame';

// Legacy RoueGame - DEPRECATED, use CoffreGame instead
// The original roue.dll was NOT a wheel but a combination lock
export { RoueGame } from './RoueGame';

// Frog memory game - from frog.dll
// Simon Says with frogs - repeat the sequence
export { FrogGame } from './FrogGame';

// Bateau drag & drop game - from bateau.dll
// Match cultural objects to European countries
export { BateauGame } from './BateauGame';

// Costume dress-up game - from costume.dll
// Dress 3 mannequins with matching outfits
export { CostumeGame } from './CostumeGame';

// Legacy game (can be removed later)
export { JustePrix } from './JustePrix';

// Mini-game types for the game engine
export type MiniGameType =
  | 'francs'      // francs.dll
  | 'pepe'        // pepe.dll (Tour Eiffel)
  | 'probleme'    // probleme.dll
  | 'memory'      // Memory.dll
  | 'coffre'      // roue.dll (combination lock)
  | 'roue'        // DEPRECATED - redirects to coffre
  | 'frog'        // frog.dll (Simon Says)
  | 'bateau'      // bateau.dll (Drag & Drop)
  | 'costume'     // costume.dll (Dress-up)
  | 'justeprix';  // Generic price guessing

// Map DLL names to mini-game types
export const DLL_TO_MINIGAME: Record<string, MiniGameType> = {
  'francs.dll': 'francs',
  'pepe.dll': 'pepe',
  'probleme.dll': 'probleme',
  'Memory.dll': 'memory',
  'roue.dll': 'coffre',  // Correct mapping - roue.dll is the combination lock
  'frog.dll': 'frog',
  'bateau.dll': 'bateau',
  'costume.dll': 'costume',
};
