#!/usr/bin/env python3
"""
VND File Parser - Virtual Navigator Engine Resource File Format
Reverse-engineered from vnresmod.dll (Sopra Multimedia, 1999)

Format Version: 2.136
Author: Reverse Engineering Project
"""

import struct
import os
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any
from enum import Enum, auto


class VNDCommand(Enum):
    """Commands supported by the VN scripting language"""
    SET_VAR = "set_var"
    INC_VAR = "inc_var"
    IF = "if"
    SCENE = "scene"
    ADDBMP = "addbmp"
    DELBMP = "delbmp"
    ADDTEXT = "addtext"
    PLAYTEXT = "playtext"
    RUNPRJ = "runprj"
    DEFCURSOR = "defcursor"
    HOTSPOT = "hotspot"
    UNKNOWN = "unknown"


@dataclass
class VNDHeader:
    """VND File Header Structure"""
    magic: bytes              # First 9 bytes - file magic
    signature: str            # "VNFILE"
    version: str              # e.g., "2.136"
    project_name: str         # e.g., "Europeo"
    creator: str              # e.g., "Sopra Multimedia"
    checksum: str             # MD5-like hash e.g., "5D51F233"
    screen_width: int         # Screen dimensions
    screen_height: int
    flags: int
    dll_path: str             # Path to vnresmod.dll


@dataclass
class VNDResource:
    """A resource/variable in the VND file"""
    name: str
    resource_type: int        # Resource type identifier
    value: int                # Initial value
    offset: int               # Offset in file


@dataclass
class VNDPolygon:
    """Polygon definition for hotspot hit-testing (PROVEN STRUCTURE)"""
    point_count: int
    points: List[Tuple[int, int]]

    @property
    def bounding_box(self) -> Tuple[int, int, int, int]:
        """Return (min_x, min_y, max_x, max_y)"""
        if not self.points:
            return (0, 0, 0, 0)
        xs = [p[0] for p in self.points]
        ys = [p[1] for p in self.points]
        return (min(xs), min(ys), max(xs), max(ys))


@dataclass
class VNDHotspot:
    """Interactive hotspot definition with polygon (PROVEN STRUCTURE)

    VND format stores hotspots as:
    - Text: "X Y W H 0 Name" (text label bounding box)
    - Binary: 00 00 00 [point_count:u32] [x1:u32][y1:u32]...[xN:u32][yN:u32]
    """
    id: int
    x: int
    y: int
    width: int
    height: int
    action: str
    name: str = ""
    polygon: Optional[VNDPolygon] = None
    target_scene: int = -1


@dataclass
class VNDScript:
    """A script/command block"""
    condition: str
    commands: List[Tuple[str, List[str]]]


@dataclass
class VNDScene:
    """A scene definition"""
    id: int
    name: str = ""
    background: str = ""
    hotspots: List[VNDHotspot] = field(default_factory=list)
    scripts: List[VNDScript] = field(default_factory=list)
    on_enter: List[str] = field(default_factory=list)
    on_exit: List[str] = field(default_factory=list)


