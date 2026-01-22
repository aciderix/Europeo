#!/usr/bin/env python3
"""
Enhanced VND file analysis focusing on finding functions that open .vnd files
"""

import pefile
import capstone
import re

def find_vnd_file_handlers(exe_path):
    """Find all functions that might handle .vnd files."""
    
    print("="*80)
    print("VND FILE HANDLER ANALYSIS")
    print("="*80)
    
    pe = pefile.PE(exe_path)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    
    image_base = pe.OPTIONAL_HEADER.ImageBase
    
    # Find CODE section
    code_section = None
    code_base = 0
    for section in pe.sections:
        section_name = section.Name.decode('utf-8').rstrip('\x00')
        if section_name.upper() == 'CODE':
            code_section = section.get_data()
            code_base = image_base + section.VirtualAddress
            print(f"\n[+] CODE section: VA=0x{section.VirtualAddress:08X}, Size={len(code_section)} bytes")
            break
    
    if not code_section:
        print("[!] No CODE section found")
        return
    
    # Search for .vnd and .vnp extensions in all sections
    print("\n[*] Searching for .vnd and .vnp file extension strings...")
    extensions = ['.vnd', '.vnp', '.VND', '.VNP']
    extension_addresses = []
    
    for section in pe.sections:
        data = section.get_data()
        section_name = section.Name.decode('utf-8').rstrip('\x00')
        
        for ext in extensions:
            offset = 0
            while True:
                pos = data.find(ext.encode('ascii'), offset)
                if pos == -1:
                    break
                
                rva = section.VirtualAddress + pos
                va = image_base + rva
                extension_addresses.append((va, rva, ext, section_name))
                print(f"    Found '{ext}' at VA=0x{va:08X}, RVA=0x{rva:08X}, Section={section_name}")
                offset = pos + 1
    
    # Find references to these extensions
    print("\n[*] Searching for code that references these extensions...")
    ext_refs = []
    
    for instruction in md.disasm(code_section, code_base):
        if instruction.mnemonic in ['mov', 'push', 'lea', 'cmp']:
            for op in instruction.operands:
                if op.type == capstone.x86.X86_OP_IMM:
                    for va, rva, ext, sec in extension_addresses:
                        if op.imm == va or op.imm == rva:
                            ext_refs.append({
                                'addr': instruction.address,
                                'inst': f"{instruction.mnemonic} {instruction.op_str}",
                                'ext': ext
                            })
                            print(f"    [!] Reference at 0x{instruction.address:08X}: {instruction.mnemonic} {instruction.op_str}")
    
    # Find CreateFileA, fopen calls
    print("\n[*] Finding file open operations...")
    imports = {}
    if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT'):
        for entry in pe.DIRECTORY_ENTRY_IMPORT:
            for imp in entry.imports:
                if imp.name:
                    func_name = imp.name.decode('utf-8')
                    if func_name in ['CreateFileA', 'CreateFileW', 'fopen', '_wfopen', 'ReadFile']:
                        va = imp.address + image_base
                        imports[func_name] = va
                        print(f"    Found import: {func_name} at VA=0x{va:08X}")
    
    # Find all CALLs to file operations
    print("\n[*] Analyzing CALL instructions to file operations...")
    file_calls = []
    
    for instruction in md.disasm(code_section, code_base):
        if instruction.mnemonic == 'call':
            for op in instruction.operands:
                # Direct call
                if op.type == capstone.x86.X86_OP_IMM:
                    for func_name, func_addr in imports.items():
                        if op.imm == func_addr:
                            file_calls.append({
                                'addr': instruction.address,
                                'func': func_name,
                                'target': op.imm
                            })
                            print(f"    [+] CALL {func_name} at 0x{instruction.address:08X}")
    
    # For each file call, disassemble the surrounding context
    print("\n[*] Disassembling context around file operations...")
    
    with open('f:\\Europeo\\FRONTAL\\dll\\vnd_file_handlers.txt', 'w') as f:
        f.write("VND FILE HANDLER ANALYSIS\n")
        f.write("="*80 + "\n\n")
        
        for call_info in file_calls[:10]:  # Limit to first 10
            # Get context: 30 instructions before the call
            start_addr = call_info['addr'] - 0x80
            start_offset = start_addr - code_base
            
            if start_offset < 0:
                start_offset = 0
                start_addr = code_base
            
            f.write(f"\nContext for CALL to {call_info['func']} at 0x{call_info['addr']:08X}\n")
            f.write("-"*80 + "\n")
            
            code_chunk = code_section[start_offset:start_offset + 400]
            count = 0
            found_call = False
            
            for inst in md.disasm(code_chunk, start_addr):
                prefix = "  "
                if inst.address == call_info['addr']:
                    prefix = ">>>"
                    found_call = True
                
                f.write(f"{prefix} 0x{inst.address:08X}:  {inst.mnemonic:10} {inst.op_str}\n")
                
                count += 1
                if found_call and count > 20:  # Show 20 instructions after the call
                    break
            
            f.write("\n")
        
        # Add extension references
        f.write("\n\n" + "="*80 + "\n")
        f.write("FILE EXTENSION REFERENCES\n")
        f.write("="*80 + "\n\n")
        
        for ref in ext_refs:
            f.write(f"0x{ref['addr']:08X}:  {ref['inst']} - Extension: {ref['ext']}\n")
    
    print("\n[+] Detailed analysis written to: vnd_file_handlers.txt")

if __name__ == '__main__':
    find_vnd_file_handlers('f:\\Europeo\\FRONTAL\\dll\\europeo.exe')
