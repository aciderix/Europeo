import { ParseResult, ParsedScene, SceneFile, InitScript, SceneConfig, Hotspot, HotspotCommand, InitCommand, TooltipInfo, SceneType } from '../types';

export class VNDSequentialParser {
  private data: DataView;
  private uint8Data: Uint8Array;
  private textDecoder: TextDecoder;
  private logs: string[] = [];

  constructor(buffer: ArrayBuffer) {
    this.data = new DataView(buffer);
    this.uint8Data = new Uint8Array(buffer);
    this.textDecoder = new TextDecoder('windows-1252');
  }

  private log(msg: string) {
    this.logs.push(msg);
    // console.log(msg); 
  }

  // --- PRIMITIVES DE LECTURE SÉCURISÉES ---

  private readU8(offset: number): number {
    if (offset >= this.data.byteLength) return 0;
    return this.data.getUint8(offset);
  }

  private readU32(offset: number): number {
    if (offset + 4 > this.data.byteLength) return 0;
    return this.data.getUint32(offset, true);
  }

  private readI32(offset: number): number {
    if (offset + 4 > this.data.byteLength) return 0;
    return this.data.getInt32(offset, true);
  }

  // Lit une chaîne Pascal (Len + Bytes) sans avancer un curseur global
  private tryReadString(offset: number): { text: string, nextOffset: number } | null {
    if (offset + 4 > this.data.byteLength) return null;
    const len = this.readU32(offset);
    
    // Sanity check longueur
    if (len > 5000) return null; 
    if (offset + 4 + len > this.data.byteLength) return null;

    if (len === 0) return { text: "", nextOffset: offset + 4 };

    // Vérification de validité stricte pour éviter le binaire
    let binaryCount = 0;
    for (let i = 0; i < len; i++) {
        const char = this.uint8Data[offset + 4 + i];
        // Accepte Tab (9), LF (10), CR (13) et les caractères imprimables >= 32
        if (char < 32 && char !== 9 && char !== 10 && char !== 13) {
            binaryCount++;
        }
    }
    
    // Si plus de 10% de caractères bizarres, on rejette
    if (binaryCount > 0 && binaryCount > len * 0.1) return null;

    const strBytes = this.uint8Data.slice(offset + 4, offset + 4 + len);
    const text = this.textDecoder.decode(strBytes).replace(/\0/g, ''); // Clean nulls
    return { text, nextOffset: offset + 4 + len };
  }

  // --- SCANNER HEURISTIQUE HOTSPOTS ---
  private scanForHotspots(startOffset: number, limitOffset: number): number {
      // Scan octet par octet pour trouver une structure de hotspot valide
      for (let ptr = startOffset; ptr < limitOffset - 16; ptr++) {
          if (this.isValidHotspotTable(ptr, limitOffset)) {
              return ptr;
          }
      }
      return -1;
  }

  private isValidHotspotTable(offset: number, limit: number): boolean {
      let ptr = offset;
      if (ptr + 4 > limit) return false;
      
      const objCount = this.readU32(ptr);
      ptr += 4;

      if (objCount > 200) return false;
      if (objCount === 0) return (limit - ptr) < 32; 

      try {
          for (let i = 0; i < objCount; i++) {
              if (ptr + 4 > limit) return false;
              const cmdCount = this.readU32(ptr);
              ptr += 4;

              if (cmdCount > 100) return false; 

              for (let c = 0; c < cmdCount; c++) {
                  if (ptr + 8 > limit) return false;
                  ptr += 8; // ID + Subtype
                  const res = this.tryReadString(ptr);
                  if (!res) return false;
                  ptr = res.nextOffset;
              }

              if (ptr + 8 > limit) return false;
              const cursorId = this.readU32(ptr);
              if (cursorId > 1000) return false; 
              ptr += 4;

              const pointCount = this.readU32(ptr);
              ptr += 4;
              
              if (pointCount > 200) return false;

              const pointsSize = pointCount * 8;
              if (ptr + pointsSize > limit) return false;
              ptr += pointsSize;

              if (ptr + 4 <= limit) ptr += 4; // Extra Flag
          }
          return true;
      } catch (e) {
          return false;
      }
  }

  // --- PASSE 1 : CARTOGRAPHIE ---

  /**
   * Vérifie s'il y a une signature 0xFFFFFFDB dans une plage donnée
   */
  private hasSignatureInRange(startOffset: number, endOffset: number): boolean {
    for (let i = startOffset; i < endOffset - 4; i++) {
      if (this.readU32(i) === 0xFFFFFFDB) {
        return true;
      }
    }
    return false;
  }

