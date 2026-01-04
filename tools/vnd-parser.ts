/**
 * VND Parser - Visual Novel Data file parser for Europeo
 * Format: VNFILE 2.13 by Sopra Multimedia
 */

interface VNDHeader {
  magic: string;
  version: string;
  application: string;
  developer: string;
  id: string;
  registryPath: string;
  width: number;
  height: number;
  resourceDll: string;
}

interface VNDVariable {
  name: string;
  value: number;
}

interface VNDHotspot {
  id: number;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  commands: VNDCommand[];
}

interface VNDCommand {
  type: string;
  condition?: string;
  params: string[];
  raw: string;
}

interface VNDScene {
  id: number;
  name: string;
  background?: string;
  backgroundPath?: string;
  htmlFile?: string;
  audio?: string;
  toolbar?: string;
  hotspots: VNDHotspot[];
  onEnterCommands: VNDCommand[];
  onExitCommands: VNDCommand[];
}

interface VNDProject {
  header: VNDHeader;
  variables: VNDVariable[];
  scenes: VNDScene[];
}

class VNDParser {
  private buffer: Buffer;
  private offset: number = 0;

  constructor(buffer: Buffer) {
    this.buffer = buffer;
  }

  private readUInt32LE(): number {
    const value = this.buffer.readUInt32LE(this.offset);
    this.offset += 4;
    return value;
  }

  private readUInt16LE(): number {
    const value = this.buffer.readUInt16LE(this.offset);
    this.offset += 2;
    return value;
  }

  private readByte(): number {
    return this.buffer[this.offset++];
  }

  private readString(): string {
    const length = this.readUInt32LE();
    if (length === 0 || length > 10000) return '';
    const str = this.buffer.toString('latin1', this.offset, this.offset + length);
    this.offset += length;
    return str;
  }

  private readPrefixedString(): string {
    const length = this.readUInt32LE();
    if (length === 0 || length > 10000) return '';
    const str = this.buffer.toString('latin1', this.offset, this.offset + length);
    this.offset += length;
    return str;
  }

  private skipBytes(count: number): void {
    this.offset += count;
  }

  private peekByte(): number {
    return this.buffer[this.offset];
  }

  private hasMoreData(): boolean {
    return this.offset < this.buffer.length;
  }

  parse(): VNDProject {
    // Skip initial flags
    this.skipBytes(5);

    // Read header strings
    const magic = this.readPrefixedString();
    this.skipBytes(4); // Skip padding/unknown
    const version = this.readPrefixedString();
    this.skipBytes(4);
    const application = this.readPrefixedString();
    const developer = this.readPrefixedString();
    const id = this.readPrefixedString();
    const registryPath = this.readPrefixedString();

    // Read dimensions (at offset ~0x78)
    const width = this.readUInt16LE();
    this.skipBytes(2);
    const height = this.readUInt16LE();
    this.skipBytes(10); // Skip unknown bytes

    // Read resource DLL path
    const resourceDll = this.readPrefixedString();

    const header: VNDHeader = {
      magic,
      version,
      application,
      developer,
      id,
      registryPath,
      width,
      height,
      resourceDll
    };

    // Read variables count
    const variableCount = this.readUInt32LE();
    const variables: VNDVariable[] = [];

    for (let i = 0; i < variableCount && i < 500; i++) {
      const name = this.readPrefixedString();
      const value = this.readUInt32LE();
      if (name) {
        variables.push({ name, value });
      }
    }

    // Scenes will be parsed from the text representation
    // This is a simplified parser - full binary parsing would require more reverse engineering
    const scenes: VNDScene[] = [];

    return {
      header,
      variables,
      scenes
    };
  }
}

/**
 * Parse VND command string into structured command
 */
function parseCommand(raw: string): VNDCommand {
  raw = raw.trim();

  // Check for conditional command
  const thenMatch = raw.match(/^(.+?)\s+then\s+(.+?)(?:\s+else\s+(.+))?$/i);
  if (thenMatch) {
    const [, condition, thenCmd, elseCmd] = thenMatch;
    return {
      type: 'conditional',
      condition: condition.trim(),
      params: elseCmd ? [thenCmd.trim(), elseCmd.trim()] : [thenCmd.trim()],
      raw
    };
  }

  // Parse command type
  const parts = raw.split(/\s+/);
  const type = parts[0]?.toLowerCase() || '';

  return {
    type,
    params: parts.slice(1),
    raw
  };
}

/**
 * Known command types in VND
 */
const COMMAND_TYPES = {
  // Navigation
  'scene': 'Change to scene N',
  'runprj': 'Load VNP project and go to scene',
  'hotspot': 'Activate hotspot N',

  // Media
  'playavi': 'Play AVI video',
  'playwav': 'Play WAV audio',
  'playtext': 'Display text at position',
  'playhtml': 'Display HTML content',

  // Graphics
  'addbmp': 'Add bitmap image',
  'delbmp': 'Delete bitmap image',
  'toolbar': 'Set toolbar image',
  'defcursor': 'Set cursor',

  // System
  'rundll': 'Execute DLL',
  'closedll': 'Close DLL',
  'closewav': 'Stop audio',

  // Variables
  'set_var': 'Set variable value',
  'inc_var': 'Increment variable',
  'dec_var': 'Decrement variable',

  // Score
  'score': 'Add to score'
};

/**
 * Parse condition expression
 */
function parseCondition(expr: string): { variable: string; operator: string; value: number } | null {
  const match = expr.match(/^(\w+)\s*(=|!=|<|>|<=|>=)\s*(\d+)$/);
  if (match) {
    return {
      variable: match[1],
      operator: match[2],
      value: parseInt(match[3], 10)
    };
  }
  return null;
}

// Export for Node.js usage
export { VNDParser, parseCommand, parseCondition, COMMAND_TYPES };
export type { VNDHeader, VNDVariable, VNDHotspot, VNDCommand, VNDScene, VNDProject };

// CLI usage
if (require.main === module) {
  const fs = require('fs');
  const path = require('path');

  const args = process.argv.slice(2);
  if (args.length === 0) {
    console.log('Usage: npx ts-node vnd-parser.ts <file.vnd>');
    process.exit(1);
  }

  const filePath = args[0];
  const buffer = fs.readFileSync(filePath);
  const parser = new VNDParser(buffer);
  const project = parser.parse();

  console.log('=== VND File Analysis ===\n');
  console.log('Header:');
  console.log(`  Magic: ${project.header.magic}`);
  console.log(`  Version: ${project.header.version}`);
  console.log(`  Application: ${project.header.application}`);
  console.log(`  Developer: ${project.header.developer}`);
  console.log(`  ID: ${project.header.id}`);
  console.log(`  Resolution: ${project.header.width}x${project.header.height}`);
  console.log(`  Resource DLL: ${project.header.resourceDll}`);

  console.log(`\nVariables (${project.variables.length}):`);
  project.variables.forEach(v => {
    console.log(`  ${v.name} = ${v.value}`);
  });
}
