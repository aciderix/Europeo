#!/usr/bin/env python3
"""
Asset Converter for Europeo React Port
Converts BMP images to PNG format
"""

import os
import sys
import shutil
from pathlib import Path

# Try to import PIL for image conversion
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("Warning: PIL not installed. Install with: pip install Pillow")
    print("Will copy files without conversion.")

# Countries to process
COUNTRIES = [
    'allem', 'angl', 'autr', 'belge', 'danem', 'ecosse',
    'espa', 'finlan', 'france', 'grece', 'holl', 'irland',
    'italie', 'portu', 'suede'
]

# Special modules
SPECIAL_MODULES = ['frontal', 'couleurs1', 'barre', 'biblio']


def convert_bmp_to_png(src_path: Path, dst_path: Path) -> bool:
    """Convert a BMP file to PNG"""
    if not HAS_PIL:
        # Just copy the file
        shutil.copy2(src_path, dst_path.with_suffix('.bmp'))
        return False

    try:
        with Image.open(src_path) as img:
            # Convert to RGB if necessary (some BMPs are palette-based)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img.save(dst_path, 'PNG', optimize=True)
        return True
    except Exception as e:
        print(f"  Error converting {src_path.name}: {e}")
        return False


def process_directory(src_dir: Path, dst_dir: Path, file_types: list) -> dict:
    """Process a directory, converting/copying files"""
    stats = {'converted': 0, 'copied': 0, 'errors': 0}

    if not src_dir.exists():
        return stats

    dst_dir.mkdir(parents=True, exist_ok=True)

    for pattern in file_types:
        for src_file in src_dir.glob(pattern):
            if src_file.is_file():
                if pattern.endswith('.bmp') or pattern.endswith('.BMP'):
                    # Convert BMP to PNG
                    dst_file = dst_dir / src_file.with_suffix('.png').name
                    if convert_bmp_to_png(src_file, dst_file):
                        stats['converted'] += 1
                    else:
                        stats['copied'] += 1
                else:
                    # Copy other files
                    dst_file = dst_dir / src_file.name
                    try:
                        shutil.copy2(src_file, dst_file)
                        stats['copied'] += 1
                    except Exception as e:
                        print(f"  Error copying {src_file.name}: {e}")
                        stats['errors'] += 1

    return stats


def convert_country(base_path: Path, output_path: Path, country_id: str) -> dict:
    """Convert all assets for a country"""
    country_path = base_path / country_id
    output_country = output_path / country_id

    total_stats = {'converted': 0, 'copied': 0, 'errors': 0}

    if not country_path.exists():
        print(f"  Country directory not found: {country_id}")
        return total_stats

    # Convert images
    img_stats = process_directory(
        country_path / 'img24',
        output_country / 'img24',
        ['*.bmp', '*.BMP']
    )

    # Also check for rol subdirectory
    rol_stats = process_directory(
        country_path / 'img24' / 'rol',
        output_country / 'img24' / 'rol',
        ['*.bmp', '*.BMP']
    )

    # Copy audio files
    audio_stats = process_directory(
        country_path / 'digit',
        output_country / 'digit',
        ['*.wav', '*.WAV']
    )

    # Copy HTML files
    html_stats = process_directory(
        country_path / 'html',
        output_country / 'html',
        ['*.htm', '*.HTM', '*.html', '*.HTML']
    )

    # Merge stats
    for key in total_stats:
        total_stats[key] += img_stats.get(key, 0)
        total_stats[key] += rol_stats.get(key, 0)
        total_stats[key] += audio_stats.get(key, 0)
        total_stats[key] += html_stats.get(key, 0)

    return total_stats


def main():
    # Determine paths
    script_dir = Path(__file__).parent
    base_path = script_dir.parent
    output_path = base_path / 'react-app' / 'public' / 'assets'

    print(f"Converting assets from: {base_path}")
    print(f"Output to: {output_path}")
    print(f"PIL available: {HAS_PIL}")
    print()

    # Create output directory
    output_path.mkdir(parents=True, exist_ok=True)

    # Copy game data JSON
    game_data_src = script_dir / 'game_data.json'
    game_data_dst = base_path / 'react-app' / 'public' / 'data'
    game_data_dst.mkdir(parents=True, exist_ok=True)
    if game_data_src.exists():
        shutil.copy2(game_data_src, game_data_dst / 'game_data.json')
        print("Copied game_data.json")

    total_converted = 0
    total_copied = 0
    total_errors = 0

    # Process countries
    print("\nProcessing countries:")
    for country_id in COUNTRIES:
        print(f"  {country_id}...", end=' ')
        stats = convert_country(base_path, output_path, country_id)
        print(f"✓ ({stats['converted']} converted, {stats['copied']} copied)")
        total_converted += stats['converted']
        total_copied += stats['copied']
        total_errors += stats['errors']

    # Process special modules
    print("\nProcessing special modules:")
    for module_id in SPECIAL_MODULES:
        print(f"  {module_id}...", end=' ')
        stats = convert_country(base_path, output_path, module_id)
        print(f"✓ ({stats['converted']} converted, {stats['copied']} copied)")
        total_converted += stats['converted']
        total_copied += stats['copied']
        total_errors += stats['errors']

    # Process barre images
    print("\nProcessing toolbar images:")
    barre_img_stats = process_directory(
        base_path / 'barre' / 'images',
        output_path / 'barre' / 'images',
        ['*.bmp', '*.BMP']
    )
    print(f"  ✓ ({barre_img_stats['converted']} converted)")
    total_converted += barre_img_stats['converted']
    total_copied += barre_img_stats['copied']

    print(f"\n{'='*50}")
    print(f"Total: {total_converted} converted, {total_copied} copied, {total_errors} errors")
    print(f"Output directory: {output_path}")


if __name__ == '__main__':
    main()
