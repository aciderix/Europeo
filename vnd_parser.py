#!/usr/bin/env python3
"""
VND Parser - Traduction exacte du parser TypeScript couleurs-ok-parser
"""

import struct
import json
import sys
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any


# === SIGNATURES MAGIQUES VND ===
# Chaque fichier VND peut utiliser une signature différente
VND_SIGNATURES = {
    0xFFFFFFDB,  # couleurs1.vnd
    0xFFFFFFF4,  # danem.vnd
    0xFFFFFFF5,  # allem.vnd
    0xFFFFFFB7,  # angleterre.vnd
    0xFFFFFFE4,  # france.vnd
    0xFFFFFFE2,  # italie.vnd
}


@dataclass
class SceneFile:
    slot: int
    filename: str
    param: int
    offset: int


@dataclass
class InitCommand:
    id: int
    param: str
    offset: int
    subtype: Optional[int] = None
    isRecovered: Optional[bool] = None


@dataclass
class InitScript:
    offset: int
    length: int
    commands: List[InitCommand] = field(default_factory=list)


@dataclass
class SceneConfig:
    offset: int
    flag: int
    ints: List[int] = field(default_factory=list)
    foundSignature: bool = False


@dataclass
class HotspotCommand:
    id: int
    subtype: int
    param: str


@dataclass
class Point:
    x: int
    y: int


@dataclass
class HotspotGeometry:
    cursorId: int
    pointCount: int
    points: List[Point] = field(default_factory=list)
    extraFlag: int = 0


@dataclass
class TooltipRect:
    x1: int
    y1: int
    x2: int
    y2: int


@dataclass
class TooltipInfo:
    type: int
    rect: TooltipRect
    flag: int
    text: str


@dataclass
class Hotspot:
    index: int
    offset: int
    commands: List[HotspotCommand] = field(default_factory=list)
    geometry: HotspotGeometry = None
    isRecovered: Optional[bool] = None
    isTooltip: Optional[bool] = None
    tooltip: Optional[TooltipInfo] = None


@dataclass
class ParsedScene:
    id: int
    offset: int
    length: int
    files: List[SceneFile] = field(default_factory=list)
    initScript: InitScript = None
    config: SceneConfig = None
    hotspots: List[Hotspot] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    parseMethod: str = 'signature'
    sceneType: str = 'game'
    sceneName: Optional[str] = None


@dataclass
class ParseResult:
    scenes: List[ParsedScene] = field(default_factory=list)
    logs: List[str] = field(default_factory=list)
    totalBytes: int = 0


