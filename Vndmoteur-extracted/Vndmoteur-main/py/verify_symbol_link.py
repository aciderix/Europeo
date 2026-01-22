import struct

vnd_path = r'f:\Europeo\FRONTAL\dll\couleurs1.vnd'

with open(vnd_path, 'rb') as f:
    data = f.read()

# 1. Lire la valeur exacte du Trigger
# On sait que c'est autour de 0x3BE9 (offset fichier)
# Hex: 03 00 00 00 15 00 00 00
# Donc Opcode=3, Param=21

trigger_param = 21
print(f"Valeur du Trigger (Paramètre du saut): {trigger_param}")

# 2. Lire la Table des Symboles (Métadonnées)
print("\n[2] VÉRIFICATION DANS LA TABLE DES SYMBOLES")
print("-" * 60)

meta_start = 0x55
# On sait que la table commence un peu plus loin, vers 0x8E (fichier)
# Offset dans meta: 0x39
table_start = meta_start + 0x39

# On va parser les strings comme avant
current_pos = table_start
symbol_index = 0
found_link = False

print(f"{'IDX':<4} | {'OFFSET':<8} | {'SYMBOLE'}")
print("-" * 40)

# On remonte un peu pour être sûr (le header de la table est avant)
# Le premier string 'vnresmod.dll' était à 0x6E
# Essayons de scanner depuis le début des metadata
current_pos = meta_start

while current_pos < 0x1276:
    try:
        # Chercher structure [Len] [String]
        length = struct.unpack('<I', data[current_pos:current_pos+4])[0]
        
        if 0 < length < 100:
            # Lire string
            s_bytes = data[current_pos+4 : current_pos+4+length]
            try:
                s = s_bytes.decode('ascii')
                
                # C'est un symbol ?
                # On numérote
                prefix = ""
                if symbol_index == trigger_param:
                    prefix = ">>> MATCH 21! <<<"
                    found_link = True
                
                print(f"{symbol_index:<4} | 0x{current_pos:04X}   | {s:<30} {prefix}")
                
                symbol_index += 1
                current_pos += 4 + length
                
                # Alignement ? Parfois 4 bytes value après ?
                # Dans l'analyse précédente on avait vu: [Len] [Str] [Val]
                # Vérifions si on doit skipper 4 bytes
                
                # Heuristique: si le prochain uint32 est une longueur valide (petite), on n'a pas skippé
                # Si c'est 0 ou grand, c'était peut-être une valeur.
                
                # Regardons le byte suivant
                if current_pos + 4 < len(data):
                    next_val = struct.unpack('<I', data[current_pos:current_pos+4])[0]
                    if next_val == 0:
                        # Padding ou valeur 0
                        current_pos += 4
                    elif next_val > 100:
                         # Probablement une valeur, pas une longueur
                         current_pos += 4
                    # Sinon, c'est probablement la longueur du suivant
                
            except:
                current_pos += 1
        else:
            current_pos += 1
            
    except:
        break
    
    if symbol_index > 30: break

print("-" * 60)

if not found_link:
    print("Pas de correspondance directe trouvée avec l'index 21 des strings.")
    print("Peut-être une table différente (Table des Scènes?)")
    # Il y a plusieurs tables dans les métadonnées.
    
    # Cherchons si 21 est utilisé comme ID ailleurs
    
else:
    print("CORRESPONDANCE TROUVÉE !")
