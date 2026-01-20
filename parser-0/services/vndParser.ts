import { ParseResult, ParsedScene, SceneFile, InitScript, SceneConfig, Hotspot, HotspotCommand, InitCommand } from '../types';

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

  private findSceneOffsets(): number[] {
    const offsets: number[] = [];
    let ptr = 0;
    const len = this.data.byteLength;

    this.log("PHASE 1: Scanning pour les signatures de scènes...");
    
    while (ptr < len - 100) {
        // isValidFileTable retourne maintenant l'offset de FIN de la table si valide, sinon -1
        const tableEnd = this.isValidFileTable(ptr);
        
        if (tableEnd !== -1 && tableEnd > ptr) {
            offsets.push(ptr);
            this.log(`  [+] Scène candidate détectée @ 0x${ptr.toString(16).toUpperCase()} (Fin Table @ 0x${tableEnd.toString(16).toUpperCase()})`);
            
            // CRUCIAL : On saute directement à la fin de la table détectée.
            // On s'assure que ptr avance pour éviter les boucles infinies.
            ptr = tableEnd; 
        } else {
            ptr++;
        }
    }
    return offsets;
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
      
      // Validation stricte : 
      const isToolbar = foundSpecificSignature;
      const isEndSig = foundEndSignature;
      // Heuristique assouplie : Si on a beaucoup de slots (variables globales), c'est valide
      const isHeuristic = (validSlots >= 2 && hasExtensions >= 1) || (validSlots > 50);

      if (isToolbar || (isEndSig && validSlots >= 1) || isHeuristic) {
          return current; // Retourne la position APRES la table
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
                              geometry.cursorId = potentialCursor;
                              geometry.pointCount = potentialPoints;
                              let ptReadPtr = geomPtr + 8;
                              for(let p=0; p<potentialPoints; p++) {
                                  geometry.points.push({ 
                                      x: this.readI32(ptReadPtr), 
                                      y: this.readI32(ptReadPtr+4) 
                                  });
                                  ptReadPtr += 8;
                              }
                              if (ptReadPtr + 4 <= end) {
                                  geometry.extraFlag = this.readU32(ptReadPtr);
                                  ptReadPtr += 4;
                              }
                              tempPtr = ptReadPtr; 
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
      
      if (hsPtr !== -1 && hsPtr < limit) {
          const objCount = this.readU32(hsPtr);
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
                  for(let p=0; p<pointCount; p++) {
                      if (hsPtr + 8 > limit) break;
                      points.push({ x: this.readI32(hsPtr), y: this.readI32(hsPtr+4) });
                      hsPtr += 8;
                  }
                  
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
      
      // Zone 1: Le reste du bloc de script
      if (cursor < scriptEnd) {
          recoveredHotspots.push(...this.recoverCommandsFromGap(cursor, scriptEnd));
      }

      // Zone 2: Le "No Man's Land" final (inclut ce qui a été abandonné par la boucle hotspots)
      let finalGapPtr = hsPtr !== -1 ? hsPtr : cursor;
      if (finalGapPtr < limit - 16) {
          recoveredHotspots.push(...this.recoverCommandsFromGap(finalGapPtr, limit));
      }

      if (recoveredHotspots.length > 0) {
          let logicCount = 0;
          let orphanCount = 0;

          recoveredHotspots.forEach(hs => {
              const cmd = hs.commands[0];
              // Classification
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
                  // Traité comme un hotspot normal
                  hotspots.push(hs);
                  orphanCount++;
              }
          });

          if (logicCount > 0) warnings.push(`${logicCount} commandes logiques récupérées.`);
          if (orphanCount > 0) warnings.push(`${orphanCount} éléments interactifs récupérés.`);
      }

      return {
          id,
          offset: start,
          length: limit - start,
          files,
          initScript,
          config,
          hotspots,
          warnings,
          parseMethod
      };
  }
}