/**
 * Game State Store using Zustand
 * Manages all game variables, current scene, and game progress
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { GameState, Condition } from '../types/game';

// Initial game variables (from VND analysis)
const INITIAL_VARIABLES: Record<string, number> = {
  // Core game state
  SCORE: 0,
  SACADOS: 0,
  CALC: 0,
  TELEPHONE: 0,
  ACTIVE: 0,
  TRANS: 0,
  FIOLE: 0,

  // Country flags
  ALLEMAGNE: 0,
  FRANCE: 0,
  ANGLETERRE: 0,
  AUTRICHE: 0,
  BELGIQUE: 0,
  DANEMARK: 0,
  ECOSSE: 0,
  ESPAGNE: 0,
  FINLANDE: 0,
  GRECE: 0,
  PAYSBAS: 0,
  IRLANDE: 0,
  ITALIE: 0,
  PORTUGAL: 0,
  SUEDE: 0,
  EUROLAND: 0,
};

interface GameStore extends GameState {
  // Actions
  setVariable: (name: string, value: number) => void;
  incrementVariable: (name: string, amount: number) => void;
  decrementVariable: (name: string, amount: number) => void;
  getVariable: (name: string) => number;

  // Scene navigation
  setScene: (sceneId: number) => void;
  setCountry: (countryId: string) => void;
  navigateTo: (countryId: string, sceneId: number) => void;

  // Score
  addScore: (points: number) => void;
  setScore: (score: number) => void;

  // Inventory
  addToInventory: (item: string) => void;
  removeFromInventory: (item: string) => void;
  hasItem: (item: string) => boolean;

  // Condition evaluation
  evaluateCondition: (condition: Condition) => boolean;

  // Game control
  startGame: () => void;
  resetGame: () => void;
  toggleToolbar: () => void;

  // Mark country as visited
  visitCountry: (countryId: string) => void;
}

export const useGameStore = create<GameStore>()(
  persist(
    (set, get) => ({
      // Initial state
      currentCountry: 'frontal',
      currentScene: 1,
      variables: { ...INITIAL_VARIABLES },
      score: 0,
      inventory: [],
      visitedCountries: [],
      isPlaying: false,
      showToolbar: true,

      // Variable operations
      setVariable: (name, value) =>
        set((state) => ({
          variables: { ...state.variables, [name.toUpperCase()]: value },
        })),

      incrementVariable: (name, amount) =>
        set((state) => ({
          variables: {
            ...state.variables,
            [name.toUpperCase()]: (state.variables[name.toUpperCase()] || 0) + amount,
          },
        })),

      decrementVariable: (name, amount) =>
        set((state) => ({
          variables: {
            ...state.variables,
            [name.toUpperCase()]: (state.variables[name.toUpperCase()] || 0) - amount,
          },
        })),

      getVariable: (name) => get().variables[name.toUpperCase()] || 0,

      // Scene navigation
      setScene: (sceneId) => set({ currentScene: sceneId }),

      setCountry: (countryId) =>
        set((state) => {
          // Mark as visited
          const visited = state.visitedCountries.includes(countryId)
            ? state.visitedCountries
            : [...state.visitedCountries, countryId];
          return { currentCountry: countryId, visitedCountries: visited };
        }),

      navigateTo: (countryId, sceneId) =>
        set((state) => {
          const visited = state.visitedCountries.includes(countryId)
            ? state.visitedCountries
            : [...state.visitedCountries, countryId];
          return {
            currentCountry: countryId,
            currentScene: sceneId,
            visitedCountries: visited,
          };
        }),

      // Score operations
      addScore: (points) =>
        set((state) => {
          const newScore = state.score + points;
          return {
            score: newScore,
            variables: { ...state.variables, SCORE: newScore },
          };
        }),

      setScore: (score) =>
        set((state) => ({
          score,
          variables: { ...state.variables, SCORE: score },
        })),

      // Inventory
      addToInventory: (item) =>
        set((state) => ({
          inventory: state.inventory.includes(item)
            ? state.inventory
            : [...state.inventory, item],
        })),

      removeFromInventory: (item) =>
        set((state) => ({
          inventory: state.inventory.filter((i) => i !== item),
        })),

      hasItem: (item) => get().inventory.includes(item),

      // Condition evaluation
      evaluateCondition: (condition) => {
        const value = get().getVariable(condition.variable);
        switch (condition.operator) {
          case '=':
            return value === condition.value;
          case '!=':
            return value !== condition.value;
          case '<':
            return value < condition.value;
          case '>':
            return value > condition.value;
          case '<=':
            return value <= condition.value;
          case '>=':
            return value >= condition.value;
          default:
            return false;
        }
      },

      // Game control
      startGame: () => set({ isPlaying: true }),

      resetGame: () =>
        set({
          currentCountry: 'frontal',
          currentScene: 1,
          variables: { ...INITIAL_VARIABLES },
          score: 0,
          inventory: [],
          visitedCountries: [],
          isPlaying: false,
          showToolbar: true,
        }),

      toggleToolbar: () => set((state) => ({ showToolbar: !state.showToolbar })),

      visitCountry: (countryId) =>
        set((state) => ({
          visitedCountries: state.visitedCountries.includes(countryId)
            ? state.visitedCountries
            : [...state.visitedCountries, countryId],
        })),
    }),
    {
      name: 'europeo-game-state',
      partialize: (state) => ({
        score: state.score,
        inventory: state.inventory,
        visitedCountries: state.visitedCountries,
        variables: state.variables,
        currentCountry: state.currentCountry,
        currentScene: state.currentScene,
      }),
    }
  )
);