class VNDParser:
    """
    Parser for Virtual Navigator (.vnd) files

    The VND format is a binary container for:
    - Project metadata (name, creator, version)
    - Resource declarations (variables, objects)
    - Scene definitions with scripts
    - Conditional logic and navigation
    """

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.data: bytes = b''
        self.header: Optional[VNDHeader] = None
        self.resources: Dict[str, VNDResource] = {}
        self.scenes: Dict[int, VNDScene] = {}
        self.scripts: List[str] = []
        self.raw_strings: List[str] = []

    def read_length_prefixed_string(self, offset: int) -> Tuple[str, int]:
        """Read a length-prefixed string from the data"""
        if offset + 4 > len(self.data):
            return "", offset
        length = struct.unpack_from('<I', self.data, offset)[0]
        offset += 4
        if length == 0 or offset + length > len(self.data):
            return "", offset
        try:
            string = self.data[offset:offset + length].decode('latin-1').rstrip('\x00')
        except:
            string = ""
        return string, offset + length

    def read_uint32(self, offset: int) -> Tuple[int, int]:
        """Read a 32-bit unsigned integer"""
        if offset + 4 > len(self.data):
            return 0, offset
        value = struct.unpack_from('<I', self.data, offset)[0]
        return value, offset + 4

    def read_uint16(self, offset: int) -> Tuple[int, int]:
        """Read a 16-bit unsigned integer"""
        if offset + 2 > len(self.data):
            return 0, offset
        value = struct.unpack_from('<H', self.data, offset)[0]
        return value, offset + 2

    def read_uint8(self, offset: int) -> Tuple[int, int]:
        """Read an 8-bit unsigned integer"""
        if offset + 1 > len(self.data):
            return 0, offset
        return self.data[offset], offset + 1

    def read_int32(self, offset: int) -> Tuple[int, int]:
        """Read a 32-bit signed integer"""
        if offset + 4 > len(self.data):
            return 0, offset
        value = struct.unpack_from('<i', self.data, offset)[0]
        return value, offset + 4

    def parse_polygon_at(self, offset: int) -> Optional[VNDPolygon]:
        """Parse polygon structure at given offset (PROVEN FORMAT)

        Binary format:
        [point_count: u32] [x1:u32][y1:u32]...[xN:u32][yN:u32]
        """
        if offset + 4 > len(self.data):
            return None

        point_count, _ = self.read_uint32(offset)

        # Validate point count
        if point_count < 3 or point_count > 30:
            return None

        # Check if we have enough data for all points
        if offset + 4 + point_count * 8 > len(self.data):
            return None

        points = []
        pos = offset + 4

        for _ in range(point_count):
            x, pos = self.read_int32(pos)
            y, pos = self.read_int32(pos)

            # Validate screen coordinates (with margin)
            if not (-100 <= x <= 2000 and -100 <= y <= 1000):
                return None

            points.append((x, y))

        return VNDPolygon(point_count=point_count, points=points)

    def find_hotspot_polygons(self) -> List[VNDHotspot]:
        """Find and parse all hotspot definitions with polygons (PROVEN FORMAT)

        Text format: "X Y W H 0 HotspotName"
        Followed by: 00 00 00 [point_count:u32] [coordinates...]
        """
        import re
        hotspots = []
        hotspot_id = 0

        # Pattern: "X Y W H 0 Name" where Name starts with letter
        pattern = rb'(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+0\s+([A-Za-z][^\x00\n\r]{1,50})'

        for match in re.finditer(pattern, self.data):
            x1, y1, x2, y2 = map(int, match.groups()[:4])
            name = match.group(5).decode('latin-1', errors='replace').strip()

            # Skip invalid names
            if len(name) > 50 or not name[0].isalpha():
                continue

            # Look for polygon after text (skip null padding)
            text_end = match.end()
            polygon = None

            # Try to find polygon in next 50 bytes
            for scan_offset in range(text_end, min(text_end + 50, len(self.data) - 4)):
                polygon = self.parse_polygon_at(scan_offset)
                if polygon:
                    break

            hotspots.append(VNDHotspot(
                id=hotspot_id,
                x=x1,
                y=y1,
                width=x2,
                height=y2,
                action="",
                name=name,
                polygon=polygon
            ))
            hotspot_id += 1

        return hotspots

    def parse_header(self) -> int:
        """Parse the VND file header, returns offset after header"""
        offset = 0

        # Read magic bytes (first 9 bytes)
        magic = self.data[offset:offset + 9]
        offset = 9

        # Read "VNFILE" signature
        signature = self.data[offset:offset + 6].decode('ascii')
        offset += 6

        if signature != "VNFILE":
            raise ValueError(f"Invalid VND signature: {signature}")

        # Read version
        version, offset = self.read_length_prefixed_string(offset)

        # Skip null byte after version
        offset += 3  # 3 null bytes

        # Read project name
        project_name, offset = self.read_length_prefixed_string(offset)

        # Read creator
        creator, offset = self.read_length_prefixed_string(offset)

        # Read checksum/hash
        checksum, offset = self.read_length_prefixed_string(offset)

        # Skip some bytes and read screen dimensions
        offset += 4  # 4 null bytes

        screen_width, offset = self.read_uint32(offset)
        screen_height, offset = self.read_uint32(offset)

        # Read flags
        flags, offset = self.read_uint32(offset)

        # Skip to DLL path
        offset += 8  # Skip some metadata

        # Read DLL path
        dll_path, offset = self.read_length_prefixed_string(offset)

        self.header = VNDHeader(
            magic=magic,
            signature=signature,
            version=version,
            project_name=project_name,
            creator=creator,
            checksum=checksum,
            screen_width=screen_width,
            screen_height=screen_height,
            flags=flags,
            dll_path=dll_path
        )

        return offset

    def parse_resources(self, offset: int) -> int:
        """Parse resource declarations"""
        resource_count = 0

        while offset < len(self.data) - 4:
            # Try to read a resource entry
            start_offset = offset
            length, offset = self.read_uint32(offset)

            # Check if this looks like a valid resource
            if length == 0 or length > 256:
                offset = start_offset
                break

            # Read resource name
            if offset + length > len(self.data):
                offset = start_offset
                break

            try:
                name = self.data[offset:offset + length].decode('latin-1').rstrip('\x00')
            except:
                offset = start_offset
                break

            offset += length

            # Read resource metadata (4 bytes of zeros usually)
            if offset + 4 > len(self.data):
                break

            metadata = self.data[offset:offset + 4]
            offset += 4

            # Store resource
            self.resources[name] = VNDResource(
                name=name,
                resource_type=metadata[0] if len(metadata) > 0 else 0,
                value=0,
                offset=start_offset
            )
            resource_count += 1

            # Check for script section (starts with non-length pattern)
            if offset < len(self.data) - 10:
                peek = self.data[offset:offset + 10]
                # Scripts often start with conditions like "variable >= value"
                if any(c in peek for c in [b'=', b'>', b'<', b'if', b'scene', b'set']):
                    break

        return offset

    def parse_scripts(self, offset: int) -> int:
        """Parse script section containing game logic"""
        # Find all text strings in the remaining data
        current = offset
        script_data = self.data[offset:]

        # Extract readable strings
        in_string = False
        current_string = []

        for i, byte in enumerate(script_data):
            if 32 <= byte <= 126:  # Printable ASCII
                current_string.append(chr(byte))
                in_string = True
            elif byte in [0x0a, 0x0d]:  # Newlines
                if current_string:
                    s = ''.join(current_string).strip()
                    if len(s) > 2:
                        self.raw_strings.append(s)
                current_string = []
                in_string = False
            elif in_string and len(current_string) > 2:
                s = ''.join(current_string).strip()
                if len(s) > 2:
                    self.raw_strings.append(s)
                current_string = []
                in_string = False
            else:
                current_string = []
                in_string = False

        # Parse scripts from raw strings
        for line in self.raw_strings:
            line = line.strip()
            if not line:
                continue
            self.scripts.append(line)

        return len(self.data)

    def parse(self):
        """Parse the entire VND file"""
        with open(self.filepath, 'rb') as f:
            self.data = f.read()

        # Parse header
        offset = self.parse_header()

        # Parse resources
        offset = self.parse_resources(offset)

        # Parse scripts
        self.parse_scripts(offset)

    def get_variables(self) -> List[str]:
        """Get list of variable names"""
        return list(self.resources.keys())

    def get_script_commands(self) -> List[Dict[str, Any]]:
        """Parse and return structured script commands"""
        commands = []

        for script in self.scripts:
            cmd = self.parse_script_line(script)
            if cmd:
                commands.append(cmd)

        return commands

    def parse_script_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse a single script line into structured command"""
        line = line.strip()
        if not line:
            return None

        result = {
            'raw': line,
            'type': 'unknown',
            'condition': None,
            'action': None,
            'params': []
        }

        # Check for conditional statement
        if ' then ' in line.lower():
            parts = line.split(' then ', 1)
            result['condition'] = parts[0].strip()
            if len(parts) > 1:
                result['action'] = parts[1].strip()
            result['type'] = 'conditional'

        # Check for set_var
        elif line.lower().startswith('set_var '):
            parts = line.split(None, 2)
            result['type'] = 'set_var'
            if len(parts) >= 3:
                result['params'] = [parts[1], parts[2]]

        # Check for inc_var
        elif line.lower().startswith('inc_var '):
            parts = line.split(None, 2)
            result['type'] = 'inc_var'
            if len(parts) >= 3:
                result['params'] = [parts[1], parts[2]]

        # Check for scene command
        elif line.lower().startswith('scene '):
            parts = line.split(None, 1)
            result['type'] = 'scene'
            if len(parts) >= 2:
                result['params'] = [parts[1]]

        # Check for addbmp
        elif line.lower().startswith('addbmp '):
            parts = line.split(None)
            result['type'] = 'addbmp'
            result['params'] = parts[1:]

        # Check for delbmp
        elif line.lower().startswith('delbmp '):
            parts = line.split(None)
            result['type'] = 'delbmp'
            result['params'] = parts[1:]

        # Check for runprj
        elif line.lower().startswith('runprj '):
            parts = line.split(None)
            result['type'] = 'runprj'
            result['params'] = parts[1:]

        # Check for addtext
        elif line.lower().startswith('addtext '):
            result['type'] = 'addtext'
            result['params'] = line.split(None)[1:]

        # Check for playtext
        elif line.lower().startswith('playtext '):
            result['type'] = 'playtext'
            result['params'] = line.split(None)[1:]

        # File path patterns (bitmaps, videos)
        elif '.bmp' in line.lower() or '.avi' in line.lower() or '.wav' in line.lower():
            result['type'] = 'media_reference'
            result['params'] = [line]

        return result

    def extract_scenes(self) -> Dict[int, List[str]]:
        """Extract scene numbers and their associated commands"""
        scenes = {}
        current_scene = 0

        for script in self.scripts:
            # Check for scene references
            if 'scene ' in script.lower():
                parts = script.lower().split('scene ')
                for part in parts[1:]:
                    try:
                        scene_num = int(part.split()[0])
                        if scene_num not in scenes:
                            scenes[scene_num] = []
                    except:
                        pass

            # Check for runprj scene references
            if 'runprj' in script.lower():
                parts = script.split()
                for i, part in enumerate(parts):
                    if part.lower() == 'runprj' and i + 2 < len(parts):
                        try:
                            scene_num = int(parts[i + 2])
                            if scene_num not in scenes:
                                scenes[scene_num] = []
                        except:
                            pass

        return scenes

    def print_summary(self):
        """Print a summary of the parsed VND file"""
        print("=" * 60)
        print("VND FILE ANALYSIS")
        print("=" * 60)

        if self.header:
            print(f"\n[HEADER]")
            print(f"  Signature: {self.header.signature}")
            print(f"  Version: {self.header.version}")
            print(f"  Project: {self.header.project_name}")
            print(f"  Creator: {self.header.creator}")
            print(f"  Checksum: {self.header.checksum}")
            print(f"  Screen: {self.header.screen_width}x{self.header.screen_height}")
            print(f"  DLL Path: {self.header.dll_path}")

        print(f"\n[RESOURCES] ({len(self.resources)} total)")
        for i, (name, res) in enumerate(list(self.resources.items())[:20]):
            print(f"  {i+1:3}. {name}")
        if len(self.resources) > 20:
            print(f"  ... and {len(self.resources) - 20} more")

        print(f"\n[SCRIPTS] ({len(self.scripts)} lines)")
        for i, script in enumerate(self.scripts[:30]):
            print(f"  {script[:80]}{'...' if len(script) > 80 else ''}")
        if len(self.scripts) > 30:
            print(f"  ... and {len(self.scripts) - 30} more lines")

        # Extract unique commands
        print(f"\n[COMMAND TYPES]")
        cmd_types = {}
        for script in self.scripts:
            cmd = self.parse_script_line(script)
            if cmd:
                cmd_type = cmd['type']
                cmd_types[cmd_type] = cmd_types.get(cmd_type, 0) + 1

        for cmd_type, count in sorted(cmd_types.items(), key=lambda x: -x[1]):
            print(f"  {cmd_type}: {count}")

        # Extract scenes
        scenes = self.extract_scenes()
        print(f"\n[SCENES REFERENCED] ({len(scenes)} scenes)")
        for scene_id in sorted(scenes.keys())[:20]:
            print(f"  Scene {scene_id}")

        print("\n" + "=" * 60)


class VNDEngine:
    """
    Runtime engine for executing VND scripts

    This reconstructs the logic of vnresmod.dll to:
    - Manage game state (variables)
    - Handle navigation between scenes
    - Execute conditional scripts
    - Process user interactions
    """

    def __init__(self):
        self.variables: Dict[str, int] = {}
        self.current_scene: int = 1
        self.bitmaps: Dict[str, Dict[str, Any]] = {}  # Active bitmaps
        self.hotspots: List[VNDHotspot] = []
        self.scripts: List[str] = []

    def set_var(self, name: str, value: int):
        """Set a variable value"""
        self.variables[name] = value

    def get_var(self, name: str) -> int:
        """Get a variable value (0 if not set)"""
        return self.variables.get(name, 0)

    def inc_var(self, name: str, amount: int = 1):
        """Increment a variable"""
        self.variables[name] = self.get_var(name) + amount

    def evaluate_condition(self, condition: str) -> bool:
        """Evaluate a conditional expression"""
        condition = condition.strip()

        # Parse operators
        operators = ['>=', '<=', '!=', '=', '>', '<']

        for op in operators:
            if op in condition:
                parts = condition.split(op, 1)
                if len(parts) == 2:
                    var_name = parts[0].strip()
                    try:
                        value = int(parts[1].strip())
                    except ValueError:
                        return False

                    var_value = self.get_var(var_name)

                    if op == '>=':
                        return var_value >= value
                    elif op == '<=':
                        return var_value <= value
                    elif op == '!=':
                        return var_value != value
                    elif op == '=':
                        return var_value == value
                    elif op == '>':
                        return var_value > value
                    elif op == '<':
                        return var_value < value

        return False

    def navigate_to_scene(self, scene_id: int):
        """Navigate to a different scene"""
        print(f"[ENGINE] Navigating from scene {self.current_scene} to scene {scene_id}")
        self.current_scene = scene_id
        # In full implementation, this would:
        # 1. Execute exit scripts for current scene
        # 2. Clear active bitmaps
        # 3. Load new scene resources
        # 4. Execute enter scripts for new scene

    def add_bitmap(self, name: str, path: str, x: int, y: int, z: int):
        """Add a bitmap to the display"""
        self.bitmaps[name] = {
            'path': path,
            'x': x,
            'y': y,
            'z': z  # Layer/priority
        }
        print(f"[ENGINE] Added bitmap: {name} at ({x}, {y}, z={z})")

    def del_bitmap(self, name: str):
        """Remove a bitmap from the display"""
        if name in self.bitmaps:
            del self.bitmaps[name]
            print(f"[ENGINE] Removed bitmap: {name}")

    def execute_command(self, command: str):
        """Execute a single script command"""
        command = command.strip()

        # Handle conditional
        if ' then ' in command.lower():
            parts = command.split(' then ', 1)
            condition = parts[0].strip()
            action = parts[1].strip() if len(parts) > 1 else ""

            # Handle nested if
            if condition.lower().startswith('if '):
                condition = condition[3:].strip()

            if self.evaluate_condition(condition):
                self.execute_command(action)
            return

        # Parse command type
        parts = command.split(None)
        if not parts:
            return

        cmd = parts[0].lower()

        if cmd == 'set_var' and len(parts) >= 3:
            try:
                self.set_var(parts[1], int(parts[2]))
            except ValueError:
                pass

        elif cmd == 'inc_var' and len(parts) >= 3:
            try:
                self.inc_var(parts[1], int(parts[2]))
            except ValueError:
                pass

        elif cmd == 'scene' and len(parts) >= 2:
            try:
                self.navigate_to_scene(int(parts[1]))
            except ValueError:
                pass

        elif cmd == 'addbmp' and len(parts) >= 5:
            try:
                name = parts[1]
                path = parts[2]
                x = int(parts[3])
                y = int(parts[4])
                z = int(parts[5]) if len(parts) > 5 else 0
                self.add_bitmap(name, path, x, y, z)
            except (ValueError, IndexError):
                pass

        elif cmd == 'delbmp' and len(parts) >= 2:
            self.del_bitmap(parts[1])

        elif cmd == 'runprj' and len(parts) >= 3:
            print(f"[ENGINE] Run project: {parts[1]} scene {parts[2]}")

    def run_scripts(self, scripts: List[str]):
        """Execute a list of scripts"""
        for script in scripts:
            self.execute_command(script)

    def print_state(self):
        """Print current engine state"""
        print("\n[ENGINE STATE]")
        print(f"  Current Scene: {self.current_scene}")
        print(f"  Variables: {len(self.variables)}")
        for name, value in list(self.variables.items())[:10]:
            print(f"    {name} = {value}")
        print(f"  Active Bitmaps: {len(self.bitmaps)}")
        for name, bmp in self.bitmaps.items():
            print(f"    {name}: {bmp['path']} at ({bmp['x']}, {bmp['y']})")


def main():
    """Main entry point"""
    import sys

    if len(sys.argv) < 2:
        # Default to couleurs1.vnd if no argument
        vnd_path = "couleurs1.vnd"
        if not os.path.exists(vnd_path):
            print("Usage: python vnd_parser.py <file.vnd>")
            sys.exit(1)
    else:
        vnd_path = sys.argv[1]

    print(f"Parsing: {vnd_path}")

    # Parse VND file
    parser = VNDParser(vnd_path)
    parser.parse()
    parser.print_summary()

    # Test engine with some scripts
    print("\n" + "=" * 60)
    print("ENGINE SIMULATION")
    print("=" * 60)

    engine = VNDEngine()

    # Initialize some variables from resources
    for name in list(parser.resources.keys())[:5]:
        engine.set_var(name, 0)

    # Run first 10 scripts
    print("\nExecuting first 10 scripts:")
    engine.run_scripts(parser.scripts[:10])

    engine.print_state()


if __name__ == "__main__":
    main()