class VNDSequentialParser:
    """Parser VND - Traduction exacte du TypeScript"""

    def __init__(self, data: bytes):
        self.data = data
        self.logs: List[str] = []

    def log(self, msg: str):
        self.logs.append(msg)

    def isValidSignature(self, value: int) -> bool:
        """Vérifie si une valeur est une signature VND valide"""
        return value in VND_SIGNATURES

    # === PRIMITIVES DE LECTURE SÉCURISÉES ===

    def readU8(self, offset: int) -> int:
        if offset >= len(self.data):
            return 0
        return self.data[offset]

    def readU32(self, offset: int) -> int:
        if offset + 4 > len(self.data):
            return 0
        return struct.unpack_from('<I', self.data, offset)[0]

    def readI32(self, offset: int) -> int:
        if offset + 4 > len(self.data):
            return 0
        return struct.unpack_from('<i', self.data, offset)[0]

    def tryReadString(self, offset: int) -> Optional[Tuple[str, int]]:
        """Lit une chaîne Pascal (Len + Bytes), retourne (text, nextOffset) ou None"""
        if offset + 4 > len(self.data):
            return None

        length = self.readU32(offset)

        # Sanity check longueur
        if length > 5000:
            return None
        if offset + 4 + length > len(self.data):
            return None

        if length == 0:
            return ("", offset + 4)

        # Vérification de validité stricte pour éviter le binaire
        binaryCount = 0
        for i in range(length):
            char = self.data[offset + 4 + i]
            # Accepte Tab (9), LF (10), CR (13) et les caractères imprimables >= 32
            if char < 32 and char not in (9, 10, 13):
                binaryCount += 1

        # Si plus de 10% de caractères bizarres, on rejette
        if binaryCount > 0 and binaryCount > length * 0.1:
            return None

        strBytes = self.data[offset + 4:offset + 4 + length]
        try:
            text = strBytes.decode('cp1252').replace('\x00', '').strip()
        except:
            text = strBytes.decode('latin-1', errors='replace').replace('\x00', '').strip()
        return (text, offset + 4 + length)

    # === SCANNER HEURISTIQUE HOTSPOTS ===

    def scanForHotspots(self, startOffset: int, limitOffset: int) -> int:
        """Scan octet par octet pour trouver une structure de hotspot valide"""
        for ptr in range(startOffset, limitOffset - 16):
            if self.isValidHotspotTable(ptr, limitOffset):
                return ptr
        return -1

    def isValidHotspotTable(self, offset: int, limit: int) -> bool:
        ptr = offset
        if ptr + 4 > limit:
            return False

        objCount = self.readU32(ptr)
        ptr += 4

        # Un nombre d'objets excessif est suspect, mais 0 est possible
        if objCount > 200:
            return False
        if objCount == 0:
            return (limit - ptr) < 32

        try:
            # On vérifie les N premiers objets pour confirmer la structure
            itemsToCheck = min(objCount, 3)

            for i in range(itemsToCheck):
                if ptr + 4 > limit:
                    return False
                cmdCount = self.readU32(ptr)

                # ALIGNEMENT FIX : Si cmdCount est énorme, check +2 bytes
                if cmdCount > 1000 and ptr + 6 <= limit:
                    aligned = self.readU32(ptr + 2)
                    if aligned < 100:
                        ptr += 2
                        cmdCount = aligned

                ptr += 4
                if cmdCount > 100:
                    return False

                for c in range(cmdCount):
                    if ptr + 8 > limit:
                        return False
                    ptr += 8  # ID + Subtype
                    res = self.tryReadString(ptr)
                    if not res:
                        return False
                    ptr = res[1]

                if ptr + 8 > limit:
                    return False
                # RELAXED CHECK : CursorID peut être n'importe quoi
                ptr += 4  # Cursor ID

                pointCount = self.readU32(ptr)
                ptr += 4

                if pointCount > 200:
                    return False

                # STRICT CHECK: Un objet doit faire quelque chose ou exister géométriquement
                if cmdCount == 0 and pointCount == 0:
                    return False

                pointsSize = pointCount * 8
                if ptr + pointsSize > limit:
                    return False
                ptr += pointsSize

                if ptr + 4 <= limit:
                    ptr += 4  # Extra Flag

            return True
        except:
            return False

    # === SPECIFIQUE COULEURS1.VND : DETECTION DE LOGIQUE D2/D3/AVI ===

    def isCouleurs1LogicBlock(self, offset: int) -> bool:
        if offset + 60 > len(self.data):
            return False

        id_val = self.readU32(offset)
        if id_val not in (21, 3):
            return False

        length = self.readU32(offset + 4)
        if length > 100:
            return False

        strBytes = self.data[offset + 8:offset + 8 + 40]
        try:
            s = strBytes.decode('cp1252', errors='replace')
        except:
            return False

        if 'score <= 0 then addbmp d3' in s:
            return True
        if 'score >= 0 then addbmp d2' in s:
            return True
        if 'fin2.avi' in s:
            return True

        return False

    # === PASSE 1 : CARTOGRAPHIE ===

    def findSceneOffsets(self) -> List[int]:
        offsets = []
        ptr = 0
        dataLen = len(self.data)

        self.log("PHASE 1: Scanning pour les tables de fichiers...")

        while ptr < dataLen - 20:
            # 0. HACK COULEURS1 : Détection forcée des blocs logiques d2/d3/avi
            if self.isCouleurs1LogicBlock(ptr):
                offsets.append(ptr)
                self.log(f"  [HACK] Scène logique 'Couleurs1' (d2/d3/avi) détectée @ 0x{ptr:X}")
                ptr += 8
                continue

            # 1. Vérifier si c'est un "Empty Slot"
            if self.isEmptySlotMarker(ptr):
                offsets.append(ptr)
                ptr += 9
                continue

            # 2. Vérifier si c'est une table de fichiers standard
            tableEnd = self.isValidFileTable(ptr)

            if tableEnd != -1 and tableEnd > ptr:
                offsets.append(ptr)
                self.log(f"  [+] Scène détectée @ 0x{ptr:X} (Table -> 0x{tableEnd:X})")
                ptr = tableEnd
            else:
                ptr += 1

        return offsets

    def isEmptySlotMarker(self, offset: int) -> bool:
        if offset + 9 > len(self.data):
            return False
        # Length = 5
        if self.readU32(offset) != 5:
            return False
        # String = "Empty" (E=69, m=109, p=112, t=116, y=121)
        return (self.data[offset+4] == 69 and
                self.data[offset+5] == 109 and
                self.data[offset+6] == 112 and
                self.data[offset+7] == 116 and
                self.data[offset+8] == 121)

    def isValidFileTable(self, offset: int) -> int:
        """Vérifie si une table de fichiers commence à offset, retourne fin ou -1"""
        current = offset
        validSlots = 0
        hasExtensions = 0
        foundSpecificSignature = False
        foundEndSignature = False

        maxSlotsToScan = 500

        for i in range(maxSlotsToScan):
            if current + 4 > len(self.data):
                break

            # Check for Magic End Signature
            if self.isValidSignature(self.readU32(current)):
                foundEndSignature = True
                break

            length = self.readU32(current)

            # 1. Gestion du Padding
            if length == 0:
                paramCheck = self.readU32(current + 4)
                if self.isValidSignature(paramCheck):
                    foundEndSignature = True
                    break

                if current + 8 <= len(self.data) and paramCheck == 0:
                    current += 8
                    continue
                break

            # 2. Lecture normale
            if length > 500:
                break

            res = self.tryReadString(current)
            if not res:
                break

            if res[1] + 4 > len(self.data):
                break
            param = self.readU32(res[1])

            if param > 0xFFFFFF and not self.isValidSignature(param):
                break

            name = res[0].lower()

            if self.looksLikeScriptParam(name):
                break

            if ' if ' in name or ' = ' in name or ' then ' in name or name.startswith('run'):
                break

            # REJECT paths relatifs (paramètres de commandes, pas des fichiers de scène)
            if '..\\' in name or '../' in name:
                break

            if name and name != "empty":
                if name == "toolbar":
                    foundSpecificSignature = True
                if re.search(r'\.(bmp|wav|avi|htm|html|dll|vnp|cur|ico)$', name):
                    hasExtensions += 1

            # CORRECTIF CIBLÉ "FIN PERDU"
            if name == 'perdu.htm':
                foundWav = False
                for scan in range(200):
                    ptr = res[1] + 4 + scan
                    if ptr + 14 > len(self.data):
                        break
                    checkLen = self.readU32(ptr)
                    if checkLen == 9:
                        if self.data[ptr+4] == 112 and self.data[ptr+12] == 118:
                            current = ptr
                            foundWav = True
                            break
                if foundWav:
                    continue

            current = res[1] + 4
            validSlots += 1

        isToolbar = foundSpecificSignature
        isEndSig = foundEndSignature
        isHeuristic = (validSlots >= 1 and hasExtensions >= 1) or (validSlots > 50)

        if isToolbar or (isEndSig and validSlots >= 1) or isHeuristic:
            return current

        for probe in range(current, min(current + 100, len(self.data) - 4)):
            if self.isValidSignature(self.readU32(probe)) and validSlots >= 1:
                return probe

        return -1

    def looksLikeScriptParam(self, text: str) -> bool:
        """Vérifie si une chaîne ressemble à un paramètre de script"""
        clean = text.strip()
        if re.match(r'^\d+\s+\d+', clean):
            return True
        if '#' in clean and re.search(r'[0-9a-fA-F]{6}', clean):
            return True
        if re.search(r'\.(avi|bmp|wav|mp3|dll)\s+\d+', clean):
            return True
        lower = clean.lower()
        if lower.startswith('comic sans') or lower.startswith('arial'):
            return True
        if clean in ('Quitter', 'Retour'):
            return True
        if re.match(r'^\d+[a-zA-Z]?$', clean) and len(clean) >= 2:
            return True
        return False

    # === INTELLIGENCE : INFÉRENCE DE TYPE ===

    def inferCommandType(self, text: str) -> Tuple[int, int]:
        """Retourne (id, subtype) inféré depuis le texte"""
        lower = text.lower()

        # PRIORITÉ ABSOLUE : Navigation (Subtype 6)
        if lower.startswith('scene '):
            return (3, 6)
        if ' then scene ' in lower:
            return (3, 6)
        if re.match(r'^\d+[a-z]$', lower):
            return (3, 6)

        if lower.endswith('.wav'):
            return (1, 11)
        if lower.endswith('.avi'):
            return (1, 9)
        if ' = ' in lower or lower.startswith('if ') or ' then ' in lower:
            return (3, 21)
        if lower.startswith('runprj') or lower.startswith('rundll') or lower.startswith('scene '):
            return (3, 0)
        if lower.endswith('.dll'):
            return (3, 5)
        if lower.startswith('font '):
            return (0, 39)
        if 'comic sans' in lower or 'arial' in lower:
            return (0, 39)

        if self.looksLikeScriptParam(text) and '=' not in text:
            return (0, 0)
        if 'addbmp' in lower or 'playbmp' in lower:
            return (0, 24)
        if lower.endswith('.bmp'):
            return (0, 27)

        return (9999, 0)

    # === DÉTECTION DE STRUCTURE TOOLTIP ===

    def tryParseTooltip(self, offset: int, limit: int) -> Optional[Tuple[TooltipInfo, int]]:
        if offset + 29 > limit:
            return None

        type_val = self.readU32(offset)
        x1 = self.readU32(offset + 4)
        y1 = self.readU32(offset + 8)
        x2 = self.readU32(offset + 12)
        y2 = self.readU32(offset + 16)
        flag = self.readU32(offset + 20)
        strLen = self.readU32(offset + 24)

        if type_val > 20:
            return None
        if x1 > 800 or y1 > 600 or x2 > 800 or y2 > 600:
            return None
        if x2 < x1 or y2 < y1:
            return None

        width = x2 - x1
        height = y2 - y1
        if width < 10 or height < 10:
            return None

        if flag > 10:
            return None
        if strLen < 2 or strLen > 100:
            return None
        if offset + 28 + strLen > limit:
            return None

        validChars = 0
        controlChars = 0
        for i in range(strLen):
            c = self.data[offset + 28 + i]
            if c < 32 and c != 0:
                controlChars += 1
            if (32 <= c <= 126) or (128 <= c <= 255):
                validChars += 1

        if controlChars > 0:
            return None
        if validChars < strLen * 0.9:
            return None

        textBytes = self.data[offset + 28:offset + 28 + strLen]
        try:
            text = textBytes.decode('cp1252').replace('\x00', '').strip()
        except:
            text = textBytes.decode('latin-1', errors='replace').replace('\x00', '').strip()

        if len(text) < 2:
            return None

        tooltip = TooltipInfo(
            type=type_val,
            rect=TooltipRect(x1=x1, y1=y1, x2=x2, y2=y2),
            flag=flag,
            text=text
        )

        return (tooltip, offset + 28 + strLen)

    def scanForTooltips(self, start: int, end: int) -> List[Hotspot]:
        """Scan pour trouver des tooltips dans une zone"""
        tooltips = []
        ptr = start

        while ptr < end - 28:
            result = self.tryParseTooltip(ptr, end)
            if result:
                tip, nextOffset = result
                tooltips.append(Hotspot(
                    index=-1,
                    offset=ptr,
                    commands=[HotspotCommand(id=8, subtype=tip.type, param=tip.text)],
                    geometry=HotspotGeometry(
                        cursorId=0,
                        pointCount=2,
                        points=[
                            Point(x=tip.rect.x1, y=tip.rect.y1),
                            Point(x=tip.rect.x2, y=tip.rect.y2)
                        ],
                        extraFlag=tip.flag
                    ),
                    isRecovered=True,
                    isTooltip=True,
                    tooltip=tip
                ))
                ptr = nextOffset
            else:
                ptr += 1

        return tooltips

    # === NOUVEAU SCANNER DE GÉOMÉTRIE ORPHELINE ===

    def scanForGeometryStructures(self, start: int, end: int, existingHotspots: List[Hotspot]) -> List[dict]:
        found = []
        ptr = start

        # On crée une map des zones déjà occupées
        occupiedZones = [(h.offset, h.offset + 200) for h in existingHotspots]

        while ptr < end - 16:
            # Si on est dans une zone déjà connue, on saute
            isInOccupied = any(z[0] <= ptr < z[1] for z in occupiedZones)
            if isInOccupied:
                ptr += 1
                continue

            val1 = self.readU32(ptr)
            val2 = self.readU32(ptr + 4)
            val3 = self.readI32(ptr + 8)

            # MODE 1 : Structure Standard [CursorID] [Count] [X]
            isCursorIdValid = val1 < 20000 or (val2 >= 3)

            if isCursorIdValid and 2 <= val2 < 50 and abs(val3) < 3000:
                pointCount = val2
                pointsSize = pointCount * 8

                if ptr + 8 + pointsSize <= end:
                    points = []
                    pPtr = ptr + 8
                    valid = True

                    for i in range(pointCount):
                        x = self.readI32(pPtr)
                        y = self.readI32(pPtr + 4)
                        if abs(x) > 3000 or abs(y) > 3000:
                            valid = False
                            break
                        points.append(Point(x=x, y=y))
                        pPtr += 8

                    if valid:
                        extraFlag = 0
                        if pPtr + 4 <= end:
                            extraFlag = self.readU32(pPtr)

                        # HEURISTIQUE BACKWARD PEEK
                        recoveredCmd = None
                        if 32 <= val1 <= 126:
                            cursorChar = chr(val1)
                            if ptr >= 4:
                                prevBytes = [self.readU8(ptr-4+i) for i in range(4)]
                                numStr = ""
                                for i in range(3, -1, -1):
                                    if 48 <= prevBytes[i] <= 57:
                                        numStr = chr(prevBytes[i]) + numStr
                                    elif prevBytes[i] == 0:
                                        pass
                                    else:
                                        break

                                if numStr:
                                    recoveredCmd = numStr + cursorChar
                                    self.log(f"  [PEEK] Commande reconstruite: \"{recoveredCmd}\" @ 0x{ptr:x}")

                        found.append({
                            'offset': ptr,
                            'geometry': HotspotGeometry(
                                cursorId=val1,
                                pointCount=pointCount,
                                points=points,
                                extraFlag=extraFlag
                            ),
                            'recoveredCmd': recoveredCmd
                        })
                        ptr = pPtr + 4
                        continue

            # MODE 2 : Structure Compacte [Count] [X] [Y]
            countCandidate = val1
            xCandidate = self.readI32(ptr + 4)
            yCandidate = self.readI32(ptr + 8)

            if 2 <= countCandidate < 50 and abs(xCandidate) < 3000 and abs(yCandidate) < 3000:
                pointCount = countCandidate
                pointsSize = pointCount * 8

                if ptr + 4 + pointsSize <= end:
                    points = []
                    pPtr = ptr + 4
                    valid = True

                    for i in range(pointCount):
                        x = self.readI32(pPtr)
                        y = self.readI32(pPtr + 4)
                        if abs(x) > 3000 or abs(y) > 3000:
                            valid = False
                            break
                        points.append(Point(x=x, y=y))
                        pPtr += 8

                    if valid:
                        extraFlag = 0
                        if pPtr + 4 <= end:
                            extraFlag = self.readU32(pPtr)

                        found.append({
                            'offset': ptr,
                            'geometry': HotspotGeometry(
                                cursorId=0,
                                pointCount=pointCount,
                                points=points,
                                extraFlag=extraFlag
                            ),
                            'recoveredCmd': None
                        })
                        ptr = pPtr + 4
                        continue

            ptr += 1

        return found

    # === LOGIQUE DE RÉCUPÉRATION ROBUSTE (GAP RECOVERY) ===

    def recoverCommandsFromGap(self, start: int, end: int) -> List[Hotspot]:
        recoveredItems = []
        ptr = start

        # Sauter le padding initial si ce sont des caractères imprimables
        if ptr < len(self.data) and 32 <= self.data[ptr] <= 126:
            backtrack = ptr
            backtrackLimit = max(0, ptr - 500)
            while backtrack > backtrackLimit and 32 <= self.data[backtrack - 1] <= 126:
                backtrack -= 1
            ptr = backtrack

        keywords = [
            ' = ', 'if ', 'then ', 'else',
            'addbmp', 'playavi', 'playwave', 'playwav', 'runprj', 'scene',
            'set_var', 'inc_var', 'dec_var', 'rundll', 'closedll', 'closewav',
            '.bmp', '.wav', '.avi', '.dll', '.vnp', '.htm',
            'font ', 'text', 'rgb', 'quit', 'save', 'load',
            'telep', 'sac', 'calc', 'bouteille', 'levure'
        ]

        while ptr < end:
            # Skip non-printable trash
            if ptr < end and (self.data[ptr] < 32 and self.data[ptr] != 0):
                ptr += 1
                continue

            tempPtr = ptr
            collectedBytes = []

            # Collect string
            while tempPtr < len(self.data) and len(collectedBytes) < 2000:
                c = self.data[tempPtr]
                if c == 0:
                    break
                if c < 32 and c not in (9, 10, 13):
                    break
                collectedBytes.append(c)
                tempPtr += 1

            tempStr = ""
            if len(collectedBytes) > 2:
                try:
                    tempStr = bytes(collectedBytes).decode('cp1252')
                except:
                    pass
            elif len(collectedBytes) == 2:
                s = bytes(collectedBytes).decode('cp1252', errors='replace')
                if re.match(r'^\d+[a-z]?$', s, re.I):
                    tempStr = s

            if len(tempStr) >= 2:
                lower = tempStr.lower()
                hasKeyword = any(k in lower for k in keywords)
                looksLikeSentence = (' ' in tempStr and re.match(r'^[A-Z0-9\xC0-\xFF]', tempStr))
                looksLikeParam = self.looksLikeScriptParam(tempStr)

                if hasKeyword or looksLikeSentence or looksLikeParam:
                    startOffset = ptr
                    cmdID = 9999
                    cmdSub = 0

                    # Tentative de récupération ID/Sub avant la chaîne
                    if ptr >= 12:
                        length = self.readU32(ptr - 4)
                        if len(tempStr) <= length < len(tempStr) + 100:
                            startOffset = ptr - 12
                            cmdID = self.readU32(startOffset)
                            cmdSub = self.readU32(startOffset + 4)

                    if cmdID == 9999 or cmdID > 10000:
                        cmdID, cmdSub = self.inferCommandType(tempStr)

                    recoveredItems.append(Hotspot(
                        index=-1,
                        offset=startOffset,
                        commands=[HotspotCommand(id=cmdID, subtype=cmdSub, param=tempStr)],
                        geometry=HotspotGeometry(cursorId=0, pointCount=0, points=[], extraFlag=0),
                        isRecovered=True
                    ))

                    ptr = tempPtr
                    continue

            if tempPtr > ptr:
                ptr = tempPtr
            else:
                ptr += 1

        return recoveredItems

    # === PASSE 2 & 3 : ANALYSE PAR CHUNK ===

    def parse(self, maxScenes: int = 100) -> ParseResult:
        self.logs = []
        sceneOffsets = self.findSceneOffsets()
        scenes = []

        gameSlotId = 0

        self.log(f"PHASE 2: Analyse de {len(sceneOffsets)} segments détectés.")

        for i in range(min(len(sceneOffsets), maxScenes)):
            start = sceneOffsets[i]
            end = sceneOffsets[i + 1] if i < len(sceneOffsets) - 1 else len(self.data)

            try:
                scene = self.parseSceneBlock(gameSlotId, start, end)

                if scene.sceneType == 'toolbar':
                    self.log(f"  [INFO] Scène 'Toolbar' à 0x{start:X} - Ignorée du mapping Slot.")
                    continue

                self.log(f"\n--- Analyse Scène #{gameSlotId} (0x{start:X} -> 0x{end:X}) ---")
                scene.id = gameSlotId
                scenes.append(scene)
                gameSlotId += 1

            except Exception as e:
                self.log(f"CRITICAL: Erreur sur segment {i}: {e}")

        return ParseResult(
            scenes=scenes,
            logs=self.logs,
            totalBytes=len(self.data)
        )

    def parseSceneBlock(self, id_val: int, start: int, limit: int) -> ParsedScene:
        # 0. DETECTION EMPTY SCENE
        if self.isEmptySlotMarker(start):
            return ParsedScene(
                id=id_val,
                offset=start,
                length=9,
                files=[],
                initScript=InitScript(offset=start, length=0, commands=[]),
                config=SceneConfig(offset=-1, flag=0, ints=[], foundSignature=False),
                hotspots=[],
                warnings=[],
                parseMethod='empty_slot',
                sceneType='empty',
                sceneName='Empty Slot'
            )

        warnings = []
        cursor = start
        detectedSceneName = None

        # 1. FILES
        files = []
        slotIndex = 1
        fileTableLimit = min(limit, start + 8192)
        isToolbarScene = False

        while cursor < fileTableLimit:
            checkSig = self.readU32(cursor)
            if self.isValidSignature(checkSig):
                break

            if self.isValidHotspotTable(cursor, limit):
                self.log(f"  [INFO] Fin de table fichiers par structure Hotspot à 0x{cursor:x}")
                break

            length = self.readU32(cursor)

            if length == 0:
                paramCheck = self.readU32(cursor + 4)
                if self.isValidSignature(paramCheck):
                    break

                if cursor + 8 <= limit and paramCheck == 0:
                    cursor += 8
                    continue

                foundNext = False
                for scan in range(1, 128):
                    probe = cursor + scan
                    if probe + 4 > limit:
                        break

                    if self.isValidSignature(self.readU32(probe)):
                        cursor = probe
                        foundNext = True
                        break

                    possibleLen = self.readU32(probe)
                    if 0 < possibleLen < 260:
                        strCheck = self.tryReadString(probe)
                        if strCheck and strCheck[0]:
                            if self.looksLikeScriptParam(strCheck[0]):
                                foundNext = False
                                break

                            if re.match(r'^[\w\s\-\.\\\/:]+$', strCheck[0]) or len(strCheck[0]) > 3:
                                self.log(f"  [RECOVERY] Saut de {scan} octets de padding à 0x{cursor:x} -> 0x{probe:x}")
                                cursor = probe
                                foundNext = True
                                break

                if foundNext:
                    continue
                break

            res = self.tryReadString(cursor)
            if not res:
                if self.isValidHotspotTable(cursor, limit):
                    self.log(f"  [INFO] Fin de table fichiers (sur échec string) par Hotspot à 0x{cursor:x}")
                    break

                recovered = False
                for scan in range(4, 64):
                    probe = cursor + scan
                    if probe + 4 > limit:
                        break

                    possibleLen = self.readU32(probe)
                    if 0 < possibleLen < 260:
                        strCheck = self.tryReadString(probe)
                        if strCheck and self.looksLikeScriptParam(strCheck[0]):
                            break
                        if strCheck and len(strCheck[0]) > 3 and re.match(r'^[\w\s\-\.\\\/:]+$', strCheck[0]):
                            self.log(f"  [RECOVERY] Structure invalide sautée (+{scan} bytes) à 0x{cursor:x}")
                            cursor = probe
                            recovered = True
                            break

                if recovered:
                    continue
                break

            filename = res[0]
            if filename.lower() == 'toolbar':
                isToolbarScene = True

            if ' if ' in filename.lower() or ' = ' in filename or ' then ' in filename.lower():
                break
            if self.looksLikeScriptParam(filename):
                self.log(f"  [INFO] Fin de table par paramètre script: \"{filename}\"")
                break

            paramOffset = res[1]
            if paramOffset + 4 > limit:
                break

            param = self.readU32(paramOffset)

            isFileExtension = bool(re.search(r'\.(bmp|wav|avi|htm|html|dll|vnp|cur|ico)$', filename, re.I))
            isEmptySlot = filename.lower() == 'empty'
            isSystemName = filename.lower() == 'toolbar'

            if slotIndex == 1 and not isFileExtension and not isEmptySlot and not isSystemName and filename:
                detectedSceneName = filename
                cursor = paramOffset + 4
                continue

            files.append(SceneFile(slot=slotIndex, filename=filename, param=param, offset=cursor))
            slotIndex += 1
            cursor = paramOffset + 4

            if filename.lower() == 'perdu.htm':
                foundWav = False
                for scan in range(200):
                    ptr = cursor + scan
                    if ptr + 14 > limit:
                        break
                    checkLen = self.readU32(ptr)
                    if checkLen == 9:
                        if self.data[ptr+4] == 112 and self.data[ptr+12] == 118:
                            self.log(f"  [FIX] Saut corruption après 'perdu.htm' (+{scan} bytes)")
                            cursor = ptr
                            foundWav = True
                            break
                if foundWav:
                    continue

            if len(files) > 500:
                break

        # 2. SEARCH CONFIG ANCHOR
        configOffset = -1
        searchLimit = min(limit, cursor + 50000)
        candidates = []
        weak_candidates = []  # Signatures sans validation hotspot stricte

        for p in range(cursor, searchLimit - 4):
            if self.isValidSignature(self.readU32(p)):
                if self.isValidHotspotTable(p + 24, searchLimit):
                    candidates.append(p)
                else:
                    # Signature trouvée mais validation hotspot échoue
                    # On la garde quand même comme candidat faible
                    weak_candidates.append(p)

        # Prioriser les candidats validés, sinon utiliser les faibles
        if candidates:
            configOffset = candidates[-1]
        elif weak_candidates:
            configOffset = weak_candidates[-1]
            warnings.append(f"[WEAK SIG] Signature config trouvée mais validation hotspot partielle")

        parseMethod = 'signature'
        scriptEnd = configOffset
        hotspotStart = -1

        if configOffset == -1:
            heuristicHotspotStart = self.scanForHotspots(cursor, limit)

            if heuristicHotspotStart != -1:
                parseMethod = 'signature' if isToolbarScene else 'heuristic_recovered'
                scriptEnd = heuristicHotspotStart
                hotspotStart = heuristicHotspotStart
                if not isToolbarScene:
                    warnings.append(f"[RECOVERY] Table Hotspots détectée heuristiquement à 0x{hotspotStart:X}")
            else:
                parseMethod = 'heuristic'
                scriptEnd = limit
                hotspotStart = limit
                warnings.append("Aucune structure de Hotspot détectée. Mode fallback.")

        # 3. INIT SCRIPT
        initScript = InitScript(offset=cursor, length=0, commands=[])

        if scriptEnd and scriptEnd > cursor:
            initScript.length = scriptEnd - cursor
            scriptPtr = cursor

            while scriptPtr < scriptEnd - 8:
                cmdOffset = scriptPtr
                cmdId = self.readU32(scriptPtr)
                scriptPtr += 4

                if cmdId in (21, 3):
                    strRes = self.tryReadString(scriptPtr + 4)
                    if strRes:
                        if 'score <= 0 then addbmp d3' in strRes[0]:
                            detectedSceneName = "Scène d3"
                        if 'score >= 0 then addbmp d2' in strRes[0]:
                            detectedSceneName = "Scène d2"
                        if 'fin2.avi' in strRes[0]:
                            detectedSceneName = "Scène AVI"

                if cmdId > 50000:
                    break

                handled = False

                if cmdId == 1 and self.readU32(scriptPtr) < 100000:
                    checkStr = self.tryReadString(scriptPtr + 4)
                    if not checkStr:
                        val = self.readU32(scriptPtr)
                        scriptPtr += 4
                        initScript.commands.append(InitCommand(
                            id=cmdId, subtype=0, param=f"Val: {val}", offset=cmdOffset
                        ))
                        handled = True
                elif cmdId == 2 and self.readU32(scriptPtr) < 100000:
                    checkStr = self.tryReadString(scriptPtr + 4)
                    if not checkStr:
                        ints = []
                        for k in range(7):
                            ints.append(self.readU32(scriptPtr))
                            scriptPtr += 4
                        initScript.commands.append(InitCommand(
                            id=cmdId, subtype=0, param=f"Zone: [{','.join(map(str, ints))}]", offset=cmdOffset
                        ))
                        handled = True

                if not handled:
                    subtype = self.readU32(scriptPtr)
                    strRes = self.tryReadString(scriptPtr + 4)

                    if strRes:
                        initScript.commands.append(InitCommand(
                            id=cmdId, subtype=subtype, param=strRes[0], offset=cmdOffset
                        ))
                        scriptPtr = strRes[1] + 4
                    else:
                        strResOld = self.tryReadString(scriptPtr)
                        if strResOld:
                            initScript.commands.append(InitCommand(
                                id=cmdId, subtype=0, param=strResOld[0], offset=cmdOffset
                            ))
                            scriptPtr = strResOld[1] + 4
                        else:
                            break

            cursor = scriptPtr

        # 4. CONFIG
        config = SceneConfig(offset=configOffset, flag=0, ints=[], foundSignature=False)
        if configOffset != -1:
            config.foundSignature = True
            config.flag = self.readU32(configOffset)
            ptr = configOffset + 4
            for k in range(5):
                config.ints.append(self.readU32(ptr))
                ptr += 4
            hotspotStart = ptr

        # 5. HOTSPOTS (STANDARD)
        hotspots = []
        hsPtr = hotspotStart

        if hsPtr != -1 and hsPtr < limit:
            objCount = self.readU32(hsPtr)
            hsPtr += 4

            if objCount < 5000:
                for i in range(objCount):
                    if hsPtr >= limit:
                        break

                    hsOffset = hsPtr
                    cmdCount = self.readU32(hsPtr)

                    # ALIGNEMENT FIX
                    if cmdCount > 1000 and hsPtr + 6 <= limit:
                        aligned = self.readU32(hsPtr + 2)
                        if aligned < 100:
                            hsPtr += 2
                            cmdCount = aligned

                    hsPtr += 4

                    if cmdCount > 200:
                        hsPtr -= 4
                        break

                    commands = []
                    cmdReadError = False

                    for c in range(cmdCount):
                        if hsPtr >= limit:
                            break

                        cmdId = self.readU32(hsPtr)
                        if cmdId > 50000:
                            cmdReadError = True
                            break

                        subtype = self.readU32(hsPtr + 4)
                        res = self.tryReadString(hsPtr + 8)

                        if res:
                            commands.append(HotspotCommand(id=cmdId, subtype=subtype, param=res[0]))
                            hsPtr = res[1]
                        else:
                            cmdReadError = True
                            break

                    if cmdReadError:
                        break

                    if hsPtr + 8 > limit:
                        break

                    cursorId = self.readU32(hsPtr)
                    pointCount = self.readU32(hsPtr + 4)

                    if pointCount > 500:
                        break

                    hsPtr += 8
                    points = []
                    hasInvalidCoords = False

                    for p in range(pointCount):
                        if hsPtr + 8 > limit:
                            break
                        x = self.readI32(hsPtr)
                        y = self.readI32(hsPtr + 4)

                        if abs(x) > 2000 or abs(y) > 2000:
                            hasInvalidCoords = True
                            self.log(f"  [WARN] Hotspot {i}: coordonnées invalides ({x}, {y})")
                            break

                        points.append(Point(x=x, y=y))
                        hsPtr += 8

                    if hasInvalidCoords:
                        break

                    # Structure hybride: commandes après géométrie
                    if cmdCount == 0 and len(points) > 0 and hsPtr + 8 < limit:
                        potentialCmdCount = self.readU32(hsPtr)

                        if potentialCmdCount == 0 and self.readU32(hsPtr + 2) > 0 and self.readU32(hsPtr + 2) < 20:
                            hsPtr += 2
                            potentialCmdCount = self.readU32(hsPtr)

                        if potentialCmdCount == 0 and self.readU32(hsPtr + 4) > 0 and self.readU32(hsPtr + 4) < 20:
                            hsPtr += 4
                            potentialCmdCount = self.readU32(hsPtr)

                        if 0 < potentialCmdCount < 20:
                            nextID = self.readU32(hsPtr + 4)
                            if nextID < 50 or nextID == 9999:
                                hsPtr += 4
                                for c in range(potentialCmdCount):
                                    if hsPtr >= limit:
                                        break
                                    cmdId = self.readU32(hsPtr)
                                    subtype = self.readU32(hsPtr + 4)
                                    res = self.tryReadString(hsPtr + 8)
                                    if res:
                                        commands.append(HotspotCommand(id=cmdId, subtype=subtype, param=res[0]))
                                        hsPtr = res[1]
                                    else:
                                        break

                    extraFlag = 0
                    if hsPtr + 4 <= limit:
                        extraFlag = self.readU32(hsPtr)
                        hsPtr += 4

                    hotspots.append(Hotspot(
                        index=i,
                        offset=hsOffset,
                        commands=commands,
                        geometry=HotspotGeometry(
                            cursorId=cursorId,
                            pointCount=pointCount,
                            points=points,
                            extraFlag=extraFlag
                        )
                    ))

        # 6. GAP RECOVERY & CLASSIFICATION INTELLIGENTE
        recoveredHotspots = []

        tooltipScanStart = min(hsPtr, cursor) if hsPtr != -1 else cursor
        detectedTooltips = self.scanForTooltips(tooltipScanStart, limit)
        if detectedTooltips:
            self.log(f"  [INFO] {len(detectedTooltips)} tooltip(s) trouvé(s)")
        recoveredHotspots.extend(detectedTooltips)

        # Récupération des commandes "orphelines"
        if scriptEnd and cursor < scriptEnd:
            recoveredHotspots.extend(self.recoverCommandsFromGap(cursor, scriptEnd))

        finalGapPtr = hsPtr if hsPtr != -1 else cursor
        if finalGapPtr < limit - 16:
            recoveredHotspots.extend(self.recoverCommandsFromGap(finalGapPtr, limit))

        # 7. DEEP GEOMETRY SCAN & MERGE INTELLIGENT (COALESCENCE)
        potentialGeometries = self.scanForGeometryStructures(finalGapPtr, limit, hotspots)
        if potentialGeometries:
            self.log(f"  [DEEP SCAN] {len(potentialGeometries)} structures géométriques orphelines.")

        # B. Sort Recovered Items by Offset
        recoveredHotspots.sort(key=lambda h: h.offset)

        mergedHotspots = list(hotspots)

        # C. Coalesce Commands
        coalescedHotspots = []
        currentGroup = None

        for item in recoveredHotspots:
            if item.isTooltip or (item.geometry and item.geometry.pointCount > 0):
                coalescedHotspots.append(item)
                currentGroup = None
                continue

            # RUPTURE DE FUSION
            isStructuralStart = any(
                c.subtype == 39 or 'comic sans' in c.param.lower() or 'arial' in c.param.lower()
                for c in item.commands
            )

            if currentGroup and isStructuralStart:
                currentGroup = None

            if currentGroup and (item.offset - currentGroup.offset < 1000):
                currentGroup.commands.extend(item.commands)
            else:
                currentGroup = item
                coalescedHotspots.append(item)

        # D. Associer Géométries aux Groupes Coalescés
        geometryPool = list(potentialGeometries)

        for cmdHotspot in coalescedHotspots:
            if cmdHotspot.isTooltip:
                mergedHotspots.append(cmdHotspot)
                continue

            if cmdHotspot.geometry and cmdHotspot.geometry.pointCount > 0:
                mergedHotspots.append(cmdHotspot)
                continue

            # Chercher une géométrie orpheline
            geoIndex = -1
            for idx, g in enumerate(geometryPool):
                if g['offset'] > cmdHotspot.offset and (g['offset'] - cmdHotspot.offset) < 2000:
                    geoIndex = idx
                    break

            if geoIndex != -1:
                geo = geometryPool[geoIndex]
                cmdHotspot.geometry = geo['geometry']
                self.log(f"  [MERGE] Commande @0x{cmdHotspot.offset:x} associée à Géométrie @0x{geo['offset']:x}")
                geometryPool.pop(geoIndex)
                mergedHotspots.append(cmdHotspot)
            else:
                hasNav = any(c.subtype == 6 or 'scene ' in c.param.lower() for c in cmdHotspot.commands)

                if hasNav:
                    mergedHotspots.append(cmdHotspot)
                else:
                    isLogic = all(
                        c.id == 3 or
                        ' = ' in c.param.lower() or ' if ' in c.param.lower() or
                        c.param.lower().startswith('run') or c.param.lower().startswith('set_') or
                        c.param.lower().startswith('inc_')
                        for c in cmdHotspot.commands
                    )

                    if isLogic:
                        for cmd in cmdHotspot.commands:
                            initScript.commands.append(InitCommand(
                                id=cmd.id,
                                subtype=cmd.subtype,
                                param=cmd.param,
                                offset=cmdHotspot.offset,
                                isRecovered=True
                            ))
                    else:
                        mergedHotspots.append(cmdHotspot)

        # Ajouter les géométries restantes
        for geo in geometryPool:
            recoveredCommands = []
            if geo.get('recoveredCmd'):
                inferred = self.inferCommandType(geo['recoveredCmd'])
                recoveredCommands.append(HotspotCommand(
                    id=inferred[0],
                    subtype=inferred[1],
                    param=geo['recoveredCmd']
                ))

            mergedHotspots.append(Hotspot(
                index=-1,
                offset=geo['offset'],
                commands=recoveredCommands,
                geometry=geo['geometry'],
                isRecovered=True
            ))

        if files and 'fin2.avi' in files[0].filename.lower():
            detectedSceneName = "Scène AVI"
        if files and 'fin perdu' in files[0].filename.lower():
            detectedSceneName = "Fin Perdu"

        sceneType = self.inferSceneType(id_val, files, mergedHotspots, isToolbarScene)

        return ParsedScene(
            id=id_val,
            offset=start,
            length=limit - start,
            files=files,
            initScript=initScript,
            config=config,
            hotspots=mergedHotspots,
            warnings=warnings,
            parseMethod=parseMethod,
            sceneType=sceneType,
            sceneName=detectedSceneName
        )

    def inferSceneType(self, id_val: int, files: List[SceneFile],
                       hotspots: List[Hotspot], isToolbar: bool) -> str:
        filenames = [f.filename.lower() for f in files]
        allFilenames = ' '.join(filenames)

        if id_val == 0 and len(files) > 50:
            return 'global_vars'
        if isToolbar or 'toolbar' in filenames:
            return 'toolbar'
        if any('vnoption' in f or 'option.dll' in f for f in filenames):
            return 'options'
        if 'credit' in allFilenames or 'générique' in allFilenames:
            return 'credits'
        if 'perdu' in allFilenames or 'gagné' in allFilenames or 'fin ' in allFilenames:
            return 'game_over'
        if any(f.startswith('fin ') for f in filenames):
            return 'game_over'
        if len(files) == 1 and filenames[0].endswith('.cur'):
            return 'unknown'

        return 'game'


