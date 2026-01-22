#!/usr/bin/env python3
"""
Analyze owl52t.dll and other DLLs to find event handling functions that read VND binary metadata.
Focus on finding functions that process the 541-byte metadata section.
"""

import pefile
import capstone
import os

def analyze_dll_for_vnd_handlers(dll_path):
    """Analyze a DLL for VND-related event handlers and binary readers."""
    
    print("="*80)
    print(f"ANALYZING: {os.path.basename(dll_path)}")
    print("="*80)
    
    if not os.path.exists(dll_path):
        print(f"[!] File not found: {dll_path}")
        return {}
    
    try:
        pe = pefile.PE(dll_path)
    except Exception as e:
        print(f"[!] Error loading PE: {e}")
        return {}
    
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    
    image_base = pe.OPTIONAL_HEADER.ImageBase
    
    results = {
        'exports': [],
        'imports': [],
        'event_handlers': [],
        'binary_readers': []
    }
    
    # 1. Analyze exports
    print("\n[EXPORTS]")
    print("-"*80)
    
    if hasattr(pe, 'DIRECTORY_ENTRY_EXPORT'):
        for export in pe.DIRECTORY_ENTRY_EXPORT.symbols:
            if export.name:
                name = export.name.decode('utf-8', errors='replace')
                results['exports'].append({
                    'name': name,
                    'address': export.address,
                    'ordinal': export.ordinal
                })
                
                # Look for event-related exports
                if any(kw in name.lower() for kw in ['event', 'message', 'dispatch', 'handle', 'wm_', 'notify', 'command']):
                    print(f"  [EVENT] {name} @ 0x{export.address:08X}")
                    results['event_handlers'].append(name)
                
                # Look for binary reading exports
                if any(kw in name.lower() for kw in ['read', 'load', 'parse', 'stream', 'binary', 'data']):
                    print(f"  [READER] {name} @ 0x{export.address:08X}")
                    results['binary_readers'].append(name)
        
        print(f"\nTotal exports: {len(results['exports'])}")
        print(f"Event handlers: {len(results['event_handlers'])}")
        print(f"Binary readers: {len(results['binary_readers'])}")
    else:
        print("  No exports found")
    
    # 2. Analyze imports - what this DLL uses
    print("\n[IMPORTS]")
    print("-"*80)
    
    if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT'):
        for entry in pe.DIRECTORY_ENTRY_IMPORT:
            dll_name = entry.dll.decode('utf-8')
            print(f"\n  From {dll_name}:")
            
            for imp in entry.imports:
                if imp.name:
                    func_name = imp.name.decode('utf-8')
                    results['imports'].append({
                        'dll': dll_name,
                        'function': func_name,
                        'address': imp.address
                    })
                    
                    # Show interesting imports
                    if any(kw in func_name.lower() for kw in ['read', 'event', 'message', 'dispatch', 'handle']):
                        print(f"    {func_name}")
    
    return results

def find_metadata_readers():
    """
    Find functions that likely read the VND metadata section.
    We know metadata is 541 bytes, so look for:
    - Loops reading ~135 DWORDs
    - Read operations with size around 541
    - Structures with ~135 elements
    """
    
    print("\n" + "="*80)
    print("SEARCHING FOR METADATA SECTION READERS")
    print("="*80)
    
    # Analyze europeo.exe for functions that read after symbol table
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
    
    if not code_section:
        print("[!] CODE section not found")
        return
    
    print("\n[*] Looking for constants related to metadata size...")
    print("    Target values: 541 (0x21D), 135 (0x87 DWORDs)")
    
    # Search for these specific constants
    constants = [
        (541, 0x21D, "metadata size in bytes"),
        (135, 0x87, "metadata size in DWORDs"),
        (4096, 0x1000, "symbol table size"),
    ]
    
    findings = []
    
    for inst in md.disasm(code_section, code_base):
        # Look for immediate values matching our constants
        if inst.mnemonic in ['mov', 'cmp', 'add', 'sub', 'push']:
            for op in inst.operands:
                if op.type == capstone.x86.X86_OP_IMM:
                    for val, hex_val, desc in constants:
                        if op.imm == val or op.imm == hex_val:
                            findings.append({
                                'address': inst.address,
                                'instruction': f"{inst.mnemonic} {inst.op_str}",
                                'value': val,
                                'description': desc
                            })
                            print(f"  [!] 0x{inst.address:08X}: {inst.mnemonic} {inst.op_str} - {desc}")
    
    return findings

def main():
    # Analyze owl52t.dll
    owl_results = analyze_dll_for_vnd_handlers('f:\\Europeo\\FRONTAL\\dll\\owl52t.dll')
    
    # Analyze other relevant DLLs
    dlls_to_check = [
        'f:\\Europeo\\FRONTAL\\dll\\bds52t.dll',
        'f:\\Europeo\\FRONTAL\\dll\\Euro32.dll',
    ]
    
    all_results = {'owl52t.dll': owl_results}
    
    for dll_path in dlls_to_check:
        if os.path.exists(dll_path):
            dll_name = os.path.basename(dll_path)
            all_results[dll_name] = analyze_dll_for_vnd_handlers(dll_path)
    
    # Search for metadata readers
    metadata_findings = find_metadata_readers()
    
    # Generate report
    print("\n" + "="*80)
    print("SUMMARY REPORT")
    print("="*80)
    
    with open('f:\\Europeo\\FRONTAL\\dll\\event_handler_analysis.txt', 'w') as f:
        f.write("VND EVENT HANDLER AND METADATA READER ANALYSIS\n")
        f.write("="*80 + "\n\n")
        
        for dll_name, results in all_results.items():
            f.write(f"\n{dll_name}\n")
            f.write("-"*80 + "\n")
            
            f.write(f"\nEvent Handlers ({len(results.get('event_handlers', []))}):\n")
            for handler in results.get('event_handlers', []):
                f.write(f"  {handler}\n")
            
            f.write(f"\nBinary Readers ({len(results.get('binary_readers', []))}):\n")
            for reader in results.get('binary_readers', []):
                f.write(f"  {reader}\n")
        
        if metadata_findings:
            f.write("\n\nMETADATA SIZE CONSTANT REFERENCES\n")
            f.write("-"*80 + "\n")
            for finding in metadata_findings:
                f.write(f"0x{finding['address']:08X}: {finding['instruction']} - {finding['description']}\n")
    
    print("\n[+] Report written to: event_handler_analysis.txt")

if __name__ == '__main__':
    main()
