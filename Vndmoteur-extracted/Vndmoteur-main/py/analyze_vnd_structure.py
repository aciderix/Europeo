import struct

vnd_path = r'f:\Europeo\FRONTAL\dll\couleurs1.vnd'

with open(vnd_path, 'rb') as f:
    data = f.read()

print("="*80)
print("ANALYSE DÉTAILLÉE DE LA STRUCTURE VND")
print("="*80)

# Analyser le header
print("\n[SECTION 1: HEADER BINAIRE]")
print("-" * 40)

offset = 0

# Peut-être un magic number ou taille
first_bytes = struct.unpack('<I', data[0:4])[0]
print(f"Offset 0x00: {first_bytes:08X} (peut-être taille ou magic)")

offset = 4

# Chercher VNFILE
vnfile_pos = data.find(b'VNFILE')
if vnfile_pos > 0:
    print(f"\nSignature 'VNFILE' trouvée à offset: {vnfile_pos} (0x{vnfile_pos:X})")
    
    # Analyser autour
    print("\nAnalyse du header structuré:")
    offset = vnfile_pos
    
    # Lire VNFILE
    signature = data[offset:offset+6].decode('ascii')
    print(f"  Signature: {signature}")
    offset += 6
    
    # Length-prefixed strings pattern
    # Format probable: [4 bytes length][string data]
    
    # Lire version
    if offset + 4 <= len(data):
        length = struct.unpack('<I', data[offset:offset+4])[0]
        print(f"  Version length: {length}")
        offset += 4
        if length < 100:  # Sanity check
            version = data[offset:offset+length].decode('ascii', errors='ignore')
            print(f"  Version: '{version}'")
            offset += length
    
    # Lire app name
    if offset + 4 <= len(data):
        length = struct.unpack('<I', data[offset:offset+4])[0]
        print(f"  App name length: {length}")
        offset += 4
        if length < 100:
            appname = data[offset:offset+length].decode('ascii', errors='ignore')
            print(f"  App name: '{appname}'")
            offset += length
    
    # Lire company
    if offset + 4 <= len(data):
        length = struct.unpack('<I', data[offset:offset+4])[0]
        print(f"  Company length: {length}")
        offset += 4
        if length < 100:
            company = data[offset:offset+length].decode('ascii', errors='ignore')
            print(f"  Company: '{company}'")
            offset += length

print(f"\nFin du header estimée: offset {offset} (0x{offset:X})")

# Chercher le début du script
print("\n[SECTION 2: RECHERCHE DU SCRIPT TEXTE]")
print("-" * 40)

# Chercher les commandes communes
keywords = [b'if ', b'then', b'addbmp', b'delbmp', b'playavi', b'runprj']
positions = {}

for kw in keywords:
    pos = data.find(kw)
    if pos > 0:
        positions[kw.decode('ascii')] = pos

if positions:
    min_pos = min(positions.values())
    print(f"Première commande trouvée à: {min_pos} (0x{min_pos:X})")
    print(f"Commandes détectées: {positions}")
    
    print(f"\nIl y a {min_pos - offset} bytes entre fin header et début script")
    
    # Analyser cette zone intermédiaire
    if min_pos - offset > 0:
        print("\nZone intermédiaire (métadonnées binaires?):")
        inter = data[offset:min_pos]
        print(f"  Taille: {len(inter)} bytes")
        print(f"  Hex (premiers 100): {inter[:100].hex(' ')}")
        
        # Chercher des patterns
        null_count = inter.count(b'\x00')
        print(f"  Bytes NULL: {null_count}")
        
        # Chercher des entiers
        if len(inter) >= 4:
            for i in range(0, min(len(inter), 100), 4):
                if i + 4 <= len(inter):
                    val = struct.unpack('<I', inter[i:i+4])[0]
                    if val < 1000000 and val > 0:  # Valeur raisonnable
                        print(f"  Offset {offset+i}: {val} (0x{val:X})")

# Analyser le script
print("\n[SECTION 3: SCRIPT TEXTE]")
print("-" * 40)

if min_pos > 0:
    # Extraire un échantillon du script
    script_sample = data[min_pos:min_pos+500]
    
    # Essayer de décoder
    try:
        script_text = script_sample.decode('ascii', errors='replace')
        print("Échantillon du script (500 premiers chars):")
        print(script_text[:500])
    except:
        print("Erreur de décodage")

# Vérifier si tout est lisible après min_pos
print("\n[SECTION 4: VÉRIFICATION ENCODAGE]")
print("-" * 40)

if min_pos > 0:
    script_section = data[min_pos:]
    
    # Compter les bytes imprimables
    printable = sum(1 for b in script_section if 32 <= b <= 126 or b in [9, 10, 13])
    total = len(script_section)
    ratio = (printable / total) * 100
    
    print(f"Section script total: {total} bytes")
    print(f"Bytes imprimables ASCII: {printable} ({ratio:.1f}%)")
    print(f"Bytes non-ASCII: {total - printable} ({100-ratio:.1f}%)")
    
    if ratio > 90:
        print("\n✓ Le script est majoritairement en TEXTE CLAIR")
    else:
        print("\n✗ Le script contient beaucoup de données binaires")

print("\n" + "="*80)
print("CONCLUSION")
print("="*80)

print("""
Structure du fichier .vnd:

┌─────────────────────────────────────────┐
│ PARTIE 1: HEADER BINAIRE                │
│ - Format structuré avec length-prefixed  │
│ - Signature, version, métadonnées        │
│ - DOIT être parsé par le moteur          │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ PARTIE 2: MÉTADONNÉES BINAIRES (?)      │
│ - Zone entre header et script            │
│ - Possible table des offsets             │
│ - Possible index des ressources          │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ PARTIE 3: SCRIPT TEXTE                   │
│ - Commandes en clair (ASCII)             │
│ - if/then/addbmp/playavi...              │
│ - Directement interprétable              │
└─────────────────────────────────────────┘
""")
