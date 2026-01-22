#!/usr/bin/env python3
"""
Generate game_data.json from extracted VND data
Parses the extracted JSON files and creates a unified game data file
for the React app.
"""

import json
import re
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Base paths
BASE_DIR = Path(__file__).parent.parent
EXTRACTED_DIR = BASE_DIR / "vnd hexa extract" / "extracted_data_all"
OUTPUT_DIR = BASE_DIR / "react-app" / "public" / "assets"

# Country mappings
COUNTRY_FOLDERS = {
    "allem": {"name": "Allemagne", "name_en": "Germany"},
    "angl": {"name": "Angleterre", "name_en": "England"},
    "autr": {"name": "Autriche", "name_en": "Austria"},
    "belge": {"name": "Belgique", "name_en": "Belgium"},
    "danem": {"name": "Danemark", "name_en": "Denmark"},
    "ecosse": {"name": "Écosse", "name_en": "Scotland"},
    "espa": {"name": "Espagne", "name_en": "Spain"},
    "finlan": {"name": "Finlande", "name_en": "Finland"},
    "france": {"name": "France", "name_en": "France"},
    "grece": {"name": "Grèce", "name_en": "Greece"},
    "holl": {"name": "Pays-Bas", "name_en": "Netherlands"},
    "irland": {"name": "Irlande", "name_en": "Ireland"},
    "italie": {"name": "Italie", "name_en": "Italy"},
    "portu": {"name": "Portugal", "name_en": "Portugal"},
    "suede": {"name": "Suède", "name_en": "Sweden"},
}

# VND to folder mapping
VND_TO_FOLDER = {
    "allem": "allem",
    "angleterre": "angl",
    "autr": "autr",
    "belge": "belge",
    "danem": "danem",
    "ecosse": "ecosse",
    "espa": "espa",
    "finlan": "finlan",
    "france": "france",
    "grece": "grece",
    "holl": "holl",
    "irland": "irland",
    "italie": "italie",
    "portu": "portu",
    "suede": "suede",
    "start": "frontal",
    "barre": "barre",
    "biblio": "biblio",
    "couleurs1": "couleurs1",
}


def parse_condition(text: str) -> Optional[Dict]:
    """Parse a condition like 'score < 0' or 'ticket = 1'"""
    match = re.match(r'(\w+)\s*(=|!=|<|>|<=|>=)\s*(-?\d+)', text.strip())
    if match:
        return {
            "variable": match.group(1).upper(),
            "operator": match.group(2),
            "value": int(match.group(3))
        }
    return None