  /**
   * Compte les occurrences de "Empty" (format Pascal: len=5 + "Empty") dans une plage
   * Ces marqueurs indiquent des slots de scène vides dans le jeu
   */
  private countEmptyMarkersInRange(startOffset: number, endOffset: number): number {
    // Pattern: 05 00 00 00 45 6D 70 74 79 (len=5 + "Empty")
    const pattern = [0x05, 0x00, 0x00, 0x00, 0x45, 0x6D, 0x70, 0x74, 0x79];
    let count = 0;

    for (let i = startOffset; i < endOffset - pattern.length; i++) {
      let match = true;
      for (let j = 0; j < pattern.length; j++) {
        if (this.uint8Data[i + j] !== pattern[j]) {
          match = false;
          break;
        }
      }
      if (match) {
        count++;
        i += pattern.length - 1;
      }
    }

    return count;
  }

  private findSceneOffsets(): number[] {
    const offsets: number[] = [];
    let ptr = 0;
    const len = this.data.byteLength;

    this.log("PHASE 1: Scanning pour les tables de fichiers...");

    // HYBRID: Détecter global_vars (Scene 0) AVANT les autres scènes
    const globalVarsOffset = this.detectGlobalVars();
    if (globalVarsOffset !== null) {
        offsets.push(globalVarsOffset);
        ptr = globalVarsOffset + 1; // Continue après global_vars
        this.log(`  [+] Scene 0 (global_vars) détectée @ 0x${globalVarsOffset.toString(16).toUpperCase()}`);
    }

    while (ptr < len - 100) {
        const tableEnd = this.isValidFileTable(ptr);

        if (tableEnd !== -1 && tableEnd > ptr) {
            offsets.push(ptr);
            this.log(`  [+] Scène @ 0x${ptr.toString(16).toUpperCase()} (Table -> 0x${tableEnd.toString(16).toUpperCase()})`);
            ptr = tableEnd;
        } else {
            ptr++;
        }
    }

    return offsets;
  }

  // HYBRID: Détecter global_vars scene à l'offset de départ
  private detectGlobalVars(): number | null {
      // Chercher file table avec 50+ fichiers dans les 0x60-0x120 premiers octets
      for (let offset = 0x60; offset < 0x120; offset++) {
          const tableEnd = this.isValidFileTable(offset);
          if (tableEnd !== -1) {
              // Compter les fichiers
              let fileCount = 0;
              let ptr = offset;

              while (ptr < tableEnd && ptr < offset + 8192) {
                  if (ptr + 4 > this.data.byteLength) break;
                  const len = this.readU32(ptr);

                  // Padding
                  if (len === 0) {
                      ptr += 8;
                      continue;
                  }

                  if (len > 500) break;

                  const res = this.tryReadString(ptr);
                  if (!res) break;

                  const param = this.readU32(res.nextOffset);
                  ptr = res.nextOffset + 4;
                  fileCount++;

                  if (fileCount > 500) break; // Safety
              }

              if (fileCount > 50) {
                  this.log(`  [HYBRID] global_vars détecté @ 0x${offset.toString(16).toUpperCase()} avec ${fileCount} fichiers`);
                  return offset;
              }
          }
      }
      return null;
  }

