#!/usr/bin/env python3
"""
Decompilation and analysis of VND parser functions from europeo.exe and DLLs.
This script identifies and decompiles the functions responsible for parsing 
.vnd file binary structures.
"""

import pefile
import capstone
import struct
import os
from pathlib import Path

class VNDParserDecompiler:
    def __init__(self, exe_path):
        self.exe_path = exe_path
        self.pe = pefile.PE(exe_path)
        self.md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
        self.md.detail = True
        
        # Extracted data
        self.code_section = None
        self.code_base = 0
        self.image_base = self.pe.OPTIONAL_HEADER.ImageBase
        
        # Results
        self.vnd_functions = []
        self.file_operations = []
        
    def find_code_section(self):
        """Find the CODE section containing executable code."""
        for section in self.pe.sections:
            section_name = section.Name.decode('utf-8').rstrip('\x00')
            if section_name.upper() == 'CODE' or section.Characteristics & 0x20000000:
                self.code_section = section.get_data()
                self.code_base = self.image_base + section.VirtualAddress
                print(f"[+] Found CODE section: {section_name}")
                print(f"    Virtual Address: 0x{section.VirtualAddress:08X}")
                print(f"    Size: {len(self.code_section)} bytes")
                return True
        return False
    
    def find_string_references(self, search_string):
        """Find all references to a specific string in the code."""
        references = []
        
        # First find the string in ALL sections (not just data)
        string_addresses = []
        for section in self.pe.sections:
            data = section.get_data()
            offset = 0
            search_bytes = search_string.encode('ascii')
            
            while True:
                pos = data.find(search_bytes, offset)
                if pos == -1:
                    break
                
                string_rva = section.VirtualAddress + pos
                string_va = self.image_base + string_rva
                string_addresses.append((string_va, string_rva))
                section_name = section.Name.decode('utf-8').rstrip('\x00')
                print(f"[+] Found string '{search_string}' at VA: 0x{string_va:08X} (RVA: 0x{string_rva:08X}, Section: {section_name})")
                offset = pos + 1
        
        # Now find code that references these addresses (both VA and RVA)
        if not self.code_section:
            return references
        
        print(f"\n[*] Searching for references to string addresses in CODE section...")
        
        # We need to check for indirect references too
        for instruction in self.md.disasm(self.code_section, self.code_base):
            # Look for MOV/PUSH/LEA with immediate values
            if instruction.mnemonic in ['mov', 'push', 'lea', 'cmp', 'add', 'sub']:
                for op in instruction.operands:
                    if op.type == capstone.x86.X86_OP_IMM:
                        # Check both VA and RVA
                        for string_va, string_rva in string_addresses:
                            if op.imm == string_va or op.imm == string_rva:
                                references.append({
                                    'address': instruction.address,
                                    'instruction': f"{instruction.mnemonic} {instruction.op_str}",
                                    'string_address': op.imm,
                                    'string': search_string
                                })
                                print(f"    [!] Reference at 0x{instruction.address:08X}: {instruction.mnemonic} {instruction.op_str}")
            
            # Also check memory operands that might reference the string
            if instruction.mnemonic in ['mov', 'lea', 'cmp']:
                for op in instruction.operands:
                    if op.type == capstone.x86.X86_OP_MEM:
                        # Check displacement
                        if op.mem.disp != 0:
                            for string_va, string_rva in string_addresses:
                                # Check if displacement could be relative to the string
                                if abs(op.mem.disp - string_va) < 0x1000 or abs(op.mem.disp - string_rva) < 0x1000:
                                    references.append({
                                        'address': instruction.address,
                                        'instruction': f"{instruction.mnemonic} {instruction.op_str}",
                                        'string_address': op.mem.disp,
                                        'string': search_string,
                                        'type': 'memory_reference'
                                    })
                                    print(f"    [~] Possible memory reference at 0x{instruction.address:08X}: {instruction.mnemonic} {instruction.op_str}")
        
        return references
    
    def find_file_operations(self):
        """Find calls to file I/O functions (CreateFileA, ReadFile, fopen, fread)."""
        file_funcs = ['CreateFileA', 'ReadFile', 'fopen', 'fread', 'GetFileSize']
        
        # Find import addresses
        import_addresses = {}
        if hasattr(self.pe, 'DIRECTORY_ENTRY_IMPORT'):
            for entry in self.pe.DIRECTORY_ENTRY_IMPORT:
                dll_name = entry.dll.decode('utf-8')
                for imp in entry.imports:
                    if imp.name:
                        func_name = imp.name.decode('utf-8')
                        if func_name in file_funcs:
                            import_addresses[func_name] = imp.address + self.image_base
                            print(f"[+] Found import: {func_name} at 0x{imp.address + self.image_base:08X}")
        
        # Find CALL instructions to these addresses
        if not self.code_section:
            return []
        
        calls = []
        for instruction in self.md.disasm(self.code_section, self.code_base):
            if instruction.mnemonic == 'call':
                for op in instruction.operands:
                    if op.type == capstone.x86.X86_OP_IMM:
                        for func_name, addr in import_addresses.items():
                            if op.imm == addr:
                                calls.append({
                                    'address': instruction.address,
                                    'function': func_name,
                                    'target': op.imm
                                })
                                print(f"    CALL to {func_name} at 0x{instruction.address:08X}")
        
        self.file_operations = calls
        return calls
    
    def disassemble_function(self, start_address, max_instructions=200):
        """Disassemble a function starting from a given address."""
        # Calculate offset in code section
        offset = start_address - self.code_base
        if offset < 0 or offset >= len(self.code_section):
            print(f"[!] Address 0x{start_address:08X} is outside CODE section")
            return []
        
        instructions = []
        code = self.code_section[offset:]
        
        # Track control flow
        current_addr = start_address
        visited = set()
        to_visit = [start_address]
        
        print(f"\n[*] Disassembling function at 0x{start_address:08X}")
        print("=" * 80)
        
        count = 0
        for instruction in self.md.disasm(code, start_address):
            if count >= max_instructions:
                break
            
            instructions.append(instruction)
            print(f"0x{instruction.address:08X}:  {instruction.mnemonic:8} {instruction.op_str}")
            
            # Stop at RET
            if instruction.mnemonic in ['ret', 'retn']:
                break
            
            count += 1
        
        print("=" * 80)
        return instructions
    
    def analyze_vnd_structure_parsing(self, function_instructions):
        """Analyze instructions to identify VND structure fields being read."""
        structure_reads = []
        
        for i, inst in enumerate(function_instructions):
            # Look for patterns like:
            # mov eax, [ebp+offset]  - reading from stack/locals
            # mov xxx, [eax+offset]   - reading from structure
            
            if inst.mnemonic == 'mov' and len(inst.operands) >= 2:
                src = inst.operands[1]
                
                # Memory operand with displacement = structure field access
                if src.type == capstone.x86.X86_OP_MEM and src.mem.disp != 0:
                    structure_reads.append({
                        'address': inst.address,
                        'instruction': f"{inst.mnemonic} {inst.op_str}",
                        'base_reg': inst.reg_name(src.mem.base) if src.mem.base != 0 else None,
                        'offset': src.mem.disp,
                        'size': src.size
                    })
        
        return structure_reads
    
    def generate_report(self, output_file):
        """Generate a detailed analysis report."""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("VND PARSER DECOMPILATION REPORT\n")
            f.write(f"Analyzed file: {self.exe_path}\n")
            f.write("=" * 80 + "\n\n")
            
            f.write("## VNFILE String References\n")
            f.write("-" * 80 + "\n")
            vnfile_refs = self.find_string_references("VNFILE")
            if vnfile_refs:
                for ref in vnfile_refs:
                    f.write(f"Address: 0x{ref['address']:08X}\n")
                    f.write(f"  Instruction: {ref['instruction']}\n")
                    f.write(f"  String Address: 0x{ref['string_address']:08X}\n\n")
            else:
                f.write("No direct references found.\n\n")
            
            f.write("\n## File I/O Operations\n")
            f.write("-" * 80 + "\n")
            for op in self.file_operations:
                f.write(f"Address: 0x{op['address']:08X}\n")
                f.write(f"  Function: {op['function']}\n")
                f.write(f"  Target: 0x{op['target']:08X}\n\n")
            
            f.write("\n## Decompiled Functions\n")
            f.write("-" * 80 + "\n")
            for func in self.vnd_functions:
                f.write(f"\nFunction at 0x{func['address']:08X}:\n")
                for inst in func['instructions']:
                    f.write(f"  0x{inst.address:08X}:  {inst.mnemonic:8} {inst.op_str}\n")
                
                if func.get('structure_reads'):
                    f.write("\n  Structure accesses detected:\n")
                    for read in func['structure_reads']:
                        f.write(f"    Offset +0x{read['offset']:X} ({read['size']} bytes) at 0x{read['address']:08X}\n")
            
        print(f"\n[+] Report generated: {output_file}")


