#!/usr/bin/env python3
"""
Direct binary analysis - scan for VNFILE string and disassemble surrounding code
"""

import pefile
import capstone

def analyze_vnfile_context():
    exe_path = 'f:\\Europeo\\FRONTAL\\dll\\europeo.exe'
    
    print("="*80)
    print("DIRECT VNFILE CONTEXT ANALYSIS")
    print("="*80)
    
    pe = pefile.PE(exe_path)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    
    image_base = pe.OPTIONAL_HEADER.ImageBase
    
    # Find all instances of "VNFILE"
    print("\n[*] Finding VNFILE string locations...")
    vnfile_locations = []
    
    for section in pe.sections:
        data = section.get_data()
        section_name = section.Name.decode('utf-8').rstrip('\x00')
        pos = 0
        
        while True:
            pos = data.find(b'VNFILE', pos)
            if pos == -1:
                break
            
            rva = section.VirtualAddress + pos
            va = image_base + rva
            vnfile_locations.append({
                'va': va,
                'rva': rva,
                'offset': section.PointerToRawData + pos,
                'section': section_name
            })
            print(f"  Found at: VA=0x{va:08X}, RVA=0x{rva:08X}, Section={section_name}")
            pos += 1
    
    # Read raw bytes around VNFILE to understand the structure
    print("\n[*] Analyzing binary structure around VNFILE...")
    
    with open(exe_path, 'rb') as f:
        for loc in vnfile_locations:
            f.seek(loc['offset'] - 50)  # 50 bytes before
            before = f.read(50)
            f.read(6)  # Skip VNFILE
            after = f.read(100)  #  100 bytes after
            
            print(f"\n  Structure at offset 0x{loc['offset']:08X}:")
            print(f"  Before VNFILE: {before.hex(' ')}")
            print(f"  After VNFILE:  {after.hex(' ')}")
            
            # Try to decode strings after VNFILE
            print(f"\n  ASCII interpretation after VNFILE:")
            try:
                # Look for length-prefixed strings
                if len(after) >= 4:
                    length = int.from_bytes(after[0:4], byteorder='little')
                    if 0 < length < 100:
                        print(f"    Possible string length: {length}")
                        if len(after) >= 4 + length:
                            string_data = after[4:4+length]
                            try:
                                decoded = string_data.decode('ascii')
                                print(f"    String: '{decoded}'")
                            except:
                                print(f"    Raw: {string_data.hex(' ')}")
            except Exception as e:
                print(f"    Error: {e}")
    
    # Now let's scan ALL code looking for any comparison with the VNFILE string
    print("\n[*] Scanning ALL code for string comparisons...")
    
    # Find all CODE-like sections
    for section in pe.sections:
        section_name = section.Name.decode('utf-8').rstrip('\x00')
        if 'CODE' in section_name.upper() or section.Characteristics & 0x20000000:
            print(f"\n  Scanning section: {section_name}")
            code_data = section.get_data()
            code_base = image_base + section.VirtualAddress
            
            # Look for STRING comparison functions: strcmp, memcmp, etc.
            # Also look for manual byte comparisons
            
            interesting_instructions = []
            
            for inst in md.disasm(code_data, code_base):
                # Look for CMP with specific byte values (V, N, F, I, L, E in hex)
                if inst.mnemonic == 'cmp':
                    for op in inst.operands:
                        if op.type == capstone.x86.X86_OP_IMM:
                            # Check if comparing against ASCII values of VNFILE characters
                            if op.imm in [0x56, 0x4E, 0x46, 0x49, 0x4C, 0x45]:  # V N F I L E
                                interesting_instructions.append({
                                    'addr': inst.address,
                                    'inst': f"{inst.mnemonic} {inst.op_str}",
                                    'char': chr(op.imm)
                                })
                
                # Look for PUSH of string addresses
                if inst.mnemonic == 'push':
                    for op in inst.operands:
                        if op.type == capstone.x86.X86_OP_IMM:
                            for loc in vnfile_locations:
                                # Check if pushing address near VNFILE
                                if abs(op.imm - loc['va']) < 100:
                                    interesting_instructions.append({
                                        'addr': inst.address,
                                        'inst': f"{inst.mnemonic} {inst.op_str}",
                                        'note': f"Near VNFILE at 0x{loc['va']:08X}"
                                    })
            
            if interesting_instructions:
                print(f"    Found {len(interesting_instructions)} potentially interesting instructions")
                for item in interesting_instructions[:20]:  # Show first 20
                    print(f"      0x{item['addr']:08X}: {item['inst']}", end="")
                    if 'ч' in item:
                        print(f" (char '{item['char']}')", end="")
                    if 'note' in item:
                        print(f" - {item['note']}", end="")
                    print()
    
    # Look for Borland stream functions that might read VND files
    print("\n[*] Checking Borland C++ stream functions...")
    
    stream_funcs = []
    if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT'):
        for entry in pe.DIRECTORY_ENTRY_IMPORT:
            dll_name = entry.dll.decode('utf-8')
            if 'cw3230mt' in dll_name.lower() or 'bds52t' in dll_name.lower():
                print(f"\n  DLL: {dll_name}") 
                for imp in entry.imports:
                    if imp.name:
                        func_name = imp.name.decode('utf-8')
                        # Look for stream/file functions
                        if any(keyword in func_name.lower() for keyword in ['stream', 'file', 'read', 'open', 'fpbase']):
                            va = imp.address + image_base
                            stream_funcs.append((func_name, va))
                            print(f"    {func_name} at 0x{va:08X}")
    
    print("\n[+] Analysis complete")
    return vnfile_locations, stream_funcs

if __name__ == '__main__':
    vnfile_locs, stream_funcs = analyze_vnfile_context()
