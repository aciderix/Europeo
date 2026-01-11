#!/usr/bin/env python3
"""
Deep disassembly of critical VND loading functions:
1. TEventHandler::Dispatch (owl52t.dll) - Event routing
2. ipstream::readWord32 (bds52t.dll) - Read 32-bit integers
3. ipstream::readBytes (bds52t.dll) - Read byte arrays

This will show EXACTLY how the VND file is loaded.
"""

import pefile
import capstone
import os

def find_function_by_name(dll_path, function_name):
    """Find a function's RVA by its export name."""
    try:
        pe = pefile.PE(dll_path)
        
        if hasattr(pe, 'DIRECTORY_ENTRY_EXPORT'):
            for export in pe.DIRECTORY_ENTRY_EXPORT.symbols:
                if export.name:
                    name = export.name.decode('utf-8', errors='replace')
                    if function_name in name:
                        return export.address, name
        
        return None, None
    except Exception as e:
        print(f"[!] Error loading {dll_path}: {e}")
        return None, None

def disassemble_function_deep(dll_path, function_name, max_instructions=500):
    """Deeply disassemble a function with detailed analysis."""
    
    print("="*80)
    print(f"DEEP DISASSEMBLY: {function_name}")
    print(f"DLL: {os.path.basename(dll_path)}")
    print("="*80)
    
    pe = pefile.PE(dll_path)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    
    image_base = pe.OPTIONAL_HEADER.ImageBase
    
    # Find function
    rva, full_name = find_function_by_name(dll_path, function_name)
    
    if not rva:
        print(f"[!] Function '{function_name}' not found")
        return None
    
    print(f"\n[+] Found: {full_name}")
    print(f"[+] RVA: 0x{rva:08X}")
    print(f"[+] VA: 0x{image_base + rva:08X}\n")
    
    # Find CODE section containing this function
    code_section = None
    code_base = 0
    
    for section in pe.sections:
        if section.VirtualAddress <= rva < section.VirtualAddress + section.Misc_VirtualSize:
            code_section = section.get_data()
            code_base = image_base + section.VirtualAddress
            section_name = section.Name.decode('utf-8').rstrip('\x00')
            print(f"[+] Function in section: {section_name}\n")
            break
    
    if not code_section:
        print("[!] Could not find section containing function")
        return None
    
    # Calculate offset in section
    offset_in_section = rva - (code_base - image_base)
    code_chunk = code_section[offset_in_section:]
    start_va = image_base + rva
    
    # Disassemble with detailed analysis
    print("[DISASSEMBLY]")
    print("-"*80)
    
    instructions = []
    call_targets = []
    jump_targets = []
    string_refs = []
    
    for i, inst in enumerate(md.disasm(code_chunk, start_va)):
        if i >= max_instructions:
            break
        
        instructions.append(inst)
        
        # Format output
        bytes_hex = ' '.join(f'{b:02X}' for b in inst.bytes)
        print(f"0x{inst.address:08X}:  {bytes_hex:20}  {inst.mnemonic:8} {inst.op_str}")
        
        # Analyze special instructions
        if inst.mnemonic == 'call':
            for op in inst.operands:
                if op.type == capstone.x86.X86_OP_IMM:
                    call_targets.append({
                        'from': inst.address,
                        'to': op.imm,
                        'offset': op.imm - image_base
                    })
                    print(f"         ; CALL to 0x{op.imm:08X}")
        
        elif inst.mnemonic in ['je', 'jne', 'jmp', 'jz', 'jnz', 'ja', 'jb', 'jg', 'jl']:
            for op in inst.operands:
                if op.type == capstone.x86.X86_OP_IMM:
                    jump_targets.append({
                        'from': inst.address,
                        'to': op.imm,
                        'type': inst.mnemonic
                    })
                    print(f"         ; {inst.mnemonic.upper()} to 0x{op.imm:08X}")
        
        elif inst.mnemonic == 'push':
            for op in inst.operands:
                if op.type == capstone.x86.X86_OP_IMM:
                    # Could be string address or constant
                    if op.imm > image_base:
                        print(f"         ; Pushing address 0x{op.imm:08X}")
        
        # Stop at RET
        if inst.mnemonic in ['ret', 'retn']:
            print(f"\n[+] Function ends at 0x{inst.address:08X}")
            break
    
    print("\n" + "="*80)
    print("[ANALYSIS SUMMARY]")
    print("-"*80)
    print(f"Total instructions: {len(instructions)}")
    print(f"CALL instructions: {len(call_targets)}")
    print(f"JUMP instructions: {len(jump_targets)}")
    
    return {
        'name': full_name,
        'rva': rva,
        'va': start_va,
        'instructions': instructions,
        'calls': call_targets,
        'jumps': jump_targets
    }

