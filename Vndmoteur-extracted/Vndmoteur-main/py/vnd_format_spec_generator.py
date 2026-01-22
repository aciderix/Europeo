#!/usr/bin/env python3
"""
Complete VND binary format documentation generator (fixed encoding)
"""

import struct
import os

def parse_vnd_complete(vnd_path, output_file):
    """Parse VND file and write analysis to file."""
    
    with open(vnd_path, 'rb') as f:
        data = f.read()
    
    out = []
    out.append("="*80)
    out.append("VND BINARY FORMAT - COMPLETE SPECIFICATION")
    out.append(f"File: {os.path.basename(vnd_path)}")
    out.append(f"Size: {len(data)} bytes")
    out.append("="*80)
    out.append("")
    
    offset = 0
    
    # Header
    out.append("[HEADER - 12 bytes]")
    out.append("-"*80)
    field1, field2, field3 = struct.unpack('<III', data[offset:offset+12])
    out.append(f"Offset 0x0000: field1 = 0x{field1:08X} ({field1})")
    out.append(f"Offset 0x0004: field2 = 0x{field2:08X} ({field2})")
    out.append(f"Offset 0x0008: field3 = 0x{field3:08X} ({field3})")
    offset += 12
    
    # Find VNFILE
    vnfile_pos = data.find(b'VNFILE')
    if vnfile_pos < 0:
        out.append("ERROR: VNFILE signature not found!")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(out))
        return
    
    out.append(f"\nVNFILE signature at offset: 0x{vnfile_pos:04X}")
    offset = vnfile_pos + 6
    
    # Length-prefixed fields
    out.append("\n[STRING FIELDS - Length-Prefixed (4-byte length + data)]")
    out.append("-"*80)
    
    def read_lpstring():
        nonlocal offset
        if offset + 4 > len(data):
            return None
        length = struct.unpack('<I', data[offset:offset+4])[0]
        offset += 4
        if offset + length > len(data) or length > 10000:
            return None
        s = data[offset:offset+length]
        offset += length
        return s
    
    # Field 1: Version
    version_bytes = read_lpstring()
    if version_bytes:
        version = version_bytes.decode('ascii', errors='replace')
        out.append(f"Version: '{version}' ({len(version_bytes)} bytes)")
    
    # Field 2: Application  
    app_bytes = read_lpstring()
    if app_bytes:
        # Only show printable part
        app_clean = app_bytes.decode('ascii', errors='replace').split('\x00')[0]
        out.append(f"Application: '{app_clean}' ({len(app_bytes)} bytes total)")
    
    # Field 3: Symbol table (huge!)
    symbol_bytes = read_lpstring()
    if symbol_bytes:
        out.append(f"\nSymbol Table: {len(symbol_bytes)} bytes")
        # Parse as null-separated strings
        symbols = symbol_bytes.split(b'\x00')
        symbols = [s.decode('ascii', errors='replace') for s in symbols if s]
        out.append(f"  Found {len(symbols)} symbols")
        out.append(f"  First 30 symbols:")
        for i, sym in enumerate(symbols[:30]):
            out.append(f"    [{i:3d}] {sym}")
    
    # Field 4: GUID
    guid_bytes = read_lpstring()
    if guid_bytes:
        guid = guid_bytes.decode('ascii', errors='replace')
        out.append(f"\nGUID/ID: '{guid.strip()}' ({len(guid_bytes)} bytes)")
    
    out.append(f"\nEnd of string fields at offset: 0x{offset:04X}")
    
    # Metadata section
    out.append("\n[BINARY METADATA SECTION]")
    out.append("-"*80)
    
    # Find text start
    text_keywords = [b'if ', b'then', b'addbmp']
    text_start = len(data)
    for kw in text_keywords:
        pos = data.find(kw, offset)
        if pos > offset and pos < text_start:
            text_start = pos
    
    metadata_section = data[offset:text_start]
    out.append(f"Metadata starts at: 0x{offset:04X}")
    out.append(f"Text starts at: 0x{text_start:04X}")
    out.append(f"Metadata size: {len(metadata_section)} bytes\n")
    
    # Analyze as DWORDs  
    out.append("First 40 DWORD values:")
    for i in range(min(40, len(metadata_section) // 4)):
        val = struct.unpack('<I', metadata_section[i*4:(i+1)*4])[0]
        # Try to interpret
        interpretation = ""
        if val == 0:
            interpretation = " (NULL)"
        elif val < 256:
            interpretation = f" (small int, possibly type/flag)"
        elif val > 0x400000 and val < 0x500000:
            interpretation = f" (possible memory address)"
        
        out.append(f"  [+{i*4:03X}] 0x{val:08X} = {val:10d}{interpretation}")
    
    # Byte patterns
    null_count = metadata_section.count(b'\x00')
    out.append(f"\nByte statistics:")
    out.append(f"  NULL bytes: {null_count} ({null_count*100//len(metadata_section)}%)")
    
    # Script section
    out.append("\n[TEXT SCRIPT SECTION]")
    out.append("-"*80)
    script_bytes = data[text_start:]
    script_text = script_bytes.decode('ascii', errors='replace')
    
    out.append(f"Script size: {len(script_bytes)} bytes")
    out.append(f"Script starts at: 0x{text_start:04X}\n")
    
    # Count commands
    commands = {}
    for cmd in ['if ', 'then', 'else', 'addbmp', 'delbmp', 'playavi', 'runprj']:
        count = script_text.count(cmd)
        if count > 0:
            commands[cmd] = count
    
    out.append("Command frequency:")
    for cmd, count in sorted(commands.items(), key=lambda x: -x[1]):
        out.append(f"  {cmd:10} : {count:4d}")
    
    out.append("\nFirst 800 characters of script:")
    out.append(script_text[:800])
    
    # Generate structure spec
    out.append("\n" + "="*80)
    out.append("FORMAT SPECIFICATION")
    out.append("="*80)
    out.append("""
VND File Structure:

┌─────────────────────────────────────────────────────────┐
│ HEADER (12 bytes)                                        │
├─────────────────────────────────────────────────────────┤
│ 0x00: uint32 field1    (purpose unknown)                │
│ 0x04: uint32 field2    (purpose unknown)                │
│ 0x08: uint32 field3    (purpose unknown)                │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ VNFILE SIGNATURE (variable position, typically 0x09)    │
├─────────────────────────────────────────────────────────┤
│ char[6] "VNFILE"                                         │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ STRING FIELDS (length-prefixed)                          │
├─────────────────────────────────────────────────────────┤
│ FIELD 1: Version string                                  │
│   uint32 length                                          │
│   char[length] data                                      │
│                                                           │
│ FIELD 2: Application name                                │
│   uint32 length                                          │
│   char[length] data                                      │
│                                                           │
│ FIELD 3: Symbol table (NULL-separated variable names)   │
│   uint32 length                                          │
│   char[length] data                                      │
│                                                           │
│ FIELD 4: GUID/ID                                         │
│   uint32 length                                          │
│   char[length] data                                      │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ BINARY METADATA (~500-600 bytes, structure TBD)         │
├─────────────────────────────────────────────────────────┤
│ Purpose: Index, offsets, or runtime data                │
│ Contains mostly DWORD (uint32) values                   │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ TEXT SCRIPT (remainder of file)                          │
├─────────────────────────────────────────────────────────┤
│ ASCII text commands (if/then/else/addbmp/etc)           │
│ References variables from symbol table by index         │
└─────────────────────────────────────────────────────────┘

Python parsing code:

```python
def parse_vnd(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()
    
    offset = 0
    
    # Read header
    field1, field2, field3 = struct.unpack('<III', data[offset:offset+12])
    offset += 12
    
    # Find VNFILE
    vnfile_pos = data.find(b'VNFILE', offset)
    offset = vnfile_pos + 6
    
    def read_lpstring():
        nonlocal offset
        length = struct.unpack('<I', data[offset:offset+4])[0]
        offset += 4
        s = data[offset:offset+length]
        offset += length
        return s
    
    version = read_lpstring().decode('ascii')
    application = read_lpstring()
    symbols_raw = read_lpstring()
    guid = read_lpstring().decode('ascii')
    
    # Parse symbol table
    symbols = [s.decode('ascii') for s in symbols_raw.split(b'\\x00') if s]
    
    # Find script start
    text_start = data.find(b'if ', offset)
    metadata = data[offset:text_start]
    script = data[text_start:].decode('ascii')
    
    return {
        'version': version,
        'application': application,
        'symbols': symbols,
        'guid': guid,
        'metadata': metadata,
        'script': script
    }
```
""")
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8', errors='replace') as f:
        f.write('\n'.join(out))
    
    print(f"[+] Analysis written to: {output_file}")

if __name__ == '__main__':
    vnd_path = 'f:\\Europeo\\FRONTAL\\dll\\couleurs1.vnd'
    output_file = 'f:\\Europeo\\FRONTAL\\dll\\vnd_binary_format_spec.md'
    
    parse_vnd_complete(vnd_path, output_file)
    print("[+] Complete!")