  /**
   * Vérifie si une structure de table de fichiers commence à 'offset'.
   * Retourne l'offset de fin de la table si valide, sinon -1.
   * Gère le "Padding" (trous de zéros) typique des scènes système.
   */
  private isValidFileTable(offset: number): number {
      let current = offset;
      let validSlots = 0;
      let hasExtensions = 0;
      let foundSpecificSignature = false;
      let foundEndSignature = false;
      
      // AUGMENTATION CRITIQUE : Scène 0 a 201 slots.
      const maxSlotsToScan = 500; 

      for (let i = 0; i < maxSlotsToScan; i++) { 
          if (current + 4 > this.data.byteLength) break;

          // Check for Magic End Signature immediately (Config start)
          if (this.readU32(current) === 0xFFFFFFDB) {
              foundEndSignature = true;
              break; 
          }

          const len = this.readU32(current);
          
          // 1. Gestion du Padding (Blocs de zéros)
          if (len === 0) {
              const paramCheck = this.readU32(current + 4);
              if (paramCheck === 0xFFFFFFDB) {
                 foundEndSignature = true;
                 break; // Signature trouvée dans le paramètre
              }

              if (current + 8 <= this.data.byteLength && paramCheck === 0) {
                  current += 8;
                  continue; // C'est du padding, on continue
              }
              // Si len=0 mais param!=0, c'est probablement la fin (début script)
              break; 
          }

          // 2. Lecture normale
          if (len > 500) break; // Sanity check

          const res = this.tryReadString(current);
          if (!res) break; 

          if (res.nextOffset + 4 > this.data.byteLength) break;
          const param = this.readU32(res.nextOffset);
          
          // Check basique sur le paramètre
          if (param > 0xFFFFFF && param !== 0xFFFFFFDB) break; 

          const name = res.text.toLowerCase();
          
          // Détection de fin de table par collision avec du script
          if (name.includes(' if ') || name.includes(' = ') || name.includes(' then ') || name.startsWith('run')) {
              break;
          }

          if (name.length > 0 && name !== "empty") {
              if (name === "toolbar") foundSpecificSignature = true;
              if (/\.(bmp|wav|avi|htm|html|dll|vnp|cur|ico)$/.test(name)) hasExtensions++;
          }

          current = res.nextOffset + 4; 
          validSlots++;
      }
      
      // Validation ASSOUPLIE pour capturer toutes les scènes :
      const isToolbar = foundSpecificSignature;
      const isEndSig = foundEndSignature;

      // NOUVELLE LOGIQUE : Accepter si :
      // 1. On a trouvé toolbar
      // 2. On a trouvé la signature de fin ET au moins 1 slot valide
      // 3. On a au moins 1 slot avec extension valide
      // 4. On a plus de 50 slots (variables globales)
      const isHeuristic = (validSlots >= 1 && hasExtensions >= 1) || (validSlots > 50);

      if (isToolbar || (isEndSig && validSlots >= 1) || isHeuristic) {
          return current; // Retourne la position APRES la table
      }

      // NOUVEAU : Vérifier si la signature 0xFFFFFFDB est juste après quelques octets
      // Cela indique une scène avec peu de fichiers
      for (let probe = current; probe < current + 100 && probe < this.data.byteLength - 4; probe++) {
          if (this.readU32(probe) === 0xFFFFFFDB && validSlots >= 1) {
              return probe; // Retourne la position de la signature
          }
      }

      return -1;
  }

  // --- INTELLIGENCE : INFÉRENCE DE TYPE ---
  private inferCommandType(text: string): { id: number, subtype: number } {
      const lower = text.toLowerCase();
      
      // Média (ID 1)
      if (lower.endsWith('.wav')) return { id: 1, subtype: 11 }; // Audio FX
      if (lower.endsWith('.avi')) return { id: 1, subtype: 9 };  // Video
      
      // Logique / Script (ID 3)
      if (lower.includes(' = ') || lower.startsWith('if ') || lower.includes(' then ')) return { id: 3, subtype: 21 }; // Script
      if (lower.startsWith('runprj') || lower.startsWith('rundll') || lower.startsWith('scene ')) return { id: 3, subtype: 0 }; // Sys
      if (lower.endsWith('.dll')) return { id: 3, subtype: 5 };
      
      // Graphique / Affichage (ID 0)
      if (lower.startsWith('font ')) return { id: 0, subtype: 39 }; // Font config
      if (lower.includes('addbmp') || lower.includes('playbmp')) return { id: 0, subtype: 24 }; // Image
      if (lower.endsWith('.bmp')) return { id: 0, subtype: 27 }; // Overlay Image

      // Par défaut
      return { id: 9999, subtype: 0 }; // Inconnu
  }

  // --- DÉTECTION DE STRUCTURE TOOLTIP ---
  // Structure: [Type:DWORD] [x1:DWORD] [y1:DWORD] [x2:DWORD] [y2:DWORD] [flag:DWORD] [strLen:DWORD] [text...]
  private tryParseTooltip(offset: number, limit: number): { tooltip: TooltipInfo, nextOffset: number } | null {
      // Besoin de minimum 28 bytes (7 DWORDs) + au moins 1 char
      if (offset + 29 > limit) return null;

      const type = this.readU32(offset);
      const x1 = this.readU32(offset + 4);
      const y1 = this.readU32(offset + 8);
      const x2 = this.readU32(offset + 12);
      const y2 = this.readU32(offset + 16);
      const flag = this.readU32(offset + 20);
      const strLen = this.readU32(offset + 24);

      // Validations STRICTES pour identifier une vraie structure tooltip
      if (type > 20) return null;
      if (x1 > 800 || y1 > 600 || x2 > 800 || y2 > 600) return null;
      if (x2 < x1) return null;
      if (y2 < y1) return null;

      const width = x2 - x1;
      const height = y2 - y1;
      if (width < 10 || height < 10) return null;

      if (flag > 10) return null;
      if (strLen < 2 || strLen > 100) return null;
      if (offset + 28 + strLen > limit) return null;

      // Vérifier que le texte est PROPRE (pas de caractères de contrôle)
      let validChars = 0;
      let controlChars = 0;
      for (let i = 0; i < strLen; i++) {
          const c = this.uint8Data[offset + 28 + i];
          if (c < 32 && c !== 0) controlChars++;
          if ((c >= 32 && c <= 126) || (c >= 128 && c <= 255)) validChars++;
      }

      if (controlChars > 0) return null;
      if (validChars < strLen * 0.9) return null;

      const textBytes = this.uint8Data.slice(offset + 28, offset + 28 + strLen);
      const text = this.textDecoder.decode(textBytes).replace(/\0/g, '').trim();

      if (text.length < 2) return null;

      this.log(`  [TOOLTIP] Détecté @ 0x${offset.toString(16)}: "${text}" rect(${x1},${y1},${x2},${y2})`);

      return {
          tooltip: { type, rect: { x1, y1, x2, y2 }, flag, text },
          nextOffset: offset + 28 + strLen
      };
  }

