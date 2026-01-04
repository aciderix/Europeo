/**
 * Command Interpreter for VND DSL
 * Parses and executes Visual Novel commands
 */

import type { Command, Condition, CommandType } from '../types/game';
import { useGameStore } from '../store/gameStore';

// Parse a condition string like "score = 0" or "guitare != 1"
export function parseCondition(conditionStr: string): Condition | null {
  const match = conditionStr.match(/^(\w+)\s*(=|!=|<|>|<=|>=)\s*(\d+)$/);
  if (!match) return null;

  return {
    variable: match[1],
    operator: match[2] as Condition['operator'],
    value: parseInt(match[3], 10),
  };
}

// Parse a command string from VND
export function parseCommand(commandStr: string): Command | null {
  const trimmed = commandStr.trim();
  if (!trimmed) return null;

  // Check for conditional command
  const thenMatch = trimmed.match(/^(.+?)\s+then\s+(.+?)(?:\s+else\s+(.+))?$/i);
  if (thenMatch) {
    const condition = parseCondition(thenMatch[1].trim());
    if (!condition) return null;

    const thenCommand = parseCommand(thenMatch[2].trim());
    const elseCommand = thenMatch[3] ? parseCommand(thenMatch[3].trim()) : undefined;

    if (thenCommand) {
      return {
        ...thenCommand,
        condition,
        elseAction: elseCommand || undefined,
      };
    }
    return null;
  }

  // Parse non-conditional command
  const parts = trimmed.split(/\s+/);
  const type = parts[0]?.toLowerCase() as CommandType;

  return {
    type,
    params: parts.slice(1),
  };
}

// Command executor class
export class CommandExecutor {
  private mediaCallbacks: {
    playVideo?: (src: string, rect?: { x: number; y: number; w: number; h: number }) => void;
    playAudio?: (src: string, loop: boolean) => void;
    stopAudio?: () => void;
    showHtml?: (src: string, rect?: { x: number; y: number; w: number; h: number }) => void;
    showText?: (text: string, x: number, y: number) => void;
    addImage?: (id: string, src: string, x: number, y: number) => void;
    removeImage?: (id: string) => void;
    setCursor?: (cursor: string) => void;
  } = {};

  setMediaCallbacks(callbacks: typeof this.mediaCallbacks) {
    this.mediaCallbacks = callbacks;
  }

  execute(command: Command): boolean {
    const store = useGameStore.getState();

    // Check condition if present
    if (command.condition) {
      const conditionMet = store.evaluateCondition(command.condition);
      if (!conditionMet) {
        // Execute else action if present
        if (command.elseAction) {
          return this.execute(command.elseAction);
        }
        return false;
      }
    }

    // Execute command
    switch (command.type) {
      case 'scene':
        return this.executeScene(command.params);

      case 'runprj':
        return this.executeRunProject(command.params);

      case 'set_var':
        return this.executeSetVar(command.params);

      case 'inc_var':
        return this.executeIncVar(command.params);

      case 'dec_var':
        return this.executeDecVar(command.params);

      case 'score':
        return this.executeScore(command.params);

      case 'playavi':
        return this.executePlayAvi(command.params);

      case 'playwav':
        return this.executePlayWav(command.params);

      case 'playtext':
        return this.executePlayText(command.params);

      case 'playhtml':
        return this.executePlayHtml(command.params);

      case 'addbmp':
        return this.executeAddBmp(command.params);

      case 'delbmp':
        return this.executeDelBmp(command.params);

      case 'defcursor':
        return this.executeDefCursor(command.params);

      case 'closewav':
        this.mediaCallbacks.stopAudio?.();
        return true;

      case 'hotspot':
        // Hotspot activation is handled by the scene
        return true;

      default:
        console.warn(`Unknown command type: ${command.type}`);
        return false;
    }
  }

