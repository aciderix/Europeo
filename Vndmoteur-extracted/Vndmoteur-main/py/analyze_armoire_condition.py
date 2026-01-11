import struct

vnd_path = r'f:\Europeo\FRONTAL\dll\couleurs1.vnd'
with open(vnd_path, 'rb') as f:
    data = f.read()

script_start = 4726
script_data = data[script_start:]

# Chercher armoire3.bmp
target = b"armoire3.bmp"
pos = script_data.find(target)

if pos >= 0:
    print(f"armoire3.bmp trouvé à script offset +{pos} (Fichier 0x{script_start+pos:X})")
    
    # Extraire 100 bytes AVANT pour voir la condition
    start = max(0, pos - 100)
    chunk = script_data[start:pos]
    
    print("\nANALYSE BINAIRE AVANT 'armoire3.bmp':")
    print("="*60)
    
    for i in range(0, len(chunk), 16):
        sub = chunk[i:i+16]
        hex_s = ' '.join(f"{b:02X}" for b in sub)
        asc_s = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in sub)
        print(f"{(start+i):04X}: {hex_s:<48} {asc_s}")

    # Chercher la valeur 21 (0x15) dans ces bytes
    # Cela indiquerait "IF VAR(21) ..."
    
    print("\nRecherche de l'ID 21 (0x15):")
    p15 = chunk.find(b'\x15')
    if p15 >= 0:
        print(f"Trouvé 0x15 à l'offset relatif -{len(chunk)-p15}")
        # Montrer le contexte immédiat
        ctx = chunk[max(0, p15-5):min(len(chunk), p15+5)]
        print(f"Contexte: {ctx.hex(' ')}")
    else:
        print("0x15 non trouvé juste avant.")

else:
    print("armoire3.bmp non trouvé")
