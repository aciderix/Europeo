import pefile
import json

dll_path = r'f:\Europeo\FRONTAL\dll\vnresmod.dll'
pe = pefile.PE(dll_path)

print("="*80)
print("DLL ANALYSIS: vnresmod.dll")
print("="*80)

# Basic Info
print("\n[BASIC INFORMATION]")
print(f"DLL Name: {dll_path}")
print(f"Machine Type: {hex(pe.FILE_HEADER.Machine)}")
print(f"Number of Sections: {pe.FILE_HEADER.NumberOfSections}")
print(f"Time Date Stamp: {pe.FILE_HEADER.TimeDateStamp}")
print(f"Entry Point: {hex(pe.OPTIONAL_HEADER.AddressOfEntryPoint)}")
print(f"Image Base: {hex(pe.OPTIONAL_HEADER.ImageBase)}")
print(f"Size of Image: {hex(pe.OPTIONAL_HEADER.SizeOfImage)} ({pe.OPTIONAL_HEADER.SizeOfImage} bytes)")

# Sections
print("\n[SECTIONS]")
for section in pe.sections:
    print(f"  {section.Name.decode().rstrip(chr(0)):10} - Virtual Size: {hex(section.Misc_VirtualSize):10} - Raw Size: {hex(section.SizeOfRawData):10}")

# Exports
print("\n[EXPORTED FUNCTIONS]")
if hasattr(pe, 'DIRECTORY_ENTRY_EXPORT'):
    print(f"Total exports: {len(pe.DIRECTORY_ENTRY_EXPORT.symbols)}\n")
    for exp in pe.DIRECTORY_ENTRY_EXPORT.symbols:
        name = exp.name.decode() if exp.name else f"Ordinal_{exp.ordinal}"
        print(f"  {exp.ordinal:4} - {hex(exp.address):10} - {name}")
else:
    print("  No exports found")

# Imports
print("\n[IMPORTED DLLS AND FUNCTIONS]")
if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT'):
    for entry in pe.DIRECTORY_ENTRY_IMPORT:
        print(f"\n  DLL: {entry.dll.decode()}")
        for imp in entry.imports[:30]:
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
data = open(dll_path, 'rb').read()
strings = []
current_string = b""
for byte in data:
    if 32 <= byte <= 126:
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
    for s in interesting_strings[:100]:
        print(f"  {s}")

pe.close()