  // Scan pour trouver des tooltips dans une zone
  private scanForTooltips(start: number, end: number): Hotspot[] {
      const tooltips: Hotspot[] = [];
      let ptr = start;

      while (ptr < end - 28) {
          const result = this.tryParseTooltip(ptr, end);
          if (result) {
              tooltips.push({
                  index: -1,
                  offset: ptr,
                  commands: [{
                      id: 8,  // Opcode 'h' = tooltips
                      subtype: result.tooltip.type,
                      param: result.tooltip.text
                  }],
                  geometry: {
                      cursorId: 0,
                      pointCount: 2,
                      points: [
                          { x: result.tooltip.rect.x1, y: result.tooltip.rect.y1 },
                          { x: result.tooltip.rect.x2, y: result.tooltip.rect.y2 }
                      ],
                      extraFlag: result.tooltip.flag
                  },
                  isRecovered: true,
                  isTooltip: true,
                  tooltip: result.tooltip
              });
              ptr = result.nextOffset;
          } else {
              ptr++;
          }
      }
      return tooltips;
  }

  // --- LOGIQUE DE RÉCUPÉRATION ROBUSTE (GAP RECOVERY) ---
  // Retourne des objets Hotspot complets (avec géométrie si trouvée)
  private recoverCommandsFromGap(start: number, end: number): Hotspot[] {
      const recoveredItems: Hotspot[] = [];
      let ptr = start;

      // 1. ALIGNEMENT INITIAL
      if (ptr < this.data.byteLength && this.uint8Data[ptr] >= 32 && this.uint8Data[ptr] <= 126) {
          let backtrack = ptr;
          const backtrackLimit = Math.max(0, ptr - 500);
          while (backtrack > backtrackLimit && this.uint8Data[backtrack - 1] >= 32 && this.uint8Data[backtrack - 1] <= 126) {
              backtrack--;
          }
          ptr = backtrack;
      }

      const keywords = [
          ' = ', 'if ', 'then ', 'else', 
          'addbmp', 'playavi', 'playwave', 'playwav', 'runprj', 'scene', 
          'set_var', 'inc_var', 'dec_var', 'rundll', 'closedll', 'closewav',
          '.bmp', '.wav', '.avi', '.dll', '.vnp', '.htm',
          'font ', 'text', 'rgb', 'quit', 'save', 'load',
          // Identifiants de ressources courts fréquents
          'telep', 'sac', 'calc', 'bouteille', 'levure'
      ];

      while (ptr < end) {
          if (ptr < end && (this.uint8Data[ptr] < 32 || this.uint8Data[ptr] > 126)) {
              ptr++;
              continue;
          }

          let tempPtr = ptr;
          let tempStr = "";
          
          while (tempPtr < this.data.byteLength && tempStr.length < 1000) {
              const c = this.uint8Data[tempPtr];
              if (c < 32 && c !== 0) break; 
              if (c === 0) break; 
              if (c > 126) break; 
              tempStr += String.fromCharCode(c);
              tempPtr++;
          }

          if (tempStr.length > 2) { 
              const lower = tempStr.toLowerCase();
              const hasKeyword = keywords.some(k => lower.includes(k));
              const looksLikeSentence = (tempStr.includes(' ') && /^[A-Z0-9]/.test(tempStr));

              if (hasKeyword || looksLikeSentence) {
                  let startOffset = ptr;
                  let cmdID = 9999;
                  let cmdSub = 0;

                  if (ptr >= 12) { 
                      const len = this.readU32(ptr - 4);
                      if (len >= tempStr.length && len < tempStr.length + 100) {
                          startOffset = ptr - 12;
                          cmdID = this.readU32(startOffset);
                          cmdSub = this.readU32(startOffset + 4);
                      }
                  }

                  if (cmdID === 9999 || cmdID > 10000) {
                      const inferred = this.inferCommandType(tempStr);
                      cmdID = inferred.id;
                      cmdSub = inferred.subtype;
                  }

                  // 2. RECHERCHE DE GÉOMÉTRIE APRÈS LA CHAÎNE
                  let geomPtr = tempPtr;
                  
                  // Sauter le padding (nulls)
                  while(geomPtr < end && this.uint8Data[geomPtr] === 0) {
                      geomPtr++;
                  }

                  let geometry = { cursorId: 0, pointCount: 0, points: [] as any[], extraFlag: 0 };
                  
                  if (geomPtr + 8 <= end) {
                      const potentialCursor = this.readU32(geomPtr);
                      const potentialPoints = this.readU32(geomPtr + 4);

                      // CRUCIAL : VÉRIFICATION ANTI-DESYNC
                      const knownCommandIDs = [0, 1, 2, 3, 4, 5, 6, 21, 27, 28];
                      const looksLikeNextCommand = knownCommandIDs.includes(potentialCursor);

                      if (!looksLikeNextCommand && potentialCursor < 200 && potentialPoints > 0 && potentialPoints < 50) {
                          const sizeBytes = potentialPoints * 8;
                          if (geomPtr + 8 + sizeBytes <= end) {
                              // Lire les points temporairement pour validation
                              const tempPoints: { x: number, y: number }[] = [];
                              let ptReadPtr = geomPtr + 8;
                              let validGeometry = true;

                              for(let p=0; p<potentialPoints; p++) {
                                  const x = this.readI32(ptReadPtr);
                                  const y = this.readI32(ptReadPtr+4);

                                  // VALIDATION CRITIQUE : Rejeter coordonnées aberrantes (Buffer Overrun)
                                  // Les écrans VGA/SVGA max ~800x600, on tolère jusqu'à 2000 pour marges
                                  if (Math.abs(x) > 2000 || Math.abs(y) > 2000) {
                                      validGeometry = false;
                                      break;
                                  }

                                  tempPoints.push({ x, y });
                                  ptReadPtr += 8;
                              }

                              if (validGeometry) {
                                  geometry.cursorId = potentialCursor;
                                  geometry.pointCount = potentialPoints;
                                  geometry.points = tempPoints;
                                  if (ptReadPtr + 4 <= end) {
                                      geometry.extraFlag = this.readU32(ptReadPtr);
                                      ptReadPtr += 4;
                                  }
                                  tempPtr = ptReadPtr;
                              }
                              // Si géométrie invalide, on garde geometry vide (pas de points)
                          }
                      }
                  }
                  
                  recoveredItems.push({
                      index: -1,
                      offset: startOffset,
                      commands: [{ id: cmdID, subtype: cmdSub, param: tempStr }],
                      geometry: geometry,
                      isRecovered: true
                  });
                  
                  ptr = tempPtr;
                  continue;
              }
          }
          
          if (tempPtr > ptr) {
              ptr = tempPtr;
          } else {
              ptr++;
          }
      }
      return recoveredItems;
  }