def parse_command_string(cmd_str: str) -> Optional[Dict]:
    """Parse a command string from VND data"""
    cmd_str = cmd_str.strip()

    # Skip empty or too short
    if len(cmd_str) < 3:
        return None

    # Check for conditional: "condition then action [else action]"
    then_match = re.match(r'(.+?)\s+then\s+(.+?)(?:\s+else\s+(.+))?$', cmd_str, re.IGNORECASE)
    if then_match:
        condition = parse_condition(then_match.group(1))
        if condition:
            result = {
                "type": "conditional",
                "condition": condition,
                "then_action": then_match.group(2).strip()
            }
            if then_match.group(3):
                result["else_action"] = then_match.group(3).strip()
            return result

    # Parse direct commands
    parts = cmd_str.split()
    if not parts:
        return None

    cmd_type = parts[0].lower()

    # scene N
    if cmd_type == "scene" and len(parts) >= 2:
        try:
            return {"type": "scene", "target": int(parts[1])}
        except ValueError:
            pass

    # runprj path N
    if cmd_type == "runprj" and len(parts) >= 2:
        path = parts[1]
        scene = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 1
        return {"type": "runprj", "path": path, "scene": scene}

    # addbmp id file flags x y
    if cmd_type == "addbmp" and len(parts) >= 5:
        try:
            return {
                "type": "addbmp",
                "id": parts[1],
                "file": parts[2],
                "layer": int(parts[3]) if parts[3].isdigit() else 0,
                "x": int(parts[4]) if len(parts) > 4 else 0,
                "y": int(parts[5]) if len(parts) > 5 else 0
            }
        except (ValueError, IndexError):
            pass

    # delbmp id
    if cmd_type == "delbmp" and len(parts) >= 2:
        return {"type": "delbmp", "id": parts[1]}

    # playavi file mode x y w h
    if cmd_type == "playavi" and len(parts) >= 2:
        result = {"type": "playavi", "file": parts[1]}
        if len(parts) >= 6:
            try:
                result["rect"] = {
                    "x": int(parts[3]),
                    "y": int(parts[4]),
                    "w": int(parts[5]) - int(parts[3]),
                    "h": int(parts[6]) - int(parts[4]) if len(parts) > 6 else 100
                }
            except ValueError:
                pass
        return result

    # playwav file mode
    if cmd_type == "playwav":
        return {
            "type": "playwav",
            "file": parts[1] if len(parts) > 1 else "",
            "mode": int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 1
        }

    # playtext x y w h flags text
    if cmd_type == "playtext" and len(parts) >= 6:
        try:
            return {
                "type": "playtext",
                "x": int(parts[1]),
                "y": int(parts[2]),
                "w": int(parts[3]),
                "h": int(parts[4]),
                "text": " ".join(parts[6:]) if len(parts) > 6 else ""
            }
        except ValueError:
            pass

    # set_var variable value
    if cmd_type == "set_var" and len(parts) >= 3:
        try:
            return {
                "type": "set_var",
                "variable": parts[1].upper(),
                "value": int(parts[2])
            }
        except ValueError:
            pass

    # inc_var variable value
    if cmd_type == "inc_var" and len(parts) >= 3:
        try:
            return {
                "type": "inc_var",
                "variable": parts[1].upper(),
                "value": int(parts[2])
            }
        except ValueError:
            pass

    # dec_var variable value
    if cmd_type == "dec_var" and len(parts) >= 3:
        try:
            return {
                "type": "dec_var",
                "variable": parts[1].upper(),
                "value": int(parts[2])
            }
        except ValueError:
            pass

    # rundll file
    if cmd_type == "rundll" and len(parts) >= 2:
        return {"type": "rundll", "file": parts[1]}

    return None


def extract_scenes_from_strings(all_strings: Dict[str, str]) -> List[Dict]:
    """Extract scene definitions from VND strings by analyzing the sequential structure"""
    scene_pattern = re.compile(r'\bscene\s+(\d+)', re.IGNORECASE)
    bmp_pattern = re.compile(r'^[a-zA-Z][\w]*\.bmp$', re.IGNORECASE)
    wav_pattern = re.compile(r'^[\w]+\.wav', re.IGNORECASE)

    # Collect all scene numbers referenced in commands
    scene_numbers = set([1])  # Always have scene 1
    for text in all_strings.values():
        for match in scene_pattern.finditer(text):
            scene_numbers.add(int(match.group(1)))

    # Parse sequential structure to find scene blocks
    # Each scene block typically starts with: audio -> background -> commands
    scene_blocks = []
    current_block = {"background": None, "audio": None, "commands": []}

    sorted_items = sorted(all_strings.items(), key=lambda x: int(x[0], 16))

    for offset, text in sorted_items:
        text_clean = text.strip()

        # Check for background BMP (marks new scene)
        if bmp_pattern.match(text_clean):
            if not any(x in text_clean.lower() for x in ['roll', 'rol/', 'rol\\', 'barre']):
                # Save previous block if it had a background
                if current_block["background"]:
                    scene_blocks.append(current_block)
                current_block = {"background": text_clean, "audio": None, "commands": []}
                continue

        # Check for audio
        if wav_pattern.match(text_clean):
            current_block["audio"] = text_clean
            continue

        # Parse commands and add to current block
        cmd = parse_command_string(text_clean)
        if cmd:
            current_block["commands"].append(cmd)

    # Add last block
    if current_block["background"]:
        scene_blocks.append(current_block)

    # Build scenes - map scene numbers to blocks
    scenes = []
    sorted_scene_nums = sorted(scene_numbers)

    for i, scene_id in enumerate(sorted_scene_nums):
        block = scene_blocks[i % len(scene_blocks)] if scene_blocks else {}
        scenes.append({
            "id": scene_id,
            "background": block.get("background"),
            "audio": block.get("audio"),
            "commands": block.get("commands", [])[:20]  # Limit commands
        })

    return scenes


