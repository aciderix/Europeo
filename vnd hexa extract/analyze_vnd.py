#!/usr/bin/env python3
"""
Analyseur de fichier .vnd (format Borland Delphi)
Ce script tente de décrypter la structure du fichier .vnd
"""

import struct
import sys
from pathlib import Path

def read_pascal_string(data, offset):
    """Lit une chaîne Pascal (longueur sur 1 byte puis caractères)"""
    if offset >= len(data):
        return None, offset
    length = data[offset]
    offset += 1
    if offset + length > len(data):
        return None, offset
    string = data[offset:offset + length].decode('latin-1', errors='replace')
    return string, offset + length

def read_delphi_string(data, offset):
    """Lit une chaîne Delphi (longueur sur 4 bytes puis caractères UTF-16 ou ASCII)"""
    if offset + 4 > len(data):
        return None, offset
    length = struct.unpack('<I', data[offset:offset+4])[0]
    offset += 4
    
    # Protection contre des longueurs absurdes
    if length > 10000 or length < 0:
        return None, offset
    
    if offset + length > len(data):
        return None, offset
    
    # Essayer d'abord en ASCII/Latin-1
    try:
        string = data[offset:offset + length].decode('latin-1').rstrip('\x00')
        offset += length
        return string, offset
    except:
        return None, offset

def analyze_vnd_file(filepath):
    """Analyse le fichier .vnd et extrait les données"""
    with open(filepath, 'rb') as f:
        data = f.read()
    
    print(f"🔍 Analyse du fichier: {filepath}")
    print(f"📦 Taille: {len(data)} bytes\n")
    
    # Afficher les premiers bytes en hexadécimal
    print("=" * 80)
    print("📋 En-tête (premiers 128 bytes):")
    print("=" * 80)
    for i in range(0, min(128, len(data)), 16):
        hex_part = ' '.join(f'{b:02X}' for b in data[i:i+16])
        ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
        print(f"{i:08X}: {hex_part:<48} | {ascii_part}")
    
    print("\n" + "=" * 80)
    print("🔤 Recherche de chaînes de caractères:")
    print("=" * 80)
    
    # Rechercher toutes les chaînes ASCII imprimables
    strings_found = []
    current_string = []
    start_offset = 0
    
    for i, byte in enumerate(data):
        if 32 <= byte < 127 or byte in (9, 10, 13):  # Caractères imprimables + TAB, LF, CR
            if not current_string:
                start_offset = i
            current_string.append(chr(byte))
        else:
            if len(current_string) >= 4:  # Au moins 4 caractères
                string = ''.join(current_string).strip()
                if string:
                    strings_found.append((start_offset, string))
            current_string = []
    
    # Afficher les chaînes trouvées
    for offset, string in strings_found[:100]:  # Limiter à 100 premières chaînes
        print(f"  @{offset:08X}: {string}")
    
    print(f"\n📊 Total de chaînes trouvées: {len(strings_found)}")
    
    # Rechercher spécifiquement les variables mentionnées
    print("\n" + "=" * 80)
    print("🎯 Variables mentionnées dans les artefacts:")
    print("=" * 80)
    
    variables = [
        "JUSTEPRIX1", "JUSTEPRIX10", "JUSTEPRIX15", "JUSTEPRIX20", "JUSTEPRIX25",
        "JUSTEPRIX30", "JUSTEPRIX50", "JUSTEPRIX100", "JUSTEPRIXSCORE",
        "PAIN", "HELICE", "HARPON", "MASQUE", "BOUT_PLO", "BALLON1", "PLONGE",
        "GRECQUESTION", "GRECREPONSE", "FIOLEGRECE", "SCORE", "CARTETOUR",
        "BUS", "LEVRIERNUMERO", "LEVRIERPARI", "LEVRIERRESULTAT",
        "RUBAN", "PARFUM", "PEPE", "CASTAGNETTE", "DANSE", "TICKET", "TICKET_A",
        "MATH", "ORGUE", "PALETTE", "PEINTRE", "SCOREPEINTRE", "HOTTE", "FROG",
        "CPHOTO", "FIOLEGRECE2", "FIOLEVASE", "ROUEDENT", "VIOLON", "MARMOTTE",
        "MUSIC", "FIOLEAUTR", "PARTITION", "ORGE", "TONDEUSE", "SIROP", "LEVURE",
        "TRANS", "ALLEMAGNE", "FIOLE", "FRANCE"
    ]
    
    for var in variables:
        offset = data.find(var.encode('latin-1'))
        if offset != -1:
            print(f"  ✓ {var:<20} trouvée à l'offset {offset:08X} ({offset})")
            
            # Essayer de lire les données avant et après
            before = data[max(0, offset-10):offset]
            after = data[offset+len(var):offset+len(var)+20]
            
            print(f"    Avant:  {' '.join(f'{b:02X}' for b in before)}")
            print(f"    Après:  {' '.join(f'{b:02X}' for b in after)}")
    
    # Analyse de la structure (recherche de patterns)
    print("\n" + "=" * 80)
    print("🔬 Analyse structurelle:")
    print("=" * 80)
    
    # Rechercher les séquences NULL répétées (souvent des séparateurs)
    null_sequences = []
    null_count = 0
    null_start = 0
    for i, byte in enumerate(data):
        if byte == 0:
            if null_count == 0:
                null_start = i
            null_count += 1
        else:
            if null_count >= 4:
                null_sequences.append((null_start, null_count))
            null_count = 0
    
    print(f"  Séquences de NULLs (≥4): {len(null_sequences)}")
    for offset, count in null_sequences[:20]:
        print(f"    @{offset:08X}: {count} NULLs")
    
    return data, strings_found

def extract_structure(data):
    """Tente d'extraire la structure des données"""
    print("\n" + "=" * 80)
    print("🏗️  Tentative d'extraction de structure:")
    print("=" * 80)
    
    offset = 0
    records = []
    
    while offset < len(data) - 10:
        # Essayer de lire un entier (peut-être une longueur ou un type)
        try:
            value1 = struct.unpack('<I', data[offset:offset+4])[0]
            value2 = struct.unpack('<I', data[offset+4:offset+8])[0]
            
            # Si on trouve deux valeurs qui semblent raisonnables
            if 0 < value1 < 1000 and 0 < value2 < 100000:
                # Essayer de lire une chaîne
                string, new_offset = read_delphi_string(data, offset + 8)
                if string and len(string) > 0:
                    records.append({
                        'offset': offset,
                        'value1': value1,
                        'value2': value2,
                        'string': string
                    })
                    offset = new_offset
                    continue
        except:
            pass
        
        offset += 1
    
    print(f"  📝 Records trouvés: {len(records)}")
    for i, rec in enumerate(records[:50]):  # Afficher les 50 premiers
        print(f"    [{i}] @{rec['offset']:08X}: v1={rec['value1']:4d}, v2={rec['value2']:6d}, str='{rec['string']}'")
    
    return records

if __name__ == "__main__":
    filepath = Path("allem.vnd")
    
    if not filepath.exists():
        print(f"❌ Fichier non trouvé: {filepath}")
        sys.exit(1)
    
    data, strings = analyze_vnd_file(filepath)
    records = extract_structure(data)
    
    print("\n" + "=" * 80)
    print("✅ Analyse terminée!")
    print("=" * 80)