  // --- PASSE 2 & 3 : ANALYSE PAR CHUNK ---

  public parse(maxScenes: number = 100): ParseResult {
    this.logs = [];
    const sceneOffsets = this.findSceneOffsets();
    const scenes: ParsedScene[] = [];

    this.log(`PHASE 2: Analyse de ${sceneOffsets.length} segments détectés.`);

    for (let i = 0; i < Math.min(sceneOffsets.length, maxScenes); i++) {
        const start = sceneOffsets[i];
        const end = (i < sceneOffsets.length - 1) ? sceneOffsets[i+1] : this.data.byteLength;
        
        try {
            this.log(`\n--- Analyse Scène #${i} (0x${start.toString(16).toUpperCase()} -> 0x${end.toString(16).toUpperCase()}) ---`);
            const scene = this.parseSceneBlock(i, start, end);
            scenes.push(scene);
        } catch (e: any) {
            this.log(`CRITICAL: Erreur fatale sur scène ${i}: ${e.message}`);
        }
    }

    return { scenes, logs: this.logs, totalBytes: this.data.byteLength };
  }

  private parseSceneBlock(id: number, start: number, limit: number): ParsedScene {
      const warnings: string[] = [];
      let cursor = start;

      // 1. FILES
      const files: SceneFile[] = [];
      let slotIndex = 1;
      const fileTableLimit = Math.min(limit, start + 8192); // Encore augmenté pour Scène 0 (Vars)

      let isToolbarScene = false;

      while (cursor < fileTableLimit) {
          // Check signature Config (Fin de fichiers / Script)
          const checkSig = this.readU32(cursor);
          if (checkSig === 0xFFFFFFDB) break;

          const len = this.readU32(cursor);
          
          // GESTION PADDING DANS L'EXTRACTION
          if (len === 0) {
              const paramCheck = this.readU32(cursor + 4);
              if (paramCheck === 0xFFFFFFDB) break; // Signature trouvée dans le paramètre

              if (cursor + 8 <= limit && paramCheck === 0) {
                  cursor += 8; // Skip empty slot
                  continue; 
              }
              break;
          }

          const res = this.tryReadString(cursor);
          if (!res) break;

          const filename = res.text;
          if (filename.toLowerCase() === 'toolbar') isToolbarScene = true;

          // Si on tombe sur du script, on arrête la table de fichiers
          if (filename.toLowerCase().includes(' if ') || filename.includes(' = ') || filename.includes(' then ')) break;

          const paramOffset = res.nextOffset;
          if (paramOffset + 4 > limit) break;
          
          const param = this.readU32(paramOffset);
          
          files.push({ slot: slotIndex++, filename, param, offset: cursor });
          cursor = paramOffset + 4;
          
          // Sécurité : Max 500 pour inclure toutes les variables globales
          if (files.length > 500) break; 
      }

      // 2. SEARCH CONFIG ANCHOR
      let configOffset = -1;
      const searchLimit = Math.min(limit, cursor + 50000); 
      const candidates: number[] = [];

      for (let p = cursor; p < searchLimit - 4; p++) {
          if (this.uint8Data[p] === 0xDB && this.uint8Data[p+1] === 0xFF && this.uint8Data[p+2] === 0xFF && this.uint8Data[p+3] === 0xFF) {
              if (this.isValidHotspotTable(p + 24, searchLimit)) {
                  candidates.push(p);
              }
          }
      }

      if (candidates.length > 0) {
          configOffset = candidates[candidates.length - 1];
      }

      let parseMethod: ParsedScene['parseMethod'] = 'signature';
      let scriptEnd = configOffset;
      let hotspotStart = -1;

      if (configOffset === -1) {
          // SPECIAL CASE FOR TOOLBAR: It often lacks the signature but has valid hotspots
          const heuristicHotspotStart = this.scanForHotspots(cursor, limit);
          
          if (heuristicHotspotStart !== -1) {
              parseMethod = isToolbarScene ? 'signature' : 'heuristic_recovered'; // Treat Toolbar as valid
              scriptEnd = heuristicHotspotStart;
              hotspotStart = heuristicHotspotStart;
              if (!isToolbarScene) warnings.push(`[RECOVERY] Table Hotspots détectée heuristiquement à 0x${hotspotStart.toString(16).toUpperCase()}`);
          } else {
              parseMethod = 'heuristic';
              scriptEnd = limit;
              hotspotStart = limit;
              warnings.push("Aucune structure de Hotspot détectée. Mode fallback.");
          }
      }

      // 3. INIT SCRIPT
      const initScript: InitScript = { offset: cursor, length: 0, commands: [] };
      
      if (scriptEnd > cursor) {
          initScript.length = scriptEnd - cursor;
          let scriptPtr = cursor;
          
          while (scriptPtr < scriptEnd - 8) { 
             const cmdOffset = scriptPtr;
             const id = this.readU32(scriptPtr);
             scriptPtr += 4;

             if (id > 50000) break; // Fin détectée

             let handled = false;

             if (id === 1 && this.readU32(scriptPtr) < 100000) { 
                 const checkStr = this.tryReadString(scriptPtr + 4);
                 if (!checkStr) {
                     const val = this.readU32(scriptPtr);
                     scriptPtr += 4;
                     initScript.commands.push({ id, subtype: 0, param: `Val: ${val}`, offset: cmdOffset });
                     handled = true;
                 }
             }
             else if (id === 2 && this.readU32(scriptPtr) < 100000) { 
                 const checkStr = this.tryReadString(scriptPtr + 4);
                 if (!checkStr) {
                     const ints = [];
                     for(let k=0; k<7; k++) { ints.push(this.readU32(scriptPtr)); scriptPtr += 4; }
                     initScript.commands.push({ id, subtype: 0, param: `Zone: [${ints.join(',')}]`, offset: cmdOffset });
                     handled = true;
                 }
             }

             if (!handled) {
                 const subtype = this.readU32(scriptPtr);
                 const strRes = this.tryReadString(scriptPtr + 4); 
                 
                 if (strRes) {
                     const param = this.readU32(strRes.nextOffset); 
                     initScript.commands.push({ id, subtype, param: strRes.text, offset: cmdOffset });
                     scriptPtr = strRes.nextOffset + 4;
                 } else {
                     const strResOld = this.tryReadString(scriptPtr);
                     if (strResOld) {
                         const param = this.readU32(strResOld.nextOffset);
                         initScript.commands.push({ id, subtype: 0, param: strResOld.text, offset: cmdOffset });
                         scriptPtr = strResOld.nextOffset + 4;
                     } else {
                         // Structure cassée -> Stop pour le Gap Recovery
                         break; 
                     }
                 }
             }
          }
          cursor = scriptPtr; 
      }

      // 4. CONFIG
      const config: SceneConfig = { offset: configOffset, flag: 0, ints: [], foundSignature: false };
      if (configOffset !== -1) {
          config.foundSignature = true;
          config.flag = this.readU32(configOffset); 
          let ptr = configOffset + 4;
          for(let k=0; k<5; k++) {
              config.ints.push(this.readU32(ptr));
              ptr += 4;
          }
          hotspotStart = ptr;
      }

      // 5. HOTSPOTS (STANDARD)
      const hotspots: Hotspot[] = [];
      let hsPtr = hotspotStart;
      let declaredObjCount: number | undefined = undefined; // HYBRID: Nombre de hotspots déclaré

      if (hsPtr !== -1 && hsPtr < limit) {
          const objCount = this.readU32(hsPtr);
          declaredObjCount = objCount; // HYBRID: Stocker pour validation
          hsPtr += 4;

          if (objCount < 5000) { 
              for (let i = 0; i < objCount; i++) {
                  if (hsPtr >= limit) break;
                  
                  const hsOffset = hsPtr;
                  const cmdCount = this.readU32(hsPtr);
                  hsPtr += 4;
                  
                  if (cmdCount > 200) {
                      hsPtr -= 4; 
                      break; 
                  }

                  const commands: HotspotCommand[] = [];
                  let cmdReadError = false;

                  for (let c = 0; c < cmdCount; c++) {
                      if (hsPtr >= limit) break;
                      
                      const id = this.readU32(hsPtr);
                      if (id > 50000) {
                          cmdReadError = true;
                          break;
                      }

                      const subtype = this.readU32(hsPtr + 4);
                      const res = this.tryReadString(hsPtr + 8);
                      
                      if (res) {
                          commands.push({ id, subtype, param: res.text });
                          hsPtr = res.nextOffset;
                      } else {
                          cmdReadError = true;
                          break;
                      }
                  }

                  if (cmdReadError) break;

                  if (hsPtr + 8 > limit) break;
                  
                  const cursorId = this.readU32(hsPtr);
                  const pointCount = this.readU32(hsPtr + 4);
                  
                  if (pointCount > 500 || cursorId > 5000) break;

                  hsPtr += 8;
                  const points = [];
                  let hasInvalidCoords = false;

                  for(let p=0; p<pointCount; p++) {
                      if (hsPtr + 8 > limit) break;
                      const x = this.readI32(hsPtr);
                      const y = this.readI32(hsPtr+4);

                      // HYBRID: Limites assouplies pour scènes scrollables
                      const MAX_COORD_STRICT = 2000;
                      const MAX_COORD_SCROLLABLE = 5000;

                      if (Math.abs(x) > MAX_COORD_SCROLLABLE || Math.abs(y) > MAX_COORD_SCROLLABLE) {
                          hasInvalidCoords = true;
                          this.log(`  [WARN] Hotspot ${i}: coordonnées invalides (${x}, ${y}) - rejeté`);
                          break;
                      } else if (Math.abs(x) > MAX_COORD_STRICT || Math.abs(y) > MAX_COORD_STRICT) {
                          // Scène scrollable (warning mais continue)
                          this.log(`  [INFO] Hotspot ${i}: scène scrollable détectée (${x}, ${y})`);
                          warnings.push(`Scène scrollable: coordonnées (${x}, ${y})`);
                      }

                      points.push({ x, y });
                      hsPtr += 8;
                  }

                  // Si coordonnées invalides, arrêter le parsing des hotspots
                  if (hasInvalidCoords) break;

                  let extraFlag = 0;
                  if (hsPtr + 4 <= limit) {
                      extraFlag = this.readU32(hsPtr);
                      hsPtr += 4;
                  }

                  hotspots.push({
                      index: i,
                      offset: hsOffset,
                      commands,
                      geometry: { cursorId, pointCount, points, extraFlag }
                  });
              }
          }
      }

      // 6. GAP RECOVERY & CLASSIFICATION INTELLIGENTE
      const recoveredHotspots: Hotspot[] = [];

      // Scanner toute la zone après les hotspots standards pour les tooltips
      const tooltipScanStart = hsPtr !== -1 ? Math.min(hsPtr, cursor) : cursor;
      const detectedTooltips = this.scanForTooltips(tooltipScanStart, limit);
      if (detectedTooltips.length > 0) {
          this.log(`  [INFO] ${detectedTooltips.length} tooltip(s) trouvé(s)`);
      }
      recoveredHotspots.push(...detectedTooltips);

      // Zone 1: Le reste du bloc de script
      if (cursor < scriptEnd) {
          recoveredHotspots.push(...this.recoverCommandsFromGap(cursor, scriptEnd));
      }

      // Zone 2: Le "No Man's Land" final
      let finalGapPtr = hsPtr !== -1 ? hsPtr : cursor;
      if (finalGapPtr < limit - 16) {
          recoveredHotspots.push(...this.recoverCommandsFromGap(finalGapPtr, limit));
      }

      if (recoveredHotspots.length > 0) {
          let logicCount = 0;
          let orphanCount = 0;
          let tooltipCount = 0;

          recoveredHotspots.forEach(hs => {
              // Les tooltips vont directement dans hotspots
              if (hs.isTooltip) {
                  hotspots.push(hs);
                  tooltipCount++;
                  return;
              }

              const cmd = hs.commands[0];
              const looksLikeLogic = (cmd.id === 3) || cmd.param.includes(' = ') || cmd.param.includes('then ') || cmd.param.startsWith('run');
              const hasGeometry = hs.geometry.pointCount > 0;

              if (looksLikeLogic && !hasGeometry) {
                  initScript.commands.push({
                      id: cmd.id,
                      subtype: cmd.subtype,
                      param: cmd.param,
                      offset: hs.offset,
                      isRecovered: true
                  });
                  logicCount++;
              } else {
                  hotspots.push(hs);
                  orphanCount++;
              }
          });

          if (tooltipCount > 0) warnings.push(`${tooltipCount} tooltips détectés.`);
          if (logicCount > 0) warnings.push(`${logicCount} commandes logiques récupérées.`);
          if (orphanCount > 0) warnings.push(`${orphanCount} éléments interactifs récupérés.`);
      }

      // Inférer le type de scène
      const sceneType = this.inferSceneType(id, files, hotspots, isToolbarScene);

      // Compter les marqueurs "Empty" dans le binaire (scan direct)
      const emptyCount = this.countEmptyMarkersInRange(start, limit);

      // HYBRID: Calculer objCountValid
      const objCountValid = declaredObjCount !== undefined ? hotspots.length === declaredObjCount : undefined;

      // HYBRID: Assigner confidence selon parseMethod
      let confidence: 'HIGH' | 'MEDIUM' | 'LOW' = 'MEDIUM';
      if (parseMethod === 'signature') {
          confidence = 'HIGH'; // Scène avec signature 0xFFFFFFDB
      } else if (parseMethod === 'heuristic_recovered' || parseMethod === 'heuristic') {
          if (sceneType === 'global_vars') {
              confidence = 'HIGH'; // global_vars très fiable (50+ fichiers)
          } else {
              confidence = 'MEDIUM'; // Récupération heuristique
          }
      } else if (parseMethod === 'empty_slot') {
          confidence = 'HIGH'; // Empty slot clairement identifié
      }

      // HYBRID: Extraire sceneName du premier fichier (si applicable)
      const sceneName = files.length > 0 && files[0].filename.toLowerCase() !== 'toolbar'
          ? files[0].filename.replace(/\.(bmp|wav|avi|htm|html|dll)$/i, '')
          : undefined;

      return {
          id,
          offset: start,
          length: limit - start,
          files,
          initScript,
          config,
          hotspots,
          objCount: declaredObjCount,
          objCountValid,
          confidence,
          warnings,
          parseMethod,
          sceneType,
          sceneName,
          emptyCount
      };
  }

