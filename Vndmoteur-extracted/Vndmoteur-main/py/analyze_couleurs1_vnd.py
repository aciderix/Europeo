import struct

vnd_path = r'f:\Europeo\FRONTAL\dll\couleurs1.vnd'
output_file = r'f:\Europeo\FRONTAL\dll\couleurs1_vnd_analysis.md'

with open(vnd_path, 'rb') as f:
    data = f.read()

with open(output_file, 'w', encoding='utf-8') as out:
    out.write("# Analyse de couleurs1.vnd\n\n")
    out.write("---\n\n")
    
    # Basic info
    out.write("## 1. Informations de Base\n\n")
    out.write(f"- **Nom du fichier**: couleurs1.vnd\n")
    out.write(f"- **Extension**: .vnd (Virtual Navigator Data)\n")
    out.write(f"- **Taille**: {len(data)} octets ({len(data) // 1024} KB)\n")
    out.write(f"- **Nom suggéré**: \"couleurs1\" → Mini-jeu ou activité sur les couleurs\n\n")
    
    # Header analysis
    out.write("## 2. Analyse du Format\n\n")
    out.write("### En-tête (premiers octets)\n\n")
    out.write("```\n")
    out.write("Hex: " + data[:50].hex(' ', 1) + "\n")
    out.write("ASCII: " + ''.join(chr(b) if 32 <= b <= 126 else '.' for b in data[:100]) + "\n")
    out.write("```\n\n")
    
    # Try to detect format
    is_text = all(b < 128 for b in data[:100])
    has_null = 0 in data[:100]
    
    out.write("### Type de Fichier\n\n")
    
    if is_text and not has_null:
        out.write("Le fichier semble être **texte** ou **format texte structuré**.\n\n")
    else:
        out.write("Le fichier semble être **binaire** ou **format propriétaire**.\n\n")
    
    # Extract strings
    out.write("## 3. Chaînes de Caractères Trouvées\n\n")
    
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
    
    out.write(f"**Nombre de chaînes**: {len(interesting_strings)}\n\n")
    
    if interesting_strings:
        out.write("### Chaînes Significatives\n\n")
        
        # Show unique strings
        unique_strings = sorted(set(interesting_strings), key=lambda x: len(x), reverse=True)[:50]
        
        for s in unique_strings:
            out.write(f"- `{s}`\n")
    
    out.write("\n")
    
    # Look for patterns
    out.write("## 4. Analyse du Contenu\n\n")
    
    # Check for common keywords
    keywords = {
        'color': any('color' in s.lower() or 'couleur' in s.lower() for s in interesting_strings),
        'image': any('bmp' in s.lower() or 'jpg' in s.lower() or 'image' in s.lower() for s in interesting_strings),
        'sound': any('wav' in s.lower() or 'sound' in s.lower() or 'son' in s.lower() for s in interesting_strings),
        'game': any('game' in s.lower() or 'jeu' in s.lower() or 'score' in s.lower() for s in interesting_strings),
    }
    
    out.write("### Éléments Détectés\n\n")
    
    for kw, found in keywords.items():
        status = "✓" if found else "✗"
        out.write(f"- **{kw.title()}**: {status}\n")
    
    out.write("\n")
    
    # Summary
    out.write("## 5. Interprétation\n\n")
    out.write("### Nature du Fichier\n\n")
    out.write("`couleurs1.vnd` est probablement un **fichier de projet Virtual Navigator**.\n\n")
    
    out.write("D'après le nom \"couleurs1\" (couleurs = colors):\n\n")
    out.write("- **Type**: Mini-jeu ou activité éducative\n")
    out.write("- **Thème**: Apprentissage des couleurs\n")
    out.write("- **Numéro**: \"1\" suggère qu'il pourrait y avoir couleurs2, couleurs3, etc.\n")
    out.write("- **Format**: Fichier de données propriétaire .vnd\n\n")
    
    out.write("### Contenu Probable\n\n")
    out.write("Ce fichier pourrait contenir:\n\n")
    out.write("- Définitions d'activités pédagogiques\n")
    out.write("- Références à des ressources (images, sons)\n")
    out.write("- Configuration du mini-jeu\n")
    out.write("- Données de questions/réponses\n")
    out.write("- Paramètres de difficulté\n\n")
    
    out.write("### Utilisation\n\n")
    out.write("Ce fichier serait chargé par `europeo.exe` pour:\n\n")
    out.write("1. Afficher une activité sur les couleurs\n")
    out.write("2. Gérer l'interaction utilisateur\n")
    out.write("3. Suivre la progression\n")
    out.write("4. Évaluer les réponses\n\n")
    
    out.write("### Extension .VND\n\n")
    out.write("L'extension `.vnd` signifie probablement:\n")
    out.write("- **V**irtual **N**avigator **D**ata, ou\n")
    out.write("- **V**irtual **N**avigator **D**ocument\n\n")
    out.write("C'est un format propriétaire créé spécifiquement pour Virtual Navigator.\n\n")
    
    out.write("---\n\n")
    out.write("*Analyse générée automatiquement*\n")

print(f"Rapport sauvegardé: {output_file}")
