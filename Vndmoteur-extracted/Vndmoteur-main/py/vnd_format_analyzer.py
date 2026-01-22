#!/usr/bin/env python3
"""
Complete VND binary format reverse engineering through direct file analysis
"""

import struct
import os

class VNDFormatAnalyzer:
    def __init__(self, vnd_path):
        self.vnd_path = vnd_path
        with open(vnd_path, 'rb') as f:
            self.data = f.read()
        self.offset = 0
        self.structures = []
    
    def read_u32(self):
        """Read unsigned 32-bit little-endian integer."""
        if self.offset + 4 > len(self.data):
            return None
        val = struct.unpack('<I', self.data[self.offset:self.offset+4])[0]
        self.offset += 4
        return val
    
    def read_string(self, length):
        """Read string of given length."""
        if self.offset + length > len(self.data):
            return None
        s = self.data[self.offset:self.offset+length].decode('ascii', errors='replace')
        self.offset += length
        return s
    
    def read_length_prefixed_string(self):
        """Read a length-prefixed string (4-byte length + string data)."""
        length = self.read_u32()
        if length is None or length > 10000:  # Sanity check
            return None
        return self.read_string(length)
    
    def analyze_header(self):
        """Analyze the VND file header."""
        print("="*80)
        print("VND BINARY FORMAT ANALYSIS")
        print(f"File: {os.path.basename(self.vnd_path)}")
        print(f"Size: {len(self.data)} bytes")
        print("="*80)
        
        print("\n[HEADER ANALYSIS]")
        print("-"*80)
        
        # Field 1: Unknown 32-bit value
        field1 = self.read_u32()
        print(f"Offset 0x{0:04X}: {field1:08X} (field 1, could be magic or size)")
        self.structures.append(('u32', 'field1_unknown', field1))
        
        # Field 2: Another 32-bit value
        field2 = self.read_u32()
        print(f"Offset 0x{4:04X}: {field2:08X} (field 2)")
        self.structures.append(('u32', 'field2_unknown', field2))
        
        # Field 3: Yet another
        field3 = self.read_u32()
        print(f"Offset 0x{8:04X}: {field3:08X} (field 3)")
        self.structures.append(('u32', 'field3_unknown', field3))
        
        # Check for VNFILE signature
        vnfile_pos = self.data.find(b'VNFILE')
        if vnfile_pos >= 0:
            print(f"\n[VNFILE SIGNATURE FOUND]")
            print(f"Position: 0x{vnfile_pos:04X} ({vnfile_pos} bytes from start)")
            
            # Jump to VNFILE
            self.offset = vnfile_pos
            signature = self.read_string(6)
            print(f"Signature: '{signature}'")
            self.structures.append(('string6', 'signature', signature))
            
            # After VNFILE: length-prefixed fields
            print("\n[LENGTH-PREFIXED FIELDS]")
            
            # Field 1: Version
            version = self.read_length_prefixed_string()
            if version:
                print(f"Version: '{version}' (length: {len(version)})")
                self.structures.append(('lpstring', 'version', version))
            
            # Field 2: Application name
            app_name = self.read_length_prefixed_string()
            if app_name:
                print(f"Application: '{app_name}' (length: {len(app_name)})")
                self.structures.append(('lpstring', 'application', app_name))
            
            # Field 3: Company/Author
            company = self.read_length_prefixed_string()
            if company:
                print(f"Company: '{company}' (length: {len(company)})")
                self.structures.append(('lpstring', 'company', company))
            
            # Field 4: GUID or unique ID
            guid = self.read_length_prefixed_string()
            if guid:
                print(f"GUID/ID: '{guid}' (length: {len(guid)})")
                self.structures.append(('lpstring', 'guid', guid))
            
            print(f"\nEnd of string fields: offset 0x{self.offset:04X}")
        
        # Analyze the binary section between end of header and start of text
        print("\n[BINARY METADATA SECTION]")
        print("-"*80)
        
        # Find first text command
        text_keywords = [b'if ', b'then', b'addbmp', b'delbmp', b'playavi', b'runprj']
        text_start = len(self.data)
        for kw in text_keywords:
            pos = self.data.find(kw)
            if pos > self.offset and pos < text_start:
                text_start = pos
        
        print(f"Text script starts at: 0x{text_start:04X}")
        print(f"Binary metadata size: {text_start - self.offset} bytes")
        
        metadata_section = self.data[self.offset:text_start]
        
        # Try to parse as series of 32-bit values
        print("\nFirst 32 DWORD values in metadata section:")
        for i in range(min(32, len(metadata_section) // 4)):
            val = struct.unpack('<I', metadata_section[i*4:(i+1)*4])[0]
            binary_str = format(val, '032b')[:16]
            print(f"  [+{i*4:03X}] 0x{val:08X} = {val:12d} (0b{binary_str}...)")
        
        # Analyze byte patterns
        print(f"\nByte value distribution (first 256 bytes):")
        sample = metadata_section[:256]
        null_count = sample.count(b'\x00')
        printable = sum(1 for b in sample if 32 <= b <= 126)
        print(f"  NULL bytes: {null_count} ({null_count*100//len(sample)}%)")
        print(f"  Printable ASCII: {printable} ({printable*100//len(sample)}%)")
        
        # Look for repeating patterns (possible table/array)
        print("\nSearching for repeating patterns (possible arrays/tables)...")
        for size in [4, 8, 12, 16, 20, 24]:
            # Check if metadata could be divided into size-byte chunks
            if len(metadata_section) % size == 0:
                print(f"  Could be {len(metadata_section) // size} entries of {size} bytes each")
        
        return text_start
    
    def analyze_script_section(self, text_start):
        """Analyze the text script section."""
        print("\n[TEXT SCRIPT SECTION]")
        print("-"*80)
        
        script_data = self.data[text_start:]
        script_text = script_data.decode('ascii', errors='replace')
        
        # Count commands
        commands = {}
        for cmd in ['if ', 'then', 'else', 'addbmp', 'delbmp', 'playavi', 'runprj', 
                    'playtext', 'setvar', 'getvar']:
            count = script_text.count(cmd)
            if count > 0:
                commands[cmd] = count
        
        print(f"Script size: {len(script_data)} bytes")
        print(f"Commands found:")
        for cmd, count in sorted(commands.items(), key=lambda x: -x[1]):
            print(f"  {cmd:15} : {count}")
        
        # Show first few lines
        print(f"\nFirst 500 characters of script:")
        print(script_text[:500])
    
    def generate_c_struct(self):
        """Generate C struct definition based on analysis."""
        print("\n" + "="*80)
        print("C STRUCTURE DEFINITION")
        print("="*80)
        
        print("""
// VND File Format Structure
typedef struct {
    uint32_t field1;           // Unknown, possibly magic or file size
    uint32_t field2;           // Unknown
    uint32_t field3;           // Unknown
    
    // Gap of unknown data until VNFILE signature
    
    char signature[6];         // "VNFILE"
    
    // Length-prefixed strings (4-byte length + data)
    uint32_t version_length;
    char version[version_length];
    
    uint32_t application_length;
    char application[application_length];
    
    uint32_t company_length;
    char company[company_length];
    
    uint32_t guid_length;
    char guid[guid_length];
    
    // Binary metadata section (structure unknown)
    uint8_t metadata[???];
    
    // Text script section (null-terminated or extends to EOF)
    char script[???];
} VNDFile;

// Python parsing code:
def parse_vnd(data):
    offset = 0
    
    # Read header fields
    field1, field2, field3 = struct.unpack('<III', data[offset:offset+12])
    offset += 12
    
    # Find VNFILE
    vnfile_pos = data.find(b'VNFILE', offset)
    offset = vnfile_pos + 6
    
    # Read length-prefixed strings
    def read_lpstring():
        nonlocal offset
        length = struct.unpack('<I', data[offset:offset+4])[0]
        offset += 4
        s = data[offset:offset+length].decode('ascii')
        offset += length
        return s
    
    version = read_lpstring()
    application = read_lpstring()
    company = read_lpstring()
    guid = read_lpstring()
    
    # Rest is metadata + script
    remaining = data[offset:]
    
    return {
        'version': version,
        'application': application,
        'company': company,
        'guid': guid,
        'metadata_and_script': remaining
    }
""")

def main():
    vnd_path = 'f:\\Europeo\\FRONTAL\\dll\\couleurs1.vnd'
    
    analyzer = VNDFormatAnalyzer(vnd_path)
    text_start = analyzer.analyze_header()
    analyzer.analyze_script_section(text_start)
    analyzer.generate_c_struct()
    
    print("\n" + "="*80)
    print("[+] Analysis complete!")
    print("="*80)

if __name__ == '__main__':
    main()