def extract_hotspots_from_strings(all_strings: Dict[str, str]) -> List[Dict]:
    """Extract hotspot definitions from VND strings with their actions"""
    hotspots = []
    seen_ids = set()
    hotspot_actions = {}  # Map hotspot id to its actions

    # Pattern for addbmp with roll/ or rol/ prefix
    addbmp_pattern = re.compile(
        r'addbmp\s+(\w+)\s+(rol[l]?[/\\][\w.]+)\s+(\d+)\s+(\d+)\s+(\d+)',
        re.IGNORECASE
    )

    # Pattern for hotspot actions: "hotspot_id = value then action"
    action_pattern = re.compile(
        r'(\w+)\s*=\s*(\d+)\s+then\s+(.+)',
        re.IGNORECASE
    )

    # First pass: collect all hotspot definitions
    for text in all_strings.values():
        match = addbmp_pattern.search(text)
        if match:
            hotspot_id = match.group(1)
            if hotspot_id not in seen_ids:
                seen_ids.add(hotspot_id)
                hotspots.append({
                    "id": hotspot_id,
                    "image": match.group(2).replace('\\', '/'),
                    "layer": int(match.group(3)),
                    "x": int(match.group(4)),
                    "y": int(match.group(5)),
                    "actions": []
                })

    # Second pass: find actions related to hotspots
    for text in all_strings.values():
        action_match = action_pattern.search(text)
        if action_match:
            var_name = action_match.group(1).lower()
            action_text = action_match.group(3).strip()

            # Check if this variable corresponds to a hotspot
            for hotspot in hotspots:
                if hotspot["id"].lower() == var_name:
                    # Parse the action
                    action_cmd = parse_command_string(action_text)
                    if action_cmd and len(hotspot["actions"]) < 5:
                        hotspot["actions"].append({
                            "condition_value": int(action_match.group(2)),
                            "action": action_cmd
                        })
                    break

    return hotspots


def extract_resources(all_strings: Dict[str, str]) -> Dict[str, List[str]]:
    """Extract resource references from VND strings"""
    resources = {
        "images": [],
        "audio": [],
        "videos": [],
        "html": []
    }

    for text in all_strings.values():
        # Images (.bmp)
        for match in re.findall(r'[\w/\\]+\.bmp', text, re.IGNORECASE):
            clean = match.replace('\\', '/').split('/')[-1]
            if clean not in resources["images"]:
                resources["images"].append(clean)

        # Audio (.wav)
        for match in re.findall(r'[\w/\\]+\.wav', text, re.IGNORECASE):
            clean = match.replace('\\', '/').split('/')[-1]
            if clean not in resources["audio"]:
                resources["audio"].append(clean)

        # Videos (.avi)
        for match in re.findall(r'[\w/\\]+\.avi', text, re.IGNORECASE):
            clean = match.replace('\\', '/').split('/')[-1]
            if clean not in resources["videos"]:
                resources["videos"].append(clean)

        # HTML (.htm)
        for match in re.findall(r'[\w/\\]+\.htm[l]?', text, re.IGNORECASE):
            clean = match.replace('\\', '/').split('/')[-1]
            if clean not in resources["html"]:
                resources["html"].append(clean)

    return resources


def load_extracted_vnd(vnd_name: str) -> Optional[Dict]:
    """Load extracted VND JSON data"""
    json_path = EXTRACTED_DIR / f"extracted_data_{vnd_name}.json"

    if not json_path.exists():
        print(f"  Warning: {json_path} not found")
        return None

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"  Error loading {json_path}: {e}")
        return None


