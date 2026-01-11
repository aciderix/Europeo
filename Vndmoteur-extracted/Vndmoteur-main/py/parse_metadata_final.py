#!/usr/bin/env python3
"""
Final analysis: Parse the metadata section completely based on patterns discovered.
The metadata appears to contain variable names + script commands that are NOT in the symbol table.
"""

import struct

def parse_metadata_completely():
    """
    Based on the analysis, the metadata section contains:
    - Additional variable names (not in main symbol table)
    - Script commands/actions
    - Resource references (file paths)
    """
    
    with open('f:\\Europeo\\FRONTAL\\dll\\couleurs1.vnd', 'rb') as f:
        data = f.read()
    
    # Metadata section
    metadata_start = 0x1059
    metadata_end = 0x1276
    metadata = data[metadata_start:metadata_end]
    
    print("="*80)
    print("METADATA SECTION COMPLETE PARSE")
    print("="*80)
    
    # The metadata appears to be: additional symbol entries in the SAME format
    # as the main symbol table: [4-byte length][string data][padding]
    
    print("\n[PARSING AS SYMBOL/COMMAND ENTRIES]")
    print("-"*80)
    
    offset = 0
    entries = []
    entry_num = 0
    
    while offset < len(metadata) - 4:
        #  Try to read as length-prefixed string
        length = struct.unpack('<I', metadata[offset:offset+4])[0]
        offset += 4
        
        # Sanity check
        if length == 0 or length > 100:
            # Not a length field, probably data
            offset -= 4
            offset += 1
            continue
        
        if offset + length > len(metadata):
            break
        
        # Read the string
        try:
            string_data = metadata[offset:offset+length]
            string_val = string_data.decode('ascii', errors='replace')
            
            # Check if it's mostly printable
            printable = sum(1 for b in string_data if 32 <= b <= 126)
            if printable > length * 0.7:  # At least 70% printable
                entries.append({
                    'offset': metadata_start + offset - 4,
                    'length': length,
                    'value': string_val.strip('\x00'),
                    'type': 'text'
                })
                print(f"  [{entry_num:3d}] @0x{metadata_start + offset - 4:04X}: '{string_val.strip(chr(0))}'")
                entry_num += 1
            
            offset += length
        except:
            offset += 1
    
    print(f"\n[+] Found {len(entries)} text entries in metadata\n")
    
    # Analyze entry types
    variable_names = []
    file_paths = []
    commands = []
    
    for entry in entries:
        val = entry['value']
        if '\\' in val or '.' in val:
            file_paths.append(val)
        elif val.isupper() or val[0].isupper():
            variable_names.append(val)
        else:
            commands.append(val)
    
    print("[CLASSIFICATION]")
    print("-"*80)
    print(f"\nVariable names ({len(variable_names)}):")
    for v in variable_names[:20]:
        print(f"  {v}")
    if len(variable_names) > 20:
        print(f"  ... and {len(variable_names) - 20} more")
    
    print(f"\nFile paths ({len(file_paths)}):")
    for f in file_paths:
        print(f"  {f}")
    
    print(f"\nCommands/Other ({len(commands)}):")
    for c in commands[:10]:
        print(f"  {c}")
    
    # Write complete report
    with open('f:\\Europeo\\FRONTAL\\dll\\metadata_complete_analysis.md', 'w') as f:
        f.write("# VND Metadata Section - Complete Analysis\n\n")
        f.write("## Overview\n\n")
        f.write(f"- **Location**: 0x{metadata_start:04X} - 0x{metadata_end:04X}\n")
        f.write(f"- **Size**: {len(metadata)} bytes\n")
        f.write(f"- **Structure**: Length-prefixed text entries (same format as main symbol table)\n")
        f.write(f"- **Purpose**: Extended symbols, commands, and resource references\n\n")
        
        f.write("## Contents\n\n")
        f.write(f"Total entries found: **{len(entries)}**\n\n")
        
        f.write("### Variable Names\n\n")
        f.write("Additional variable names not in main symbol table:\n\n")
        for v in variable_names:
            f.write(f"- `{v}`\n")
        
        f.write("\n### File Paths / Resources\n\n")
        for path in file_paths:
            f.write(f"- `{path}`\n")
        
        f.write("\n### Commands / Other\n\n")
        for cmd in commands:
            f.write(f"- `{cmd}`\n")
        
        f.write("\n## Interpretation\n\n")
        f.write("The metadata section appears to contain:\n\n")
        f.write("1. **Dynamic variable names**: Variables created at runtime or specific to this scene\n")
        f.write("2. **Resource references**: Paths to BMP, WAV, AVI files used in the scene\n")
        f.write("3. **UI commands**: Text display commands, positioning, etc.\n\n")
        
        f.write("## How It's Used\n\n")
        f.write("The engine reads this section after loading the main symbol table.\n")
        f.write("Each entry is processed and likely:\n")
        f.write("- Registered in a runtime symbol map\n")
        f.write("- Used to pre-load resources\n")
        f.write("- Set up UI elements\n")
    
    print("\n[+] Complete analysis written to: metadata_complete_analysis.md")
    return entries

if __name__ == '__main__':
    entries = parse_metadata_completely()
