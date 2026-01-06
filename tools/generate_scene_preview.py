#!/usr/bin/env python3
"""
Generate a visual preview of the Euroland main scene (face.bmp) with hotspots marked.
Based on analysis of couleurs1.vnd
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import json

# Hotspots from face.bmp (Scene 1) based on VND analysis
# Format: (x, y, text, action)
# X,Y are positions where hover text appears - they indicate hotspot center
FACE_HOTSPOTS = [
    (57, 60, "La bibliothèque", "bibliobis.avi"),
    (387, 351, "La banque", "bankbis.avi"),
    (89, 375, "Ma maison", "home2.avi"),
    (387, 18, "La maison de prof", "profbis.avi"),
    (249, 297, "Le musée du village", "musee.avi"),
    (348, 357, "La fontaine couleurs", "fontaine.avi -> scene 39"),
]

# Maison.bmp hotspots for second preview
MAISON_HOTSPOTS = [
    (1400, 350, "Une armoire bien remplie", "-> armoire3.bmp"),
    (95, 350, "SORTIE", "-> face.bmp"),
    (120, 360, "Madame euro", "femme.avi"),
    (370, 340, "Une table avec choses", "-> scene 51 (table_m.bmp)"),
    (800, 350, "Tu n'as pas le temps", ""),
    (990, 350, "Un lit", ""),
    (380, 320, "Un message caché", ""),
    (1090, 350, "Une étagère", "-> mess2.bmp"),
    (680, 350, "Question Bonus", "-> scene 35"),
    (1440, 350, "Chaudron (clé jaune)", "conditional"),
]


def load_bmp(path: Path) -> Image.Image:
    """Load a BMP file and convert to RGB"""
    img = Image.open(path)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    return img


def create_preview(bmp_path: Path, hotspots: list, output_path: Path, title: str = ""):
    """Create a preview image with hotspots marked"""
    # Load the background image
    img = load_bmp(bmp_path)
    draw = ImageDraw.Draw(img)

    print(f"Image size: {img.size}")

    # Try to load a font, fall back to default
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
    except:
        font = ImageFont.load_default()
        small_font = font

    # Draw each hotspot
    for i, (x, y, text, action) in enumerate(hotspots):
        # Skip if coordinates are outside image
        if x >= img.width or y >= img.height:
            print(f"  Skipping hotspot {i+1} - outside image bounds ({x},{y})")
            continue

        # Draw a circle at the hotspot position
        radius = 18
        color = (255, 255, 0)  # Yellow
        outline = (255, 0, 0)  # Red outline

        # Draw filled circle
        draw.ellipse(
            [x - radius, y - radius, x + radius, y + radius],
            fill=color,
            outline=outline,
            width=3
        )

        # Draw number in circle
        num = str(i + 1)
        bbox = draw.textbbox((0, 0), num, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text((x - tw // 2, y - th // 2), num, fill=(0, 0, 0), font=font)

        # Draw label with text
        label_x = x + radius + 10
        label_y = y - 8

        # Adjust position if off-screen
        if label_x + 180 > img.width:
            label_x = x - radius - 190

        # Draw text background
        label_text = text[:28]
        bbox = draw.textbbox((0, 0), label_text, font=small_font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        padding = 4
        draw.rectangle(
            [label_x - padding, label_y - padding, label_x + tw + padding, label_y + th + padding],
            fill=(0, 0, 0),
            outline=(255, 255, 0),
            width=1
        )
        draw.text((label_x, label_y), label_text, fill=(255, 255, 255), font=small_font)

    # Draw title bar at top
    if title:
        draw.rectangle([0, 0, img.width, 30], fill=(0, 0, 100))
        draw.text((10, 6), title, fill=(255, 255, 255), font=font)

    # Draw legend at bottom
    legend_height = 25 + len(hotspots) * 14
    legend_y = img.height - legend_height
    draw.rectangle([0, legend_y, img.width, img.height], fill=(0, 0, 50))
    draw.text((10, legend_y + 5), "HOTSPOTS:", fill=(255, 255, 0), font=font)

    for i, (x, y, text, action) in enumerate(hotspots):
        line_y = legend_y + 22 + (i * 14)
        if line_y < img.height - 5:
            action_short = action[:35] if action else "-"
            legend_text = f"{i + 1}. [{x:4d},{y:4d}] {text[:25]:<25} -> {action_short}"
            draw.text((10, line_y), legend_text, fill=(200, 200, 200), font=small_font)

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, 'PNG')
    print(f"Saved preview to: {output_path}")

    return img


def main():
    base_path = Path("/home/user/Europeo/couleurs1/img24/euroland")
    output_dir = Path("/home/user/Europeo/Doc/previews")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Preview 1: face.bmp (main Euroland screen)
    face_bmp = base_path / "face.bmp"
    if face_bmp.exists():
        print(f"\n=== Creating preview for face.bmp ===")
        create_preview(
            face_bmp,
            FACE_HOTSPOTS,
            output_dir / "01_face_hotspots.png",
            title="EUROLAND - Écran principal (face.bmp) - 640x400"
        )
    else:
        print(f"Not found: {face_bmp}")

    # Preview 2: maison.bmp (the house - scrollable 1920px wide)
    maison_bmp = base_path / "maison.bmp"
    if maison_bmp.exists():
        print(f"\n=== Creating preview for maison.bmp ===")
        create_preview(
            maison_bmp,
            MAISON_HOTSPOTS,
            output_dir / "02_maison_hotspots.png",
            title="MA MAISON (maison.bmp) - Image scrollable 1920x400"
        )
    else:
        print(f"Not found: {maison_bmp}")

    # Preview 3: armoire3.bmp
    armoire_bmp = base_path / "armoire3.bmp"
    armoire_hotspots = [
        (52, 177, "Sac à dos", "sac2.bmp + sacados=1"),
        (360, 36, "Allumettes", "if sacados: allumette2.bmp"),
        (280, 370, "SORTIE", "-> maison.bmp"),
    ]
    if armoire_bmp.exists():
        print(f"\n=== Creating preview for armoire3.bmp ===")
        create_preview(
            armoire_bmp,
            armoire_hotspots,
            output_dir / "03_armoire_hotspots.png",
            title="ARMOIRE (armoire3.bmp)"
        )

    # Preview 4: table_m.bmp
    table_bmp = base_path / "table_m.bmp"
    table_hotspots = [
        (400, 180, "Une bouteille vide", "info"),
        (380, 290, "Dossier euro", "-> mes_100.bmp"),
        (50, 350, "SORTIE", "-> maison.bmp"),
    ]
    if table_bmp.exists():
        print(f"\n=== Creating preview for table_m.bmp ===")
        create_preview(
            table_bmp,
            table_hotspots,
            output_dir / "04_table_hotspots.png",
            title="TABLE (table_m.bmp)"
        )

    print(f"\n{'='*60}")
    print(f"All previews saved to: {output_dir}")
    print(f"{'='*60}")
    print("\nFiles created:")
    for f in sorted(output_dir.glob("*.png")):
        print(f"  - {f.name} ({f.stat().st_size / 1024:.1f} KB)")


if __name__ == '__main__':
    main()
