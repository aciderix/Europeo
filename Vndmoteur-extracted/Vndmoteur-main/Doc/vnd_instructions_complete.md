# VND Instructions - Complete Analysis

## Two Instruction Types

VND files contain TWO types of instructions:

### 1. Binary Opcodes (Metadata Section)

- **Location**: Offset 0x1059-0x1276 (541 bytes)
- **Format**: Binary opcodes with parameters
- **Purpose**: Pre-compiled commands, resource loading, initialization

**Most Common Opcodes**:
```
0x20: 15 occurrences
0x4E: 11 occurrences
0x30: 10 occurrences
0x45: 9 occurrences
0x4F: 9 occurrences
0x55: 9 occurrences
0x41: 9 occurrences
0x69: 9 occurrences
0x53: 8 occurrences
```

### 2. Text Commands (Script Section)

- **Location**: Offset 0x1276-EOF (71KB)
- **Format**: ASCII text commands
- **Purpose**: Game logic, conditional execution, user interaction

**Known Commands**:
```
Control Flow:
  if <condition> then <action>
  else
  goto <label>

Graphics/Media:
  addbmp <file> <x> <y>
  delbmp <id>
  playavi <file>
  playwav <file>
  playtext <text> <params>

Variables:
  setvar <name> <value>
  getvar <name>
  inc_var <name> <amount>
  dec_var <name> <amount>

Navigation:
  runprj <path>
```

## Interpreter Architecture

```
VND File Loaded
    ↓
┌─────────────────────────────────┐
│ 1. BINARY OPCODE INTERPRETER    │
│    - Reads metadata section     │
│    - Executes binary opcodes    │
│    - Loads resources            │
│    - Initializes state          │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│ 2. TEXT COMMAND PARSER          │
│    - Reads script section       │
│    - Tokenizes commands         │
│    - strcmp() to identify cmd   │
│    - Calls handler functions    │
└─────────────────────────────────┘
```

## Next Steps to Complete Reverse Engineering

1. **Find binary opcode interpreter**:
   - Search for switch statements on byte values
   - Look for jump tables indexed by opcode
   - Disassemble the dispatch loop

2. **Find text command parser**:
   - Search for strcmp() calls with command strings
   - Find the command dispatch table
   - Map each command to its handler function

3. **Document opcode meanings**:
   - Create opcode→function mapping
   - Understand parameter formats
   - Document instruction set completely
