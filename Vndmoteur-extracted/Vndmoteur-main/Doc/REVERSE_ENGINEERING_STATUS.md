# Virtual Navigator Engine - Reverse Engineering Status

## Project Goal
Reverse engineer the Virtual Navigator game engine (Sopra Multimedia, 1999) to understand
and recreate its functionality for porting purposes.

---

## COMPLETED ANALYSIS

### 1. europeo.exe (868 KB) - Main Game Executable

#### Command Dispatch System
- **Main dispatcher**: `fcn.0040b990` (7328 bytes) at switch 0x40ba62
- **Switch table**: 49 entries at 0x40ba69
- **Command strings**: Located at 0x43f76c (NULL-separated)

**Complete Command Table:**
```
Index | Command     | Handler      | Description
------|-------------|--------------|------------------
0     | quit        | 0x0040bb2d   | Exit application
1     | about       | 0x0040bb47   | About dialog
2     | prefs       | 0x0040bb61   | Preferences
3     | prev        | 0x0040bb7b   | Previous scene
4     | next        | 0x0040bc46   | Next scene
5     | zoom        | 0x0040bd11   | Zoom view
6     | scene       | 0x0040bd2b   | Load scene
7     | hotspot     | 0x0040bef9   | Define hotspot
8     | tiptext     | 0x0040bf6c   | Tooltip
9     | playavi     | 0x0040c097   | Play video
10    | playbmp     | 0x0040c134   | Display bitmap
11    | playwav     | 0x0040c4fe   | Play WAV
12    | playmid     | 0x0040c5c3   | Play MIDI
13    | playhtml    | 0x0040c661   | Display HTML
14-16 | zoomin/out/pause | 0x0040c82a | Shared
17    | exec        | 0x0040c8e7   | Execute
18    | explore     | 0x0040bf6c   | Same as tiptext
19    | playcda     | 0x0040c70d   | CD audio
20    | playseq     | 0x0040c74b   | Sequence
21    | if          | 0x0040c99c   | Conditional
22    | set_var     | 0x0040ca96   | Set variable
23    | inc_var     | 0x0040cb26   | Increment
24    | dec_var     | 0x0040cbd5   | Decrement
25    | invalidate  | 0x0040cc84   | Redraw
26    | defcursor   | 0x0040ccce   | Set cursor
27    | addbmp      | 0x0040c1f3   | Add bitmap
28-30 | del/show/hidebmp | 0x0040c3a6 | Shared
31    | runprj      | 0x0040cdee   | Run project
32    | update      | 0x0040ccb5   | Update
33    | rundll      | 0x0040cf4f   | Run DLL
34    | msgbox      | 0x0040d01d   | Message box
35    | playcmd     | 0x0040d175   | Play command
36    | closewav    | 0x0040c5aa   | Close WAV
37    | closedll    | 0x0040d004   | Close DLL
38    | playtext    | 0x0040d19f   | Display text
39    | font        | 0x0040d23d   | Set font
40    | rem         | 0x0040d6de   | Comment
41    | addtext     | 0x0040c2e3   | Add text
42-44 | del/show/hideobj | 0x0040c3a6 | Shared
45    | load        | 0x0040d2ca   | Load state
46    | save        | 0x0040d4c7   | Save state
47-48 | closeavi/mid | 0x0040c5aa  | Shared close
```

#### Event Types (at 0x43f8cf)
- `EV_ONFOCUS` : Mouse hover
- `EV_ONCLICK` : Mouse click
- `EV_ONINIT` : Initialization
- `EV_AFTERINIT` : Post-init

#### Operator Table (at 0x43f8fd)
- `=`, `!=`, `<`, `>`, `<=`, `>=`

#### Hotspot Hit-Testing
- **Function**: `fcn.00412168`
- Uses OWL52t.dll `TRegion` constructor with polygon points
- Calls GDI32 `PtInRegion()` for mouse detection
- Structure offsets:
  - `+0x31`: flags (bit 1 = special mode)
  - `+0x35`: point_count (uint32)
  - `+0x39`: pointer to TPoint array

#### Binary Stream Reading
Uses Borland Data Streaming (bds52t.dll):
- `ipstream_readWord32_qv` @ 0x439180
- `ipstream_readWord_qv` @ 0x439186
- `ipstream_readBytes_qpvui` @ 0x439192

**VND Record Reader** @ 0x42662b:
```c
void ReadRecord(Record* rec, ipstream* stream) {
    readBytes(stream, &rec->field_08, 4);
    readBytes(stream, &rec->field_0c, 4);
    readBytes(stream, &rec->field_10, 4);
    rec->field_14 = (readWord32(stream) != 0);
}
```

#### Command Registration
- **Function**: `fcn.004039b8` (99 bytes)
- Iterates NULL-separated command strings
- Allocates memory and copies to structure
- Called from init at 0x0040eb00

#### Argument Parser
- **Function**: `fcn.00407fe5`
- Checks for `<` (0x3c) and `>` (0x3e) delimiters
- Handles `<variable>` syntax for dynamic values
- Falls back to `_atol` for numeric conversion

---

### 2. vndllapi.dll (12 KB) - Variable Management API