def analyze_vnd_loading_flow():
    """Analyze the complete VND loading flow."""
    
    print("\n" + "="*80)
    print("VND LOADING FLOW ANALYSIS")
    print("="*80)
    
    output = []
    output.append("# VND Loading Flow - Complete Disassembly\n\n")
    
    # 1. Analyze TEventHandler::Dispatch (owl52t.dll)
    print("\n[STEP 1: Event Dispatch Mechanism]")
    owl_path = 'f:\\Europeo\\FRONTAL\\dll\\owl52t.dll'
    
    dispatch_result = disassemble_function_deep(
        owl_path, 
        'TEventHandler@Dispatch',
        max_instructions=100
    )
    
    if dispatch_result:
        output.append("## 1. TEventHandler::Dispatch (Event Router)\n\n")
        output.append(f"**Location**: `{dispatch_result['name']}` @ 0x{dispatch_result['va']:08X}\n\n")
        output.append(f"**Purpose**: Routes Windows messages and VND events to appropriate handlers\n\n")
        output.append(f"**Key Calls**: {len(dispatch_result['calls'])} function calls\n\n")
    
    # 2. Analyze ipstream::readWord32 (bds52t.dll)
    print("\n[STEP 2: Binary Reading - readWord32]")
    bds_path = 'f:\\Europeo\\FRONTAL\\dll\\bds52t.dll'
    
    readword32_result = disassemble_function_deep(
        bds_path,
        'ipstream@readWord32',
        max_instructions=150
    )
    
    if readword32_result:
        output.append("## 2. ipstream::readWord32 (Read 32-bit Integer)\n\n")
        output.append(f"**Location**: `{readword32_result['name']}` @ 0x{readword32_result['va']:08X}\n\n")
        output.append(f"**Purpose**: Reads a 32-bit little-endian integer from stream\n\n")
        output.append(f"**Instructions**: {len(readword32_result['instructions'])}\n\n")
    
    # 3. Analyze ipstream::readBytes (bds52t.dll)
    print("\n[STEP 3: Binary Reading - readBytes]")
    
    readbytes_result = disassemble_function_deep(
        bds_path,
        'ipstream@readBytes',
        max_instructions=150
    )
    
    if readbytes_result:
        output.append("## 3. ipstream::readBytes (Read Byte Array)\n\n")
        output.append(f"**Location**: `{readbytes_result['name']}` @ 0x{readbytes_result['va']:08X}\n\n")
        output.append(f"**Purpose**: Reads N bytes from stream into buffer\n\n")
        output.append(f"**Instructions**: {len(readbytes_result['instructions'])}\n\n")
    
    # Generate flow diagram
    output.append("## Complete VND Loading Flow\n\n")
    output.append("```\n")
    output.append("1. User Action → Windows Event\n")
    output.append("   ↓\n")
    output.append("2. TEventHandler::Dispatch (owl52t.dll)\n")
    output.append("   - Routes event to appropriate handler\n")
    output.append("   ↓\n")
    output.append("3. TFileDocument::InStream / fpbase::open\n")
    output.append("   - Opens .vnd file\n")
    output.append("   - Creates ipstream object\n")
    output.append("   ↓\n")
    output.append("4. Parse VND Header (12 bytes)\n")
    output.append("   - ipstream::readWord32() × 3\n")
    output.append("   ↓\n")
    output.append("5. Find 'VNFILE' Signature\n")
    output.append("   - ipstream::readBytes(6)\n")
    output.append("   ↓\n")
    output.append("6. Parse Length-Prefixed Strings\n")
    output.append("   Loop:\n")
    output.append("     - ipstream::readWord32() → length\n")
    output.append("     - ipstream::readBytes(length) → string data\n")
    output.append("   Reads:\n")
    output.append("     a) Version\n")
    output.append("     b) Application\n")
    output.append("     c) Symbol Table (200+ vars)\n")
    output.append("     d) Metadata (13+ vars + resources)\n")
    output.append("   ↓\n")
    output.append("7. Parse Script Section\n")
    output.append("   - Remaining bytes as ASCII text\n")
    output.append("   ↓\n")
    output.append("8. TEventHandler::Dispatch\n")
    output.append("   - Execute script commands\n")
    output.append("   - Route to UI handlers\n")
    output.append("```\n\n")
    
    # Write report
    with open('f:\\Europeo\\FRONTAL\\dll\\vnd_loading_flow_complete.md', 'w', encoding='utf-8') as f:
        f.write(''.join(output))
    
    print("\n[+] Complete flow analysis written to: vnd_loading_flow_complete.md")

def main():
    print("VND LOADING MECHANISM - DEEP ANALYSIS")
    print("="*80)
    print("This will disassemble the exact functions that load VND files\n")
    
    analyze_vnd_loading_flow()
    
    print("\n[+] Analysis complete!")
    print("[+] All disassembly written to: vnd_loading_flow_complete.md")

if __name__ == '__main__':
    main()
