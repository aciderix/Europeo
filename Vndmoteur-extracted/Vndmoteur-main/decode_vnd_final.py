import struct
import json

def decode_vnd(file_path):
    with open(file_path, 'rb') as f:
        data = f.read()
    
    size = len(data)
    results = {
        'header': {},
        'names': [],
        'records': []
    }
    
    # 1. En-tête
    results['header']['magic'] = data[9:15].decode('ascii', errors='ignore')
    results['header']['version'] = data[19:24].decode('ascii', errors='ignore')
    
    # 2. Dictionnaire de noms (SACADOS, JEU, etc.)
    offset = 0x8a
    while offset < 0x0800:
        if offset + 4 > size: break
        length = struct.unpack_from('<I', data, offset)[0]
        if 1 <= length <= 64:
            s_bytes = data[offset+4:offset+4+length]
            if all(32 <= b <= 126 for b in s_bytes):
                results['names'].append(s_bytes.decode())
                offset += 4 + length
                while offset < size and data[offset] == 0:
                    offset += 1
            else: offset += 1
        else: offset += 1

    # 3. Scan des enregistrements
    # On va scanner tout le fichier pour trouver les types connus
    # Types identifiés :
    # 105 : Polygone [Type][Count][X1][Y1]...
    # Autres : [Type][Length][String]
    
    i = 0
    while i < size - 8:
        r_type = struct.unpack_from('<I', data, i)[0]
        
        # Cas du Polygone (105)
        if r_type == 105:
            count = struct.unpack_from('<I', data, i + 4)[0]
            if 3 <= count <= 100:
                points = []
                valid = True
                for n in range(count):
                    off = i + 8 + (n * 8)
                    if off + 8 <= size:
                        x, y = struct.unpack_from('<ii', data, off)
                        if not (-2000 <= x <= 2000 and -2000 <= y <= 2000):
                            valid = False; break
                        points.append({'x': x, 'y': y})
                    else: valid = False; break
                if valid:
                    results['records'].append({
                        'offset': i,
                        'type': 'POLYGON',
                        'type_id': 105,
                        'data': points
                    })
                    i += 8 + count * 8
                    continue
        
        # Cas des chaînes de caractères (beaucoup de types différents)
        # On a vu que le type est suivi de la longueur
        length = struct.unpack_from('<I', data, i + 4)[0]
        if 1 <= length <= 1000 and i + 8 + length <= size:
            s_bytes = data[i+8:i+8+length]
            # On vérifie si c'est du texte imprimable
            if all(32 <= b <= 126 or 160 <= b <= 255 for b in s_bytes):
                text = s_bytes.decode('latin-1', errors='ignore')
                results['records'].append({
                    'offset': i,
                    'type': 'STRING',
                    'type_id': r_type,
                    'data': text
                })
                i += 8 + length
                continue
        
        i += 1

    return results

if __name__ == "__main__":
    output = decode_vnd('/home/ubuntu/upload/couleurs1.vnd')
    with open('/home/ubuntu/decoded_data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"Décodage terminé. {len(output['records'])} enregistrements extraits.")
    print(f"Résultats sauvegardés dans /home/ubuntu/decoded_data.json")
