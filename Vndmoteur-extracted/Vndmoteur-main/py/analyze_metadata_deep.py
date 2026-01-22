#!/usr/bin/env python3
"""
Deep analysis of metadata section (541 bytes) - find exact reader functions.
Look for patterns that read in 135 DWORD loop or 541-byte block.
"""

import pefile
import capstone
import struct

def analyze_metadata_section_pattern():
    """
    The metadata section in couleurs1.vnd is 541 bytes (0x21D).
    This is 135 DWORDs + 1 byte. Let's analyze what these values represent.
    """
    
    print("="*80)
    print("METADATA SECTION PATTERN ANALYSIS")
    print("="*80)
    
    # Read the metadata section from couleurs1.vnd
    with open('f:\\Europeo\\FRONTAL\\dll\\couleurs1.vnd', 'rb') as f:
        data = f.read()
    
    # Find metadata start (after symbol table ends at 0x1059)
    metadata_start = 0x1059
    metadata_end = 0x1276  # Text script starts
    metadata = data[metadata_start:metadata_end]
    
    print(f"\nMetadata Section:")
    print(f"  Start: 0x{metadata_start:04X}")
    print(f"  End: 0x{metadata_end:04X}")
    print(f"  Size: {len(metadata)} bytes (0x{len(metadata):X})")
    print(f"  Size in DWORDs: {len(metadata)//4}")
    
    # Parse as DWORDs
    dwords = []
    for i in range(0, len(metadata), 4):
        if i + 4 <= len(metadata):
            dw = struct.unpack('<I', metadata[i:i+4])[0]
            dwords.append(dw)
    
    print(f"\n[PATTERN ANALYSIS]")
    print("-"*80)
    
    # Look for repeating patterns
    # Check if it's a series of records
    
    # Strategy 1: Look for NULL-terminated strings
    null_positions = [i for i, b in enumerate(metadata) if b == 0]
    print(f"\nNULL byte positions (first 50): {null_positions[:50]}")
    
    # Strategy 2: Look for ASCII patterns
    print(f"\n[ASCII PATTERNS]")
    ascii_chunks = []
    current_chunk = []
    for i, b in enumerate(metadata):
        if 32 <= b <= 126:  # Printable ASCII
            current_chunk.append(chr(b))
        else:
            if len(current_chunk) >= 4:  # At least 4 chars
                ascii_chunks.append((i - len(current_chunk), ''.join(current_chunk)))
            current_chunk = []
    
    print("ASCII strings found in metadata:")
    for pos, s in ascii_chunks[:20]:
        print(f"  0x{pos:04X}: '{s}'")
    
    # Strategy 3: Look for pairs of (name_offset, value) or (index, offset)
    print(f"\n[STRUCTURE HYPOTHESIS]")
    print("-"*80)
    
    # Check if dwords come in pairs
    print("\nFirst 40 DWORDs analyzed as potential structure:")
    for i in range(0, min(40, len(dwords)), 2):
        if i+1 < len(dwords):
            dw1 = dwords[i]
            dw2 = dwords[i+1]
            
            # Try to interpret
            interpretation = ""
            
            # Check if dw1 looks like ASCII
            try:
                ascii_bytes = struct.pack('<I', dw1)
                if all(32 <= b <= 126 for b in ascii_bytes):
                    ascii_str = ascii_bytes.decode('ascii')
                    interpretation += f" ('{ascii_str}')"
            except:
                pass
            
            # Check if dw2 is a small number (index/count)
            if dw2 < 256:
                interpretation += f" [dw2 is small: {dw2}]"
            
            print(f"  [{i:3d}] 0x{dw1:08X}, 0x{dw2:08X}{interpretation}")
    
    return metadata

def find_metadata_reader_in_code():
    """Find the exact function that reads the 541-byte metadata."""
    
    print("\n" + "="*80)
    print("SEARCHING FOR METADATA READER FUNCTION")
    print("="*80)
    
    exe_path = 'f:\\Europeo\\FRONTAL\\dll\\europeo.exe'
    pe = pefile.PE(exe_path)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    
    # Find CODE section
    code_section = None
    code_base = 0
    for section in pe.sections:
        if section.Name.decode('utf-8').rstrip('\x00').upper() == 'CODE':
            code_section = section.get_data()
            code_base = pe.OPTIONAL_HEADER.ImageBase + section.VirtualAddress
            break
    
    # Search for loop counters or sizes related to metadata
    # 541 = 0x21D, 135 = 0x87
    
    print("\n[*] Searching for constants: 541 (0x21D), 135 (0x87)...")
    
    found_constants = []
    
    for inst in md.disasm(code_section, code_base):
        # Look for MOV, CMP with our constants
        if inst.mnemonic in ['mov', 'cmp', 'add', 'sub']:
            for op in inst.operands:
                if op.type == capstone.x86.X86_OP_IMM:
                    if op.imm in [541, 0x21D, 135, 0x87]:
                        found_constants.append({
                            'address': inst.address,
                            'instruction': f"{inst.mnemonic} {inst.op_str}",
                            'value': op.imm
                        })
                        print(f"  [!] 0x{inst.address:08X}: {inst.mnemonic} {inst.op_str} (value: {op.imm})")
    
    # If we found constants, disassemble around them
    if found_constants:
        print(f"\n[*] Found {len(found_constants)} references to metadata size constants")
        print("\n[*] Disassembling context around first reference...")
        
        first_ref = found_constants[0]
        start_addr = first_ref['address'] - 100
        offset = start_addr - code_base
        
        if offset > 0 and offset < len(code_section):
            code_chunk = code_section[offset:offset + 500]
            
            print(f"\nContext around 0x{first_ref['address']:08X}:")
            print("-"*80)
            
            count = 0
            for inst in md.disasm(code_chunk, start_addr):
                marker = ">>>" if inst.address == first_ref['address'] else "   "
                print(f"{marker} 0x{inst.address:08X}:  {inst.mnemonic:10} {inst.op_str}")
                
                count += 1
                if count > 50:
                    break
    
    return found_constants

def main():
    metadata = analyze_metadata_section_pattern()
    constants = find_metadata_reader_in_code()
    
    # Write metadata hex dump for manual analysis
    with open('f:\\Europeo\\FRONTAL\\dll\\metadata_hexdump.txt', 'w') as f:
        f.write("METADATA SECTION HEX DUMP (541 bytes)\n")
        f.write("="*80 + "\n\n")
        
        for i in range(0, len(metadata), 16):
            hex_part = ' '.join(f'{b:02X}' for b in metadata[i:i+16])
            ascii_part = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in metadata[i:i+16])
            f.write(f"{i:04X}:  {hex_part:48}  {ascii_part}\n")
    
    print("\n[+] Metadata hex dump written to: metadata_hexdump.txt")
    print("\n[+] Analysis complete!")

if __name__ == '__main__':
    main()
