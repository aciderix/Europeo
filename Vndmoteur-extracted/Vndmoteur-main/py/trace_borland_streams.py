#!/usr/bin/env python3
"""
Trace and decompile Borland stream function calls to understand VND parsing
"""

import pefile
import capstone

def trace_borland_streams():
    exe_path = 'f:\\Europeo\\FRONTAL\\dll\\europeo.exe'
    
    print("="*80)
    print("BORLAND STREAM I/O ANALYSIS FOR VND PARSING")
    print("="*80)
    
    pe = pefile.PE(exe_path)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    
    image_base = pe.OPTIONAL_HEADER.ImageBase
    
    # Find critical Borland stream functions
    stream_imports = {}
    critical_funcs = [
        'fpbase@open',
        'ipstream@readWord32',
        'ipstream@readBytes', 
        'ipstream@readWord',
        'ifstream@$bctr',
        '$brsh$qr8ipstreamr6string',  # operator>> for string
        'filebuf@'
    ]
    
    print("\n[*] Finding Borland stream imports...")
    if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT'):
        for entry in pe.DIRECTORY_ENTRY_IMPORT:
            dll_name = entry.dll.decode('utf-8')
            for imp in entry.imports:
                if imp.name:
                    func_name = imp.name.decode('utf-8')
                    for critical in critical_funcs:
                        if critical in func_name:
                            va = imp.address + image_base
                            stream_imports[func_name] = va
                            print(f"  {func_name:50} at 0x{va:08X}")
    
    # Find CODE section
    code_section = None
    code_base = 0
    for section in pe.sections:
        if section.Name.decode('utf-8').rstrip('\x00').upper() == 'CODE':
            code_section = section.get_data()
            code_base = image_base + section.VirtualAddress
            break
    
    if not code_section:
        print("[!] CODE section not found")
        return
    
    # Find all CALLs to these functions
    print("\n[*] Finding function calls...")
    stream_calls = []
    
    for inst in md.disasm(code_section, code_base):
        if inst.mnemonic == 'call':
            for op in inst.operands:
                if op.type == capstone.x86.X86_OP_IMM:
                    for func_name, func_addr in stream_imports.items():
                        if op.imm == func_addr:
                            stream_calls.append({
                                'addr': inst.address,
                                'func': func_name,
                                'offset': inst.address - code_base
                            })
                            print(f"  CALL {func_name} at 0x{inst.address:08X}")
    
    print(f"\n[+] Found {len(stream_calls)} calls to stream functions")
    
    # Disassemble context around each call
    print("\n[*] Disassembling context around stream calls...")
    
    output = []
    output.append("="*80)
    output.append("BORLAND STREAM FUNCTION USAGE ANALYSIS")
    output.append("="*80)
    output.append("")
    
    for call in stream_calls[:30]:  # First 30 calls
        output.append(f"\nFunction: {call['func']}")
        output.append(f"Called at: 0x{call['addr']:08X}")
        output.append("-" * 80)
        
        # Get 15 instructions before and 15 after
        start_offset = max(0, call['offset'] - 60)
        start_addr = code_base + start_offset
        
        code_chunk = code_section[start_offset:start_offset + 300]
        
        count = 0
        found = False
        for inst in md.disasm(code_chunk, start_addr):
            prefix = "  "
            if inst.address == call['addr']:
                prefix = ">>>"
                found = True
            
            line = f"{prefix} 0x{inst.address:08X}:  {inst.mnemonic:10} {inst.op_str}"
            output.append(line)
            print(line)
            
            # Annotate interesting patterns
            if inst.mnemonic == 'push' and len(inst.operands) > 0:
                op = inst.operands[0]
                if op.type == capstone.x86.X86_OP_IMM:
                    if op.imm < 0x10000:  # Likely a size or count
                        output.append(f"         ; Possible size/count parameter: {op.imm} (0x{op.imm:X})")
                    elif op.imm > image_base:  # Likely an address
                        output.append(f"         ; Possible address parameter: 0x{op.imm:08X}")
            
            count += 1
            if found and count > 20:
                break
        
        output.append("")
    
    # Write to file
    with open('f:\\Europeo\\FRONTAL\\dll\\borland_stream_analysis.txt', 'w') as f:
        f.write('\n'.join(output))
    
    print(f"\n[+] Detailed analysis written to: borland_stream_analysis.txt")
    
    # Now let's try to find VND header parsing pattern
    print("\n[*] Searching for VND header parsing pattern...")
    print("   (Looking for: readWord32, readBytes pattern with VNFILE check)")
    
    # Pattern: readWord32 (length) -> readBytes (string data)
    for i in range(len(stream_calls) - 1):
        call1 = stream_calls[i]
        call2 = stream_calls[i + 1]
        
        # If readWord32/readWord followed by readBytes within 100 bytes
        if ('readWord32' in call1['func'] or 'readWord' in call1['func']) and \
           'readBytes' in call2['func'] and \
           abs(call2['addr'] - call1['addr']) < 100:
            
            print(f"\n  [!] Potential length-prefixed read pattern:")
            print(f"      readWord at 0x{call1['addr']:08X}")
            print(f"      readBytes at 0x{call2['addr']:08X}")
            print(f"      Distance: {call2['addr'] - call1['addr']} bytes")
    
    return stream_calls

if __name__ == '__main__':
    calls = trace_borland_streams()