  private executeScene(params: string[]): boolean {
    const sceneId = parseInt(params[0], 10);
    if (isNaN(sceneId)) return false;

    useGameStore.getState().setScene(sceneId);
    return true;
  }

  private executeRunProject(params: string[]): boolean {
    if (params.length < 2) return false;

    // Parse project path: ..\france\france.vnp 18
    const projectPath = params[0];
    const sceneId = parseInt(params[1], 10);

    // Extract country from path
    const match = projectPath.match(/[\\/](\w+)[\\/]\w+\.vnp$/i);
    if (match) {
      const countryId = match[1].toLowerCase();
      useGameStore.getState().navigateTo(countryId, sceneId);
      return true;
    }

    return false;
  }

  private executeSetVar(params: string[]): boolean {
    if (params.length < 2) return false;
    const [name, valueStr] = params;
    const value = parseInt(valueStr, 10);
    if (isNaN(value)) return false;

    useGameStore.getState().setVariable(name, value);
    return true;
  }

  private executeIncVar(params: string[]): boolean {
    if (params.length < 2) return false;
    const [name, amountStr] = params;
    const amount = parseInt(amountStr, 10);
    if (isNaN(amount)) return false;

    useGameStore.getState().incrementVariable(name, amount);
    return true;
  }

  private executeDecVar(params: string[]): boolean {
    if (params.length < 2) return false;
    const [name, amountStr] = params;
    const amount = parseInt(amountStr, 10);
    if (isNaN(amount)) return false;

    useGameStore.getState().decrementVariable(name, amount);
    return true;
  }

  private executeScore(params: string[]): boolean {
    if (params.length < 1) return false;
    const points = parseInt(params[0], 10);
    if (isNaN(points)) return false;

    useGameStore.getState().addScore(points);
    return true;
  }

  private executePlayAvi(params: string[]): boolean {
    if (params.length < 1) return false;
    const [src, , x, y, x2, y2] = params;

    const rect = x && y && x2 && y2
      ? {
          x: parseInt(x, 10),
          y: parseInt(y, 10),
          w: parseInt(x2, 10) - parseInt(x, 10),
          h: parseInt(y2, 10) - parseInt(y, 10),
        }
      : undefined;

    this.mediaCallbacks.playVideo?.(src, rect);
    return true;
  }

  private executePlayWav(params: string[]): boolean {
    if (params.length < 1) return false;
    const [src, modeStr] = params;
    const loop = modeStr === '2';

    this.mediaCallbacks.playAudio?.(src, loop);
    return true;
  }

  private executePlayText(params: string[]): boolean {
    // playtext x y w h flags text
    if (params.length < 6) return false;
    const x = parseInt(params[0], 10);
    const y = parseInt(params[1], 10);
    const text = params.slice(5).join(' ');

    this.mediaCallbacks.showText?.(text, x, y);
    return true;
  }

  private executePlayHtml(params: string[]): boolean {
    if (params.length < 1) return false;
    const [src, , x, y, w, h] = params;

    const rect = x && y && w && h
      ? {
          x: parseInt(x, 10),
          y: parseInt(y, 10),
          w: parseInt(w, 10),
          h: parseInt(h, 10),
        }
      : undefined;

    this.mediaCallbacks.showHtml?.(src, rect);
    return true;
  }

  private executeAddBmp(params: string[]): boolean {
    // addbmp id path flags x y
    if (params.length < 5) return false;
    const [id, path, , x, y] = params;

    this.mediaCallbacks.addImage?.(id, path, parseInt(x, 10), parseInt(y, 10));
    return true;
  }

  private executeDelBmp(params: string[]): boolean {
    if (params.length < 1) return false;
    this.mediaCallbacks.removeImage?.(params[0]);
    return true;
  }

  private executeDefCursor(params: string[]): boolean {
    if (params.length < 1) return false;
    this.mediaCallbacks.setCursor?.(params[0]);
    return true;
  }
}

// Singleton instance
export const commandExecutor = new CommandExecutor();