def process_country(folder_id: str, info: Dict) -> Dict:
    """Process a single country's VND data"""
    print(f"Processing {info['name']} ({folder_id})...")

    # Map folder to VND name
    vnd_name = folder_id
    if folder_id == "angl":
        vnd_name = "angleterre"

    vnd_data = load_extracted_vnd(vnd_name)

    country = {
        "id": folder_id,
        "name": info["name"],
        "name_en": info["name_en"],
        "vnd": None,
        "vnp": None,
        "assets": {
            "images": [],
            "audio": [],
            "videos": [],
            "html": []
        }
    }

    if vnd_data:
        all_strings = vnd_data.get("all_strings", {})
        variables = vnd_data.get("variables", [])

        # Extract data
        scenes = extract_scenes_from_strings(all_strings)
        hotspots = extract_hotspots_from_strings(all_strings)
        resources = extract_resources(all_strings)

        # Build VND structure with full scene and hotspot data
        country["vnd"] = {
            "file": f"{vnd_name}.vnd",
            "path": f"{folder_id}/{vnd_name}.vnd",
            "variables": variables[:50],  # Limit for size
            "scenes": scenes[:30],  # Full scene objects with background and commands
            "resources": resources,
            "commands": [],  # Would be too large, skip for now
            "navigation": [],
            "hotspots": [
                {
                    "id": h["id"],
                    "image": h["image"],
                    "x": h["x"],
                    "y": h["y"],
                    "layer": h["layer"],
                    "actions": h.get("actions", [])
                }
                for h in hotspots[:30]
            ]
        }

        country["assets"] = resources
        print(f"  Found {len(scenes)} scenes, {len(hotspots)} hotspots, {len(resources['images'])} images")

    # Scan actual asset folder
    assets_dir = BASE_DIR / folder_id
    if assets_dir.exists():
        img_dir = assets_dir / "img24"
        if img_dir.exists():
            for f in img_dir.iterdir():
                if f.suffix.lower() == '.bmp' and f.name not in country["assets"]["images"]:
                    country["assets"]["images"].append(f.name)

        audio_dir = assets_dir / "digit"
        if audio_dir.exists():
            for f in audio_dir.iterdir():
                if f.suffix.lower() == '.wav' and f.name not in country["assets"]["audio"]:
                    country["assets"]["audio"].append(f.name)

    return country


def generate_game_data():
    """Generate the complete game_data.json"""
    print("=" * 60)
    print("Generating game_data.json from extracted VND data")
    print("=" * 60)

    game_data = {
        "metadata": {
            "title": "Europeo",
            "developer": "Sopra Multimedia",
            "format_version": "2.13",
            "resolution": {"width": 640, "height": 480}
        },
        "countries": {},
        "special_modules": {},
        "global_variables": []
    }

    # Process each country
    for folder_id, info in COUNTRY_FOLDERS.items():
        country = process_country(folder_id, info)
        game_data["countries"][folder_id] = country

    # Process special modules
    for module in ["start", "barre", "biblio", "couleurs1"]:
        vnd_data = load_extracted_vnd(module)
        if vnd_data:
            game_data["special_modules"][module] = {
                "vnd": {
                    "file": f"{module}.vnd",
                    "variables": vnd_data.get("variables", [])[:30]
                }
            }

    # Collect global variables
    all_vars = set()
    for country in game_data["countries"].values():
        if country["vnd"]:
            all_vars.update(country["vnd"]["variables"])
    game_data["global_variables"] = sorted(list(all_vars))[:100]

    # Write output
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "game_data.json"

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(game_data, f, indent=2, ensure_ascii=False)

    print("=" * 60)
    print(f"Generated: {output_path}")
    print(f"Countries: {len(game_data['countries'])}")
    print(f"Global variables: {len(game_data['global_variables'])}")
    print("=" * 60)

    return game_data


if __name__ == "__main__":
    generate_game_data()