def dataclass_to_dict(obj):
    """Convertit les dataclasses en dict pour JSON avec ordre exact comme référence TS"""
    if isinstance(obj, list):
        return [dataclass_to_dict(item) for item in obj]
    elif hasattr(obj, '__dataclass_fields__'):
        # Ordre des champs selon le type (pour correspondance exacte avec référence)
        field_orders = {
            'InitCommand': ['id', 'subtype', 'param', 'offset', 'isRecovered'],
            'HotspotCommand': ['id', 'subtype', 'param'],
            'SceneFile': ['slot', 'filename', 'param', 'offset'],
            'InitScript': ['offset', 'length', 'commands'],
            'SceneConfig': ['offset', 'flag', 'ints', 'foundSignature'],
            'HotspotGeometry': ['cursorId', 'pointCount', 'points', 'extraFlag'],
            'Point': ['x', 'y'],
            'Hotspot': ['index', 'offset', 'commands', 'geometry', 'isRecovered', 'isTooltip', 'tooltip'],
            'TooltipInfo': ['type', 'rect', 'flag', 'text'],
            'TooltipRect': ['x1', 'y1', 'x2', 'y2'],
            'ParsedScene': ['id', 'offset', 'length', 'files', 'initScript', 'config', 'hotspots', 'warnings', 'parseMethod', 'sceneType', 'sceneName'],
            'ParseResult': ['scenes', 'logs', 'totalBytes'],
        }

        class_name = obj.__class__.__name__
        fields = field_orders.get(class_name, list(obj.__dataclass_fields__.keys()))

        result = {}
        for field_name in fields:
            if field_name in obj.__dataclass_fields__:
                value = getattr(obj, field_name)
                if value is not None:
                    result[field_name] = dataclass_to_dict(value)
        return result
    else:
        return obj


def main():
    if len(sys.argv) < 2:
        print("Usage: python vnd_parser.py <fichier.vnd> [max_scenes]")
        sys.exit(1)

    vnd_file = sys.argv[1]
    max_scenes = int(sys.argv[2]) if len(sys.argv) > 2 else 100

    with open(vnd_file, 'rb') as f:
        data = f.read()

    parser = VNDSequentialParser(data)
    result = parser.parse(max_scenes)

    result_dict = dataclass_to_dict(result)

    output_file = vnd_file + '.parsed.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result_dict, f, indent=2, ensure_ascii=False)

    print(f"Parsé {len(result.scenes)} scènes -> {output_file}")

    for log in result.logs[-20:]:
        print(log)


if __name__ == '__main__':
    main()
