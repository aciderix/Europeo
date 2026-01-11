#!/usr/bin/env python3
"""
Find VND command interpreters and instruction parsers.
Look for:
1. String references to VND commands (addbmp, playavi, setvar, etc.)
2. Dispatch tables that map commands to handlers
3. Parser functions that read and execute instructions
"""

import pefile
import capstone
import struct

def find_command_strings(dll_path):
    """Find references to VND command strings in the executable."""
    
    print("="*80)
    print(f"SEARCHING FOR VND COMMAND PARSERS")
    print(f"DLL: {dll_path}")
    print("="*80)
    
    pe = pefile.PE(dll_path)
    image_base = pe.OPTIONAL_HEADER.ImageBase
    
    # VND commands we know from the script section
    vnd_commands = [
        b'if ', b'then', b'else',
        b'addbmp', b'delbmp',
        b'playavi', b'stopavi',
        b'playtext', b'deltext',
        b'setvar', b'getvar', b'inc_var', b'dec_var',
        b'runprj',
        b'goto', b'gosub', b'return',
        b'playwav', b'stopwav'
    ]
    
    found_commands = {}
    
    # Search all sections for command strings
    for section in pe.sections:
        data = section.get_data()
        section_name = section.Name.decode('utf-8').rstrip('\x00')
        section_va = image_base + section.VirtualAddress
        
        for cmd in vnd_commands:
            pos = 0
            while True:
                pos = data.find(cmd, pos)
                if pos == -1:
                    break
                
                va = section_va + pos
                cmd_str = cmd.decode('ascii', errors='replace')
                
                if cmd_str not in found_commands:
                    found_commands[cmd_str] = []
                
                found_commands[cmd_str].append({
                    'va': va,
                    'section': section_name,
                    'offset': pos
                })
                pos += 1
    
    print(f"\n[FOUND COMMAND STRINGS]")
    print("-"*80)
    for cmd, locations in sorted(found_commands.items()):
        print(f"\n'{cmd}' ({len(locations)} occurrences):")
        for loc in locations[:3]:  # Show first 3
            print(f"  0x{loc['va']:08X} in {loc['section']}")
    
    return found_commands

def find_string_references_in_code(dll_path, string_va, search_range=500000):
    """Find code that references a specific string address."""
    
    pe = pefile.PE(dll_path)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    
    image_base = pe.OPTIONAL_HEADER.ImageBase
    
    # Find CODE section
    code_section = None
    code_base = 0
    for section in pe.sections:
        if section.Name.decode('utf-8').rstrip('\x00').upper() == 'CODE':
            code_section = section.get_data()
            code_base = image_base + section.VirtualAddress
            break
    
    if not code_section:
        return []
    
    references = []
    
    # Limit search to avoid too long analysis
    search_data = code_section[:min(len(code_section), search_range)]
    
    for inst in md.disasm(search_data, code_base):
        # Look for PUSH or MOV with the string address
        if inst.mnemonic in ['push', 'mov', 'lea']:
            for op in inst.operands:
                if op.type == capstone.x86.X86_OP_IMM:
                    # Check if this immediate is close to our string address
                    if abs(op.imm - string_va) < 20:  # Allow small offset
                        references.append({
                            'addr': inst.address,
                            'instruction': f"{inst.mnemonic} {inst.op_str}",
                            'string_addr': string_va
                        })
    
    return references

def find_command_handlers(dll_path):
    """Find functions that likely handle VND commands."""
    
    pe = pefile.PE(dll_path)
    
    print(f"\n[SEARCHING EXPORTS FOR COMMAND HANDLERS]")
    print("-"*80)
    
    handlers = []
    
    if hasattr(pe, 'DIRECTORY_ENTRY_EXPORT'):
        for export in pe.DIRECTORY_ENTRY_EXPORT.symbols:
            if export.name:
                name = export.name.decode('utf-8', errors='replace')
                
                # Look for function names that suggest command handling
                keywords = ['command', 'cmd', 'execute', 'run', 'do', 'parse', 
                           'interp', 'eval', 'process', 'handle']
                
                if any(kw in name.lower() for kw in keywords):
                    handlers.append({
                        'name': name,
                        'rva': export.address
                    })
                    print(f"  {name} @ 0x{export.address:08X}")
    
    return handlers

def analyze_europeo_for_interpreters():
    """Analyze europeo.exe for VND script interpreters."""
    
    exe_path = 'f:\\Europeo\\FRONTAL\\dll\\europeo.exe'
    
    print("\n" + "="*80)
    print("ANALYZING europeo.exe FOR SCRIPT INTERPRETER")
    print("="*80)
    
    # 1. Find command strings
    commands = find_command_strings(exe_path)
    
    # 2. For key commands, find code references
    if 'addbmp' in commands and commands['addbmp']:
        print(f"\n[FINDING CODE THAT USES 'addbmp']")
        print("-"*80)
        
        addbmp_va = commands['addbmp'][0]['va']
        refs = find_string_references_in_code(exe_path, addbmp_va)
        
        print(f"Found {len(refs)} code references to 'addbmp':")
        for ref in refs[:10]:
            print(f"  0x{ref['addr']:08X}: {ref['instruction']}")
    
    # 3. Search for command handlers
    handlers = find_command_handlers(exe_path)
    
    # Write report
    with open('f:\\Europeo\\FRONTAL\\dll\\vnd_command_interpreter_analysis.txt', 'w') as f:
        f.write("VND COMMAND INTERPRETER ANALYSIS\n")
        f.write("="*80 + "\n\n")
        
        f.write("COMMAND STRINGS FOUND:\n")
        f.write("-"*80 + "\n")
        for cmd, locs in sorted(commands.items()):
            f.write(f"\n'{cmd}': {len(locs)} occurrence(s)\n")
            for loc in locs:
                f.write(f"  0x{loc['va']:08X} in {loc['section']}\n")
        
        f.write("\n\nCOMMAND HANDLERS (from exports):\n")
        f.write("-"*80 + "\n")
        for h in handlers:
            f.write(f"{h['name']} @ 0x{h['rva']:08X}\n")
    
    print("\n[+] Analysis written to: vnd_command_interpreter_analysis.txt")

def analyze_vndllapi_for_vars():
    """Analyze vndllapi.dll for variable handling (setvar, getvar)."""
    
    dll_path = 'f:\\Europeo\\FRONTAL\\dll\\vndllapi.dll'
    
    print("\n" + "="*80)
    print("ANALYZING vndllapi.dll FOR VARIABLE HANDLERS")
    print("="*80)
    
    pe = pefile.PE(dll_path)
    
    # We already know these exports exist
    print("\nKnown variable functions:")
    print("  VNDLLVarAddModify - Add or modify variable")
    print("  VNDLLVarFind - Find variable by name")
    print("  VNDLLVarGet - Get variable value")
    print("  VNDLLVarSet - Set variable value")
    
    # These are the functions that IMPLEMENT setvar/getvar commands!

def main():
    print("VND COMMAND INTERPRETER SEARCH")
    print("="*80)
    print("Looking for code that parses and executes VND commands\n")
    
    # Analyze main executable
    analyze_europeo_for_interpreters()
    
    # Analyze variable handler
    analyze_vndllapi_for_vars()
    
    print("\n[+] Complete!")
    print("\nNext steps:")
    print("  1. Disassemble functions that reference command strings")
    print("  2. Look for switch/case or jump tables")
    print("  3. Trace execution from command string to handler")

if __name__ == '__main__':
    main()
