#!/usr/bin/env python3
"""
Analyze BINARY opcodes in VND metadata section.
The 541-byte metadata section likely contains binary instructions (opcodes).
Find the interpreter that reads and executes these opcodes.
"""

import struct

def analyze_binary_opcodes():
    """Analyze the metadata section for binary instruction patterns."""
    
    with open('f:\\Europeo\\FRONTAL\\dll\\couleurs1.vnd', 'rb') as f:
        data = f.read()
    
    # Metadata section
    metadata_start = 0x1059
    metadata_end = 0x1276
    metadata = data[metadata_start:metadata_end]
    
    print("="*80)
    print("BINARY OPCODE ANALYSIS - Metadata Section")
    print("="*80)
    print(f"\nMetadata: {len(metadata)} bytes at offset 0x{metadata_start:04X}\n")
    
    # Look for patterns that could be opcodes
    # Hypothesis: Structure might be [opcode][params...]
    
    print("[BYTE VALUE FREQUENCY]")
    print("-"*80)
    
    # Count frequency of each byte value
    freq = {}
    for b in metadata:
        freq[b] = freq.get(b, 0) + 1
    
    # Show most common bytes (likely opcodes)
    print("\nMost common byte values (potential opcodes):")
    for byte_val, count in sorted(freq.items(), key=lambda x: -x[1])[:20]:
        if byte_val != 0:  # Skip NULL
            print(f"  0x{byte_val:02X} ({byte_val:3d}): {count:3d} times", end="")
            if 32 <= byte_val <= 126:
                print(f" ('{chr(byte_val)}')")
            else:
                print()
    
    # Look for sequences that repeat
    print("\n[REPEATING PATTERNS]")
    print("-"*80)
    
    # Check for 2-byte, 3-byte, and 4-byte patterns
    for pattern_len in [2, 3, 4]:
        patterns = {}
        for i in range(len(metadata) - pattern_len):
            pattern = metadata[i:i+pattern_len]
            # Skip all-zero patterns
            if pattern != b'\x00' * pattern_len:
                patterns[pattern] = patterns.get(pattern, 0) + 1
        
        # Show patterns that appear more than once
        repeated = [(p, c) for p, c in patterns.items() if c > 1]
        if repeated:
            print(f"\n{pattern_len}-byte patterns (appearing {'>'}1 time):")
            for pattern, count in sorted(repeated, key=lambda x: -x[1])[:10]:
                hex_str = ' '.join(f'{b:02X}' for b in pattern)
                print(f"  {hex_str}: {count} times")
    
    # Analyze as potential instruction stream
    print("\n[POTENTIAL INSTRUCTION STREAM]")
    print("-"*80)
    
    # Try to parse as [opcode][count/size][data...]
    offset = 0
    instructions = []
    
    while offset < len(metadata) - 4:
        # Read potential opcode
        opcode = metadata[offset]
        
        # Skip large sequences of NULLs
        if opcode == 0:
            offset += 1
            continue
        
        # Read next 3 bytes as potential size/params
        if offset + 4 <= len(metadata):
            param1 = metadata[offset + 1]
            param2 = metadata[offset + 2]
            param3 = metadata[offset + 3]
            
            # Check if looks like length-prefixed data
            size = struct.unpack('<I', metadata[offset:offset+4])[0]
            
            # If size is reasonable (1-100) and we have enough data
            if 1 <= size <= 100 and offset + 4 + size <= len(metadata):
                # This might be [4-byte size][data]
                data_chunk = metadata[offset+4:offset+4+size]
                
                # Check if data is mostly ASCII
                ascii_count = sum(1 for b in data_chunk if 32 <= b <= 126)
                if ascii_count > size * 0.7:
                    try:
                        text = data_chunk.decode('ascii', errors='replace').strip('\x00')
                        instructions.append({
                            'offset': metadata_start + offset,
                            'type': 'string',
                            'size': size,
                            'data': text
                        })
                        print(f"0x{metadata_start + offset:04X}: STRING[{size:2d}] = '{text}'")
                        offset += 4 + size
                        continue
                    except:
                        pass
        
        # Otherwise, just show as potential opcode + params
        if offset + 4 <= len(metadata):
            instructions.append({
                'offset': metadata_start + offset,
                'type': 'opcode',
                'opcode': opcode,
                'params': [param1, param2, param3]
            })
            
            # Show readable interpretation
            param_str = f"{param1:02X} {param2:02X} {param3:02X}"
            offset += 4
        else:
            offset += 1
    
    print(f"\n[+] Identified {len(instructions)} potential instructions")
    
    # Now look for the INTERPRETER in europeo.exe
    print("\n" + "="*80)
    print("SEARCHING FOR BINARY INSTRUCTION INTERPRETER")
    print("="*80)
    
    # The interpreter likely:
    # 1. Reads a byte (opcode)
    # 2. Has a switch/case or jump table
    # 3. Calls different handlers based on opcode
    
    print("""
The binary instructions are likely interpreted by a function that:
1. Reads opcodes from the metadata section
2. Uses a switch statement or jump table to dispatch
3. Calls handler functions based on opcode value

Common opcode values found:
- Small values (0x00-0x0F): Likely control flow opcodes
- ASCII range (0x41-0x5A): Might be command codes
- NULL (0x00): Padding or NOP instruction
    
To find the interpreter, look for:
- Functions with large switch statements
- Jump tables indexed by byte values
- Loops that read and dispatch bytes
""")
    
    return instructions

