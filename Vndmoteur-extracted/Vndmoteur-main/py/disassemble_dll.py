import pefile
import capstone

dll_path = r'f:\Europeo\FRONTAL\dll\vndllapi.dll'
output_file = r'f:\Europeo\FRONTAL\dll\vndllapi_disassembly.txt'

pe = pefile.PE(dll_path)

with open(output_file, 'w', encoding='utf-8') as f:
    f.write("="*80 + "\n")
    f.write("DETAILED DISASSEMBLY: vndllapi.dll\n")
    f.write("="*80 + "\n")
    
    # Get the code section
    code_section = None
    for section in pe.sections:
        if b'CODE' in section.Name:
            code_section = section
            break
    
    if code_section:
        f.write(f"\n[CODE SECTION ANALYSIS]\n")
        f.write(f"Section Name: {code_section.Name.decode().rstrip(chr(0))}\n")
        f.write(f"Virtual Address: {hex(code_section.VirtualAddress)}\n")
        f.write(f"Virtual Size: {hex(code_section.Misc_VirtualSize)}\n")
        f.write(f"Raw Size: {hex(code_section.SizeOfRawData)}\n")
        
        # Get code bytes
        code_data = code_section.get_data()
        code_base = pe.OPTIONAL_HEADER.ImageBase + code_section.VirtualAddress
        
        # Initialize disassembler
        md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
        
        # Disassemble exported functions
        f.write("\n[DISASSEMBLED EXPORTED FUNCTIONS]\n\n")
        
        if hasattr(pe, 'DIRECTORY_ENTRY_EXPORT'):
            for exp in pe.DIRECTORY_ENTRY_EXPORT.symbols:
                name = exp.name.decode() if exp.name else f"Ordinal_{exp.ordinal}"
                rva = exp.address
                
                # Check if address is in code section
                if code_section.VirtualAddress <= rva < code_section.VirtualAddress + code_section.Misc_VirtualSize:
                    offset = rva - code_section.VirtualAddress
                    
                    f.write(f"\n{'='*60}\n")
                    f.write(f"Function: {name} (Ordinal: {exp.ordinal})\n")
                    f.write(f"RVA: {hex(rva)} | Offset in CODE: {hex(offset)}\n")
                    f.write(f"{'='*60}\n\n")
                    
                    # Disassemble up to 200 instructions or until return
                    count = 0
                    for i in md.disasm(code_data[offset:offset+1000], code_base + offset):
                        f.write(f"  {hex(i.address)}:\t{i.mnemonic}\t{i.op_str}\n")
                        count += 1
                        
                        # Stop at ret or retn
                        if i.mnemonic in ['ret', 'retn']:
                            break
                        if count > 200:
                            f.write("  ... (truncated)\n")
                            break
        
        # Also disassemble the entire CODE section for reference
        f.write("\n\n" + "="*80 + "\n")
        f.write("[COMPLETE CODE SECTION DISASSEMBLY]\n")
        f.write("="*80 + "\n\n")
        
        for i in md.disasm(code_data, code_base):
            f.write(f"{hex(i.address)}:\t{i.mnemonic}\t{i.op_str}\n")
    
    pe.close()
    f.write("\n" + "="*80 + "\n")
    f.write("DISASSEMBLY COMPLETE\n")
    f.write("="*80 + "\n")

print(f"Disassembly saved to: {output_file}")
