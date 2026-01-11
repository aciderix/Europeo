import pefile
import json

exe_path = r'f:\Europeo\FRONTAL\dll\europeo.exe'
pe = pefile.PE(exe_path)

print("="*80)
print("EXE ANALYSIS: europeo.exe")
print("="*80)

# Basic Info
print("\n[BASIC INFORMATION]")
print(f"EXE Name: {exe_path}")
print(f"Machine Type: {hex(pe.FILE_HEADER.Machine)}")
print(f"Number of Sections: {pe.FILE_HEADER.NumberOfSections}")
print(f"Time Date Stamp: {pe.FILE_HEADER.TimeDateStamp}")
print(f"Entry Point: {hex(pe.OPTIONAL_HEADER.AddressOfEntryPoint)}")
print(f"Image Base: {hex(pe.OPTIONAL_HEADER.ImageBase)}")
print(f"Subsystem: {pe.OPTIONAL_HEADER.Subsystem} ({'GUI' if pe.OPTIONAL_HEADER.Subsystem == 2 else 'Console' if pe.OPTIONAL_HEADER.Subsystem == 3 else 'Other'})")

# Sections
print("\n[SECTIONS]")
for section in pe.sections:
    print(f"  {section.Name.decode().rstrip(chr(0)):10} - Virtual Size: {hex(section.Misc_VirtualSize):10} - Raw Size: {hex(section.SizeOfRawData):10}")

# Exports (if any)
print("\n[EXPORTED FUNCTIONS]")
if hasattr(pe, 'DIRECTORY_ENTRY_EXPORT'):
    for exp in pe.DIRECTORY_ENTRY_EXPORT.symbols:
        name = exp.name.decode() if exp.name else f"Ordinal_{exp.ordinal}"
        print(f"  {exp.ordinal:4} - {hex(exp.address):10} - {name}")
else:
    print("  No exports (normal for an EXE)")

# Imports
print("\n[IMPORTED DLLS AND FUNCTIONS]")
if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT'):
    for entry in pe.DIRECTORY_ENTRY_IMPORT:
        print(f"\n  DLL: {entry.dll.decode()}")
        for imp in entry.imports[:30]:  # Limit to first 30
            if imp.name:
                print(f"    - {imp.name.decode()}")
            else:
                print(f"    - Ordinal: {imp.ordinal}")
        if len(entry.imports) > 30:
            print(f"    ... and {len(entry.imports) - 30} more functions")
else:
    print("  No imports found")

# Resources
print("\n[RESOURCES]")
if hasattr(pe, 'DIRECTORY_ENTRY_RESOURCE'):
    print("  Resource directory exists")
    for resource_type in pe.DIRECTORY_ENTRY_RESOURCE.entries:
        if resource_type.name is not None:
            name = f"{resource_type.name}"
        else:
            name = f"{pefile.RESOURCE_TYPE.get(resource_type.struct.Id, 'Unknown')}"
        print(f"  Type: {name}")
else:
    print("  No resources found")

# Strings
print("\n[EXTRACTING STRINGS...]")
data = open(exe_path, 'rb').read()
strings = []
current_string = b""
for byte in data:
    if 32 <= byte <= 126:  # Printable ASCII
        current_string += bytes([byte])
    else:
        if len(current_string) >= 4:
            try:
                strings.append(current_string.decode('ascii'))
            except:
                pass
        current_string = b""

interesting_strings = [s for s in strings if len(s) >= 4]
print(f"Found {len(interesting_strings)} strings")
if len(interesting_strings) > 0:
    print("\n[INTERESTING STRINGS] (sample):")
    for s in interesting_strings[:100]:  # Show first 100
        print(f"  {s}")

pe.close()