  // Détecte le type de scène basé sur son contenu
  private inferSceneType(id: number, files: SceneFile[], hotspots: Hotspot[], isToolbar: boolean): SceneType {
      const filenames = files.map(f => f.filename.toLowerCase());
      const allFilenames = filenames.join(' ');

      // Scène 0 avec beaucoup de fichiers = variables globales
      if (id === 0 && files.length > 50) {
          return 'global_vars';
      }

      // Toolbar explicite
      if (isToolbar || filenames.some(f => f === 'toolbar')) {
          return 'toolbar';
      }

      // Options/DLL système
      if (filenames.some(f => f.includes('vnoption') || f.includes('option.dll'))) {
          return 'options';
      }

      // Crédits
      if (allFilenames.includes('credit') || allFilenames.includes('générique')) {
          return 'credits';
      }

      // Game Over / Fin
      if (allFilenames.includes('perdu') || allFilenames.includes('gagné') ||
          allFilenames.includes('fin ') || filenames.some(f => f.startsWith('fin '))) {
          return 'game_over';
      }

      // Curseur seul = probablement une meta-scène
      if (files.length === 1 && filenames[0].endsWith('.cur')) {
          return 'unknown';
      }

      // Sinon c'est une vraie scène de jeu
      return 'game';
  }
}