def find_text_command_parser():
    """Find the parser for text commands (if/then/addbmp/etc)."""
    
    print("\n" + "="*80)
    print("TEXT COMMAND PARSER")
    print("="*80)
    
    # We found command strings at these addresses in europeo.exe:
    command_strings = {
        'addbmp': 0x0043F82D,
        'delbmp': 0x0043F834,
        'playavi': 0x0043F7A2,
        'playtext': 0x0043F881,
        'playwav': 0x0043F7B2,
        'runprj': 0x0043F84B,
        'inc_var': 0x0043F808,
        'dec_var': 0x0043F810,
        'then': 0x0043F9F1,
        'else': 0x0043F9F8,
    }
    
    print("\nCommand strings found in europeo.exe DATA section:")
    for cmd, addr in sorted(command_strings.items()):
        print(f"  '{cmd:12}' @ 0x{addr:08X}")
    
    print("""
These strings are likely used in string comparison functions like strcmp().
The text command parser probably:
1. Reads a line/token from the script section
2. Compares it against known command strings
3. Calls appropriate handler function

Pattern: if (strcmp(token, "addbmp") == 0) { handle_addbmp(); }
""")

def main():
    print("VND INSTRUCTION ANALYSIS")
    print("="*80)
    print("Analyzing BOTH binary opcodes AND text commands\n")
    
    # 1. Analyze binary opcodes in metadata
    binary_instr = analyze_binary_opcodes()
    
    # 2. Analyze text command parser
    find_text_command_parser()
    
    # Write comprehensive report
    with open('f:\\Europeo\\FRONTAL\\dll\\vnd_instructions_complete.md', 'w', encoding='utf-8') as f:
        f.write("# VND Instructions - Complete Analysis\n\n")
        
        f.write("## Two Instruction Types\n\n")
        f.write("VND files contain TWO types of instructions:\n\n")
        
        f.write("### 1. Binary Opcodes (Metadata Section)\n\n")
        f.write(f"- **Location**: Offset 0x1059-0x1276 (541 bytes)\n")
        f.write(f"- **Format**: Binary opcodes with parameters\n")
        f.write(f"- **Purpose**: Pre-compiled commands, resource loading, initialization\n\n")
        
        f.write("**Most Common Opcodes**:\n")
        f.write("```\n")
        # Re-analyze for file
        with open('f:\\Europeo\\FRONTAL\\dll\\couleurs1.vnd', 'rb') as vnd:
            data = vnd.read()
        metadata = data[0x1059:0x1276]
        freq = {}
        for b in metadata:
            freq[b] = freq.get(b, 0) + 1
        for byte_val, count in sorted(freq.items(), key=lambda x: -x[1])[:10]:
            if byte_val != 0:
                f.write(f"0x{byte_val:02X}: {count} occurrences\n")
        f.write("```\n\n")
        
        f.write("### 2. Text Commands (Script Section)\n\n")
        f.write(f"- **Location**: Offset 0x1276-EOF (71KB)\n")
        f.write(f"- **Format**: ASCII text commands\n")
        f.write(f"- **Purpose**: Game logic, conditional execution, user interaction\n\n")
        
        f.write("**Known Commands**:\n")
        f.write("```\n")
        f.write("Control Flow:\n")
        f.write("  if <condition> then <action>\n")
        f.write("  else\n")
        f.write("  goto <label>\n\n")
        f.write("Graphics/Media:\n")
        f.write("  addbmp <file> <x> <y>\n")
        f.write("  delbmp <id>\n")
        f.write("  playavi <file>\n")
        f.write("  playwav <file>\n")
        f.write("  playtext <text> <params>\n\n")
        f.write("Variables:\n")
        f.write("  setvar <name> <value>\n")
        f.write("  getvar <name>\n")
        f.write("  inc_var <name> <amount>\n")
        f.write("  dec_var <name> <amount>\n\n")
        f.write("Navigation:\n")
        f.write("  runprj <path>\n")
        f.write("```\n\n")
        
        f.write("## Interpreter Architecture\n\n")
        f.write("```\n")
        f.write("VND File Loaded\n")
        f.write("    ↓\n")
        f.write("┌─────────────────────────────────┐\n")
        f.write("│ 1. BINARY OPCODE INTERPRETER    │\n")
        f.write("│    - Reads metadata section     │\n")
        f.write("│    - Executes binary opcodes    │\n")
        f.write("│    - Loads resources            │\n")
        f.write("│    - Initializes state          │\n")
        f.write("└─────────────────────────────────┘\n")
        f.write("    ↓\n")
        f.write("┌─────────────────────────────────┐\n")
        f.write("│ 2. TEXT COMMAND PARSER          │\n")
        f.write("│    - Reads script section       │\n")
        f.write("│    - Tokenizes commands         │\n")
        f.write("│    - strcmp() to identify cmd   │\n")
        f.write("│    - Calls handler functions    │\n")
        f.write("└─────────────────────────────────┘\n")
        f.write("```\n\n")
        
        f.write("## Next Steps to Complete Reverse Engineering\n\n")
        f.write("1. **Find binary opcode interpreter**:\n")
        f.write("   - Search for switch statements on byte values\n")
        f.write("   - Look for jump tables indexed by opcode\n")
        f.write("   - Disassemble the dispatch loop\n\n")
        f.write("2. **Find text command parser**:\n")
        f.write("   - Search for strcmp() calls with command strings\n")
        f.write("   - Find the command dispatch table\n")
        f.write("   - Map each command to its handler function\n\n")
        f.write("3. **Document opcode meanings**:\n")
        f.write("   - Create opcode→function mapping\n")
        f.write("   - Understand parameter formats\n")
        f.write("   - Document instruction set completely\n")
    
    print(f"\n[+] Complete analysis written to: vnd_instructions_complete.md")
    print("\n[+] Analysis complete!")

if __name__ == '__main__':
    main()
