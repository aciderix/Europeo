#!/usr/bin/env python3
"""
Re-parse tous les VND avec le parser amélioré
Génère de nouveaux JSON avec classification améliorée
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

# Liste de tous les VND à parser
VND_FILES = [
    'couleurs1/couleurs1.vnd',
    'allem/allem.vnd',
    'autr/autr.vnd',
    'belge/belge.vnd',
    'danem/danem.vnd',
    'ecosse/ecosse.vnd',
    'espa/espa.vnd',
    'finlan/finlan.vnd',
    'france/france.vnd',
    'grece/grece.vnd',
    'holl/holl.vnd',
    'irland/irland.vnd',
    'italie/italie.vnd',
    'portu/portu.vnd',
    'suede/suede.vnd',
    'biblio/biblio.vnd',
    'barre/barre.vnd',
    'frontal/start.vnd',
]

def parse_vnd(vnd_path: str) -> bool:
    """Parse un fichier VND avec le parser amélioré"""

    if not os.path.exists(vnd_path):
        print(f"  ⚠️  Fichier introuvable: {vnd_path}")
        return False

    # Parser sans limite de scènes
    cmd = ['python3', 'vnd_parser.py', vnd_path]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            print(f"  ✅ Succès")
            return True
        else:
            print(f"  ❌ Erreur:")
            if result.stderr:
                print(f"     {result.stderr[:200]}")
            return False

    except subprocess.TimeoutExpired:
        print(f"  ⏱️  Timeout (>30s)")
        return False
    except Exception as e:
        print(f"  ❌ Exception: {e}")
        return False

def main():
    """Re-parse tous les VND"""

    print("=" * 100)
    print("RE-PARSING TOUS LES VND AVEC PARSER AMÉLIORÉ")
    print("=" * 100)
    print()
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"VND à parser: {len(VND_FILES)}")
    print()

    # Vérifier que vnd_parser.py existe
    if not os.path.exists('vnd_parser.py'):
        print("❌ ERREUR: vnd_parser.py introuvable!")
        return

    print("-" * 100)
    print()

    success_count = 0
    failed_count = 0
    skipped_count = 0

    for i, vnd_path in enumerate(VND_FILES, 1):
        vnd_name = os.path.basename(vnd_path)
        print(f"[{i}/{len(VND_FILES)}] {vnd_name}...", end=' ')

        if parse_vnd(vnd_path):
            success_count += 1
        else:
            if os.path.exists(vnd_path):
                failed_count += 1
            else:
                skipped_count += 1

    print()
    print("=" * 100)
    print("RÉSUMÉ")
    print("=" * 100)
    print()

    print(f"Total VND: {len(VND_FILES)}")
    print(f"  ✅ Succès: {success_count}")
    print(f"  ❌ Échecs: {failed_count}")
    print(f"  ⚠️  Sautés (introuvables): {skipped_count}")
    print()

    if success_count == len(VND_FILES):
        print("🎉 TOUS LES VND ONT ÉTÉ PARSÉS AVEC SUCCÈS!")
    elif failed_count == 0:
        print("✅ Tous les VND disponibles ont été parsés avec succès")
    else:
        print(f"⚠️  {failed_count} VND ont échoué")

    print()

    # Lister les JSON générés
    print("=" * 100)
    print("JSON GÉNÉRÉS")
    print("=" * 100)
    print()

    for vnd_path in VND_FILES:
        json_path = vnd_path + '.parsed.json'
        if os.path.exists(json_path):
            size_kb = os.path.getsize(json_path) / 1024
            print(f"  ✅ {json_path} ({size_kb:.1f} KB)")
        else:
            print(f"  ❌ {json_path} (non généré)")

    print()

if __name__ == '__main__':
    main()