def main():
    print("VND Parser Decompiler")
    print("=" * 80)
    
    # Analyze europeo.exe
    exe_path = r'f:\Europeo\FRONTAL\dll\europeo.exe'
    if not os.path.exists(exe_path):
        print(f"[!] File not found: {exe_path}")
        return
    
    print(f"\n[*] Analyzing {exe_path}\n")
    decompiler = VNDParserDecompiler(exe_path)
    
    # Find code section
    if not decompiler.find_code_section():
        print("[!] Could not find CODE section")
        return
    
    print("\n[*] Searching for VNFILE string references...")
    vnfile_refs = decompiler.find_string_references("VNFILE")
    
    print("\n[*] Searching for file I/O operations...")
    decompiler.find_file_operations()
    
    # If we found VNFILE references, disassemble the surrounding functions
    if vnfile_refs:
        print("\n[*] Disassembling functions that reference VNFILE...")
        for ref in vnfile_refs[:3]:  # Limit to first 3
            # Try to find function start by looking backwards for push ebp; mov ebp, esp
            func_start = ref['address']
            instructions = decompiler.disassemble_function(func_start, max_instructions=100)
            
            structure_reads = decompiler.analyze_vnd_structure_parsing(instructions)
            
            decompiler.vnd_functions.append({
                'address': func_start,
                'instructions': instructions,
                'structure_reads': structure_reads
            })
    
    # Also disassemble functions that call file operations
    if decompiler.file_operations:
        print("\n[*] Analyzing functions with file I/O operations...")
        for op in decompiler.file_operations[:5]:  # Limit to first 5
            func_start = op['address'] - 0x20  # Approximate function start
            instructions = decompiler.disassemble_function(func_start, max_instructions=150)
            
            structure_reads = decompiler.analyze_vnd_structure_parsing(instructions)
            
            decompiler.vnd_functions.append({
                'address': func_start,
                'instructions': instructions,
                'structure_reads': structure_reads,
                'file_operation': op
            })
    
    # Generate report
    output_file = r'f:\Europeo\FRONTAL\dll\vnd_parser_analysis.txt'
    decompiler.generate_report(output_file)
    
    print("\n[+] Analysis complete!")


if __name__ == '__main__':
    main()