#### Exported Functions
- `InitVNCommandMessage()` : Registers "wm_vncommand" Windows message
- `VNDLLVarFind(list, name)` : Find variable (case-insensitive via _strupr)
- `VNDLLVarAddModify(list, name, value)` : Add or modify variable
- `DirectDrawEnabled()` : Check DirectDraw availability

#### VNDLLVar Structure (264 bytes)
```c
typedef struct VNDLLVar {
    char name[256];        // 0x000: Variable name (uppercase)
    int value;             // 0x100: Value
    struct VNDLLVar* next; // 0x104: Next in linked list
} VNDLLVar;                // Total: 0x108 (264 bytes)
```

---

### 3. vnresmod.dll - Resource Module

#### Identified
- Borland C++ 1996 compiled
- Contains VND loading/parsing logic
- Uses TLS (Thread Local Storage)
- SetFilePointer for file seeking

#### Not Yet Analyzed
- Main parsing functions
- Resource extraction logic
- Scene loading mechanism

---

### 4. OWL52t.dll / bds52t.dll - Borland Libraries

- ObjectWindows Library 5.2 for GUI
- Data Streaming library for binary I/O
- TRegion for polygon regions
- TPoint for coordinates (8 bytes: x,y as int32)

---

## REMAINING WORK ON BINARIES

### High Priority
1. **Handler Deep Analysis**: Examine key handlers (scene, if, set_var) to understand:
   - How scene data is loaded from VND
   - How conditions are evaluated
   - How variables interact with VNDLLVar

2. **vnresmod.dll Full Analysis**:
   - Find VND file open/parse functions
   - Understand resource table parsing
   - Scene data extraction

3. **Event Dispatch Mechanism**:
   - How EV_ONFOCUS/ONCLICK trigger handlers
   - Event registration and routing

### Medium Priority
4. **Initialization Sequence**:
   - Full analysis of 0x0040eb00
   - Table registration order
   - Engine state initialization

5. **Multimedia Handlers**:
   - playavi implementation (MCI?)
   - playwav/playmid details
   - closewav cleanup

### Lower Priority
6. **Mini-game DLLs**: roue.dll, etc.
7. **Error handling paths**
8. **Memory management details

---

## VND FILE ANALYSIS (NEW FOCUS)

### Known Structure
```
[HEADER]
- Magic: 3a 01 01 00 00 06 00 00 00
- Signature: "VNFILE"
- Version: "2.136"
- Project name (length-prefixed)
- Creator (length-prefixed)
- Checksum (length-prefixed)
- Screen dimensions (640x480x16)
- DLL path

[RESOURCES]
- Length-prefixed resource names
- 4-byte metadata per resource

[MIXED DATA]
- Text commands (plaintext)
- Binary data (Little Endian integers)
  - Polygon coordinates
  - Scene numbers
  - Object types
  - Flags and parameters
```

### Binary Data Structure (DECODED)

#### Record Separator
Every record is separated by `01 00 00 00` (uint32 = 1)

#### Text Record Structure
```
01 00 00 00 [LENGTH:u32] [TYPE:u32] [TEXT...]
```
Where TYPE values observed:
- 1, 2: Hotspot/object references
- 11: Audio file reference
- 20-24: Media path records
- 34, 63, 64: Conditional commands

#### Hotspot/Polygon Structure (PROVEN)
```
[X1] [Y1] [X2] [Y2] 0 [Name] 00 00 00 [POINT_COUNT:u32] 00 00 00
[X1:u32] [Y1:u32] [X2:u32] [Y2:u32] ... [Xn:u32] [Yn:u32]
```

Example: "455 430 125 480 0 Quitteri"
- Text rect: 455,430 to 125,480 (bounding box text format)
- Name: "Quitter" with suffix 'i'
- Point count: 8 (at next aligned position)
- Polygon: (518,457), (520,416), (534,376), (558,356),
           (604,361), (621,402), (624,457), (592,474)

#### Discovered Polygons in couleurs1.vnd
| Offset | Name | Points | BBox |
|--------|------|--------|------|
| 0x33c0 | de la bière | 5 | (21,227)-(77,260) |
| 0x4c8c | Une table à produits | 8 | (311,173)-(605,298) |
| 0x53d8 | SORTIE | 6 | (98,49)-(289,246) |
| 0x6714 | runprj target | 7 | (551,289)-(630,394) |
| 0x11f90 | Quitter | 8 | (518,356)-(624,474) |

### Completed Analysis
1. **Record Type Enumeration**: 65+ record types identified (see VND_BINARY_FORMAT.md)
2. **Scene Structure**: Complete scene format decoded (name, audio, background, hotspots)
3. **Event Handling**: Events are implicit - hotspot polygons trigger ONCLICK, conditionals define actions
4. **Variable Table**: 240+ game variables discovered in header

### Next Steps
1. Create complete VND parser with binary support
2. Implement scene renderer for testing
3. Cross-validate with vnresmod.dll disassembly

---

## Files in Repository
- `vnengine.py` : Parser and engine implementation
- `polygons_hotspot_extractor.py` : Polygon extraction tool
- `Doc/` : Analysis documentation
- `europeo.exe`, `vndllapi.dll`, `vnresmod.dll` : Binaries under analysis

---

*Last updated: Session continuing VND binary analysis*
