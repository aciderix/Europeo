
import { ParseResult, ParsedScene, SceneFile, InitScript, SceneConfig, Hotspot, HotspotCommand, InitCommand, TooltipInfo, SceneType, HotspotGeometry } from '../types';

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
    const text = this.textDecoder.decode(strBytes).replace(/\0/g, '').trim(); // Clean nulls and trim
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

      // Un nombre d'objets excessif est suspect pour un début de table, 
      // mais 0 est possible (scène sans interaction)
      if (objCount > 200) return false;
      if (objCount === 0) return (limit - ptr) < 32; 

      try {
          // On vérifie les N premiers objets pour confirmer la structure
          const itemsToCheck = Math.min(objCount, 3);

          for (let i = 0; i < itemsToCheck; i++) {
              if (ptr + 4 > limit) return false;
              let cmdCount = this.readU32(ptr);
              
              // ALIGNEMENT FIX : Si cmdCount est énorme, check +2 bytes
              if (cmdCount > 1000 && ptr + 6 <= limit) {
                  const aligned = this.readU32(ptr + 2);
                  if (aligned < 100) {
                      ptr += 2;
                      cmdCount = aligned;
                  }
              }

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
              // RELAXED CHECK : CursorID peut être n'importe quoi (label "49i" = large int)
              ptr += 4; // Cursor ID

              const pointCount = this.readU32(ptr);
              ptr += 4;
              
              if (pointCount > 200) return false;

              // STRICT CHECK: Un objet doit faire quelque chose ou exister géométriquement.
              if (cmdCount === 0 && pointCount === 0) return false;

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

  // --- SPECIFIQUE COULEURS1.VND : DETECTION DE LOGIQUE D2/D3/AVI ---
  private isCouleurs1LogicBlock(offset: number): boolean {
      // On cherche une commande ID 21 (0x15) ou ID 3 qui commence une condition spécifique
      if (offset + 60 > this.data.byteLength) return false;
      
      const id = this.readU32(offset);
      // 21 = Commande logique (if/set_var...), 3 = Autre type de commande script (ex: fin2.avi)
      if (id !== 21 && id !== 3) return false; 

      const len = this.readU32(offset + 4);
      if (len > 100) return false;

      // Lecture optimisée de la chaîne sans créer d'objets intermédiaires
      const strBytes = this.uint8Data.slice(offset + 8, offset + 8 + 40); 
      const str = this.textDecoder.decode(strBytes);

      // Détection des signatures spécifiques demandées
      if (str.includes('score <= 0 then addbmp d3')) return true;
      if (str.includes('score >= 0 then addbmp d2')) return true;
      // Ajout spécifique pour couper la scène AVI
      if (str.includes('fin2.avi')) return true;
      
      return false;
  }

  // --- PASSE 1 : CARTOGRAPHIE ---

  private findSceneOffsets(): number[] {
    const offsets: number[] = [];
    let ptr = 0;
    const len = this.data.byteLength;

    this.log("PHASE 1: Scanning pour les tables de fichiers...");

    while (ptr < len - 20) {
        // 0. HACK COULEURS1 : Détection forcée des blocs logiques d2/d3/avi comme scènes
        if (this.isCouleurs1LogicBlock(ptr)) {
            offsets.push(ptr);
            this.log(`  [HACK] Scène logique 'Couleurs1' (d2/d3/avi) détectée @ 0x${ptr.toString(16).toUpperCase()}`);
            // On avance un peu pour éviter une boucle infinie sur le même offset,
            // le parser de scène gérera la fin exacte.
            ptr += 8; 
            continue;
        }

        // 1. Vérifier si c'est un "Empty Slot" (Scène vide)
        if (this.isEmptySlotMarker(ptr)) {
            offsets.push(ptr);
            // On saute juste après la chaine "Empty" (4 bytes length + 5 bytes string = 9 bytes)
            // Mais souvent il y a du padding, on laisse le parseSceneBlock gérer la longueur exacte
            ptr += 9; 
            continue;
        }

        // 2. Vérifier si c'est une table de fichiers standard
        const tableEnd = this.isValidFileTable(ptr);

        if (tableEnd !== -1 && tableEnd > ptr) {
            offsets.push(ptr);
            this.log(`  [+] Scène détectée @ 0x${ptr.toString(16).toUpperCase()} (Table -> 0x${tableEnd.toString(16).toUpperCase()})`);
            ptr = tableEnd;
        } else {
            ptr++;
        }
    }

    return offsets;
  }

  private isEmptySlotMarker(offset: number): boolean {
      if (offset + 9 > this.data.byteLength) return false;
      // Length = 5
      if (this.readU32(offset) !== 5) return false;
      // String = "Empty"
      // E=69, m=109, p=112, t=116, y=121
      if (this.uint8Data[offset+4] === 69 && 
          this.uint8Data[offset+5] === 109 && 
          this.uint8Data[offset+6] === 112 && 
          this.uint8Data[offset+7] === 116 && 
          this.uint8Data[offset+8] === 121) {
          return true;
      }
      return false;
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
                  continue; // C'est du padding classique (8 bytes), on continue
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
          // Si on trouve ce genre de chaine, c'est qu'on est DÉJÀ dans le script
          if (this.looksLikeScriptParam(name)) {
              break;
          }

          if (name.includes(' if ') || name.includes(' = ') || name.includes(' then ') || name.startsWith('run')) {
              break;
          }

          if (name.length > 0 && name !== "empty") {
              if (name === "toolbar") foundSpecificSignature = true;
              if (/\.(bmp|wav|avi|htm|html|dll|vnp|cur|ico)$/.test(name)) hasExtensions++;
          }

          // CORRECTIF CIBLÉ "FIN PERDU"
          if (name === 'perdu.htm') {
              let foundWav = false;
              for (let scan = 0; scan < 200; scan++) {
                  const ptr = res.nextOffset + 4 + scan;
                  if (ptr + 14 > this.data.byteLength) break;
                  
                  const checkLen = this.readU32(ptr);
                  if (checkLen === 9) {
                      if (this.uint8Data[ptr+4] === 112 && this.uint8Data[ptr+12] === 118) {
                          current = ptr; 
                          foundWav = true;
                          break;
                      }
                  }
              }
              if (foundWav) continue;
          }

          current = res.nextOffset + 4; 
          validSlots++;
      }
      
      const isToolbar = foundSpecificSignature;
      const isEndSig = foundEndSignature;
      const isHeuristic = (validSlots >= 1 && hasExtensions >= 1) || (validSlots > 50);

      if (isToolbar || (isEndSig && validSlots >= 1) || isHeuristic) {
          return current; 
      }

      for (let probe = current; probe < current + 100 && probe < this.data.byteLength - 4; probe++) {
          if (this.readU32(probe) === 0xFFFFFFDB && validSlots >= 1) {
              return probe;
          }
      }

      return -1;
  }

  // Vérifie si une chaîne ressemble à un paramètre de script (et non à un nom de fichier)
  private looksLikeScriptParam(text: string): boolean {
      const clean = text.trim();
      if (/^\d+\s+\d+/.test(clean)) return true;
      if (clean.includes('#') && /[0-9a-fA-F]{6}/.test(clean)) return true;
      if (/\.(avi|bmp|wav|mp3|dll)\s+\d+/.test(clean)) return true;
      if (clean.toLowerCase().startsWith('comic sans') || clean.toLowerCase().startsWith('arial')) return true;
      if (clean === 'Quitter' || clean === 'Retour') return true;
      // ACCEPTATION DE "35k", "48i" etc. qui sont des labels de scène
      if (/^\d+[a-zA-Z]?$/.test(clean) && clean.length >= 2) return true;
      return false;
  }

  // --- INTELLIGENCE : INFÉRENCE DE TYPE ---
  private inferCommandType(text: string): { id: number, subtype: number } {
      const lower = text.toLowerCase();
      
      // PRIORITÉ ABSOLUE : Navigation (Subtype 6)
      if (lower.startsWith('scene ')) return { id: 3, subtype: 6 }; 
      if (lower.includes(' then scene ')) return { id: 3, subtype: 6 };
      if (/^\d+[a-z]$/.test(lower)) return { id: 3, subtype: 6 }; // "48i" -> Scene Nav

      if (lower.endsWith('.wav')) return { id: 1, subtype: 11 }; // Audio FX
      if (lower.endsWith('.avi')) return { id: 1, subtype: 9 };  // Video
      if (lower.includes(' = ') || lower.startsWith('if ') || lower.includes(' then ')) return { id: 3, subtype: 21 }; // Script
      if (lower.startsWith('runprj') || lower.startsWith('rundll') || lower.startsWith('scene ')) return { id: 3, subtype: 0 }; // Sys
      if (lower.endsWith('.dll')) return { id: 3, subtype: 5 };
      if (lower.startsWith('font ')) return { id: 0, subtype: 39 }; // Font config
      if (lower.includes('comic sans') || lower.includes('arial')) return { id: 0, subtype: 39 }; // Config Police explicite
      
      if (this.looksLikeScriptParam(text) && !text.includes('=')) {
          return { id: 0, subtype: 0 }; 
      }
      if (lower.includes('addbmp') || lower.includes('playbmp')) return { id: 0, subtype: 24 }; // Image
      if (lower.endsWith('.bmp')) return { id: 0, subtype: 27 }; // Overlay Image
      return { id: 9999, subtype: 0 }; // Inconnu
  }

  // --- DÉTECTION DE STRUCTURE TOOLTIP ---
  private tryParseTooltip(offset: number, limit: number): { tooltip: TooltipInfo, nextOffset: number } | null {
      if (offset + 29 > limit) return null;

      const type = this.readU32(offset);
      const x1 = this.readU32(offset + 4);
      const y1 = this.readU32(offset + 8);
      const x2 = this.readU32(offset + 12);
      const y2 = this.readU32(offset + 16);
      const flag = this.readU32(offset + 20);
      const strLen = this.readU32(offset + 24);

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

  // --- NOUVEAU SCANNER DE GÉOMÉTRIE ORPHELINE ---
  private scanForGeometryStructures(start: number, end: number, existingHotspots: Hotspot[]): { offset: number, geometry: HotspotGeometry, recoveredCmd?: string }[] {
      const found: { offset: number, geometry: HotspotGeometry, recoveredCmd?: string }[] = [];
      let ptr = start;

      // On crée une map des zones déjà occupées pour ne pas rescanner
      const occupiedZones = existingHotspots.map(h => ({ start: h.offset, end: h.offset + 200 })); // Estimation loose

      while (ptr < end - 16) { // Minimum 16 bytes
          
          // SCANNER OCTET PAR OCTET POUR TROUVER DES STRUCTURES DÉSALIGNÉES
          
          // Si on est dans une zone déjà connue, on saute
          const isInOccupied = occupiedZones.some(z => ptr >= z.start && ptr < z.end);
          if (isInOccupied) {
              ptr += 1;
              continue;
          }

          const val1 = this.readU32(ptr);
          const val2 = this.readU32(ptr + 4);
          const val3 = this.readI32(ptr + 8);

          // MODE 1 : Structure Standard [CursorID] [Count] [X]
          // Count entre 2 et 50
          
          // TOLÉRANCE CURSOR ID : Si on a plus de 2 points (Polygone), on accepte des CursorID "sales"
          const isCursorIdValid = val1 < 20000 || (val2 >= 3);

          if (isCursorIdValid && val2 >= 2 && val2 < 50 && Math.abs(val3) < 3000) {
              const pointCount = val2;
              const pointsSize = pointCount * 8;
              
              if (ptr + 8 + pointsSize <= end) {
                  const points = [];
                  let pPtr = ptr + 8;
                  let valid = true;
                  
                  for (let i = 0; i < pointCount; i++) {
                      const x = this.readI32(pPtr);
                      const y = this.readI32(pPtr + 4);
                      if (Math.abs(x) > 3000 || Math.abs(y) > 3000) { valid = false; break; }
                      points.push({ x, y });
                      pPtr += 8;
                  }

                  if (valid) {
                      let extraFlag = 0;
                      if (pPtr + 4 <= end) extraFlag = this.readU32(pPtr);
                      
                      // HEURISTIQUE BACKWARD PEEK
                      // Si le CursorID ressemble à un caractère ASCII (32-126)
                      // Et que les octets précédents sont des chiffres, on reconstitue la commande
                      let recoveredCmd: string | undefined = undefined;
                      if (val1 >= 32 && val1 <= 126) {
                          const cursorChar = String.fromCharCode(val1);
                          // Peek back 4 bytes
                          if (ptr >= 4) {
                              const prevBytes = [
                                  this.readU8(ptr-4), this.readU8(ptr-3), this.readU8(ptr-2), this.readU8(ptr-1)
                              ];
                              let numStr = "";
                              // Collect digits from end of buffer
                              for (let i = 3; i >= 0; i--) {
                                  if (prevBytes[i] >= 48 && prevBytes[i] <= 57) {
                                      numStr = String.fromCharCode(prevBytes[i]) + numStr;
                                  } else if (prevBytes[i] === 0) {
                                      // Null byte allowed
                                  } else {
                                      break; 
                                  }
                              }
                              
                              if (numStr.length > 0) {
                                  recoveredCmd = numStr + cursorChar;
                                  this.log(`  [PEEK] Commande reconstruite par rétro-analyse : "${recoveredCmd}" @ 0x${ptr.toString(16)}`);
                              }
                          }
                      }

                      found.push({
                          offset: ptr,
                          geometry: { cursorId: val1, pointCount, points, extraFlag },
                          recoveredCmd
                      });
                      ptr = pPtr + 4;
                      continue;
                  }
              }
          }

          // MODE 2 : Structure Compacte [Count] [X] [Y]
          const countCandidate = val1;
          const xCandidate = this.readI32(ptr + 4);
          const yCandidate = this.readI32(ptr + 8);

          if (countCandidate >= 2 && countCandidate < 50 && Math.abs(xCandidate) < 3000 && Math.abs(yCandidate) < 3000) {
               const pointCount = countCandidate;
               const pointsSize = pointCount * 8;

               if (ptr + 4 + pointsSize <= end) {
                   const points = [];
                   let pPtr = ptr + 4; // On saute direct aux points
                   let valid = true;

                   for (let i = 0; i < pointCount; i++) {
                      const x = this.readI32(pPtr);
                      const y = this.readI32(pPtr + 4);
                      if (Math.abs(x) > 3000 || Math.abs(y) > 3000) { valid = false; break; }
                      points.push({ x, y });
                      pPtr += 8;
                   }

                   if (valid) {
                       let extraFlag = 0;
                       if (pPtr + 4 <= end) extraFlag = this.readU32(pPtr);

                       found.push({
                          offset: ptr,
                          geometry: { cursorId: 0, pointCount, points, extraFlag }
                       });
                       ptr = pPtr + 4;
                       continue;
                   }
               }
          }

          ptr += 1; // Avance de 1 octet pour scan minutieux
      }

      return found;
  }

  // --- LOGIQUE DE RÉCUPÉRATION ROBUSTE (GAP RECOVERY) ---
  private recoverCommandsFromGap(start: number, end: number): Hotspot[] {
      const recoveredItems: Hotspot[] = [];
      let ptr = start;

      // Sauter le padding initial si ce sont des caractères imprimables
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
          'telep', 'sac', 'calc', 'bouteille', 'levure'
      ];

      while (ptr < end) {
          // Skip non-printable trash at start of block
          if (ptr < end && (this.uint8Data[ptr] < 32 && this.uint8Data[ptr] !== 0)) {
              ptr++;
              continue;
          }

          let tempPtr = ptr;
          const collectedBytes: number[] = [];
          
          // Collect string
          while (tempPtr < this.data.byteLength && collectedBytes.length < 2000) {
              const c = this.uint8Data[tempPtr];
              if (c === 0) break;
              if (c < 32 && c !== 9 && c !== 10 && c !== 13) break; 
              
              collectedBytes.push(c);
              tempPtr++;
          }

          let tempStr = "";
          if (collectedBytes.length > 2) {
             tempStr = this.textDecoder.decode(new Uint8Array(collectedBytes));
          } else if (collectedBytes.length === 2) {
             // Acceptation spéciale des chaînes de 2 chars si ce sont des chiffres (ex: "48")
             const s = this.textDecoder.decode(new Uint8Array(collectedBytes));
             if (/^\d+[a-z]?$/i.test(s)) tempStr = s;
          }

          if (tempStr.length >= 2) { 
              const lower = tempStr.toLowerCase();
              const hasKeyword = keywords.some(k => lower.includes(k));
              const looksLikeSentence = (tempStr.includes(' ') && /^[A-Z0-9\xC0-\xFF]/.test(tempStr));
              const looksLikeParam = this.looksLikeScriptParam(tempStr);

              if (hasKeyword || looksLikeSentence || looksLikeParam) {
                  let startOffset = ptr;
                  let cmdID = 9999;
                  let cmdSub = 0;

                  // Tentative de récupération ID/Sub avant la chaîne
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

                  recoveredItems.push({
                      index: -1,
                      offset: startOffset,
                      commands: [{ id: cmdID, subtype: cmdSub, param: tempStr }],
                      geometry: { cursorId: 0, pointCount: 0, points: [], extraFlag: 0 }, // Placeholder
                      isRecovered: true
                  });
                  
                  ptr = tempPtr; // Sauter la chaîne lue
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
    
    let gameSlotId = 0;

    this.log(`PHASE 2: Analyse de ${sceneOffsets.length} segments détectés.`);

    for (let i = 0; i < Math.min(sceneOffsets.length, maxScenes); i++) {
        const start = sceneOffsets[i];
        const end = (i < sceneOffsets.length - 1) ? sceneOffsets[i+1] : this.data.byteLength;
        
        try {
            const scene = this.parseSceneBlock(gameSlotId, start, end);
            
            if (scene.sceneType === 'toolbar') {
                this.log(`  [INFO] Scène 'Toolbar' détectée à 0x${start.toString(16).toUpperCase()} - Ignorée du mapping Slot.`);
                continue;
            }

            this.log(`\n--- Analyse Scène #${gameSlotId} (0x${start.toString(16).toUpperCase()} -> 0x${end.toString(16).toUpperCase()}) ---`);
            scene.id = gameSlotId;
            scenes.push(scene);
            gameSlotId++; 

        } catch (e: any) {
            this.log(`CRITICAL: Erreur fatale sur segment ${i}: ${e.message}`);
        }
    }

    return { scenes, logs: this.logs, totalBytes: this.data.byteLength };
  }

  private parseSceneBlock(id: number, start: number, limit: number): ParsedScene {
      // 0. DETECTION EMPTY SCENE
      if (this.isEmptySlotMarker(start)) {
          return {
              id,
              offset: start,
              length: 9, 
              files: [],
              initScript: { offset: start, length: 0, commands: [] },
              config: { offset: -1, flag: 0, ints: [], foundSignature: false },
              hotspots: [],
              warnings: [],
              parseMethod: 'empty_slot',
              sceneType: 'empty',
              sceneName: 'Empty Slot'
          };
      }

      const warnings: string[] = [];
      let cursor = start;
      let detectedSceneName: string | undefined;

      // 1. FILES
      const files: SceneFile[] = [];
      let slotIndex = 1;
      const fileTableLimit = Math.min(limit, start + 8192);

      let isToolbarScene = false;

      while (cursor < fileTableLimit) {
          const checkSig = this.readU32(cursor);
          if (checkSig === 0xFFFFFFDB) break;

          if (this.isValidHotspotTable(cursor, limit)) {
              this.log(`  [INFO] Fin de table fichiers détectée par structure Hotspot valide à 0x${cursor.toString(16)}`);
              break;
          }

          const len = this.readU32(cursor);
          
          if (len === 0) {
              const paramCheck = this.readU32(cursor + 4);
              if (paramCheck === 0xFFFFFFDB) break; 

              if (cursor + 8 <= limit && paramCheck === 0) {
                  cursor += 8; 
                  continue; 
              }
              
              let foundNext = false;
              for (let scan = 1; scan < 128; scan++) { 
                  const probe = cursor + scan;
                  if (probe + 4 > limit) break;
                  
                  if (this.readU32(probe) === 0xFFFFFFDB) {
                      cursor = probe; 
                      foundNext = true;
                      break;
                  }

                  const possibleLen = this.readU32(probe);
                  if (possibleLen > 0 && possibleLen < 260) { 
                      const strCheck = this.tryReadString(probe);
                      if (strCheck && strCheck.text.length > 0) {
                          if (this.looksLikeScriptParam(strCheck.text)) {
                              foundNext = false;
                              break;
                          }

                          if (/^[\w\s\-\.\\\/:]+$/.test(strCheck.text) || strCheck.text.length > 3) {
                              this.log(`  [RECOVERY] Saut de ${scan} octets de padding détecté à 0x${cursor.toString(16)} -> 0x${probe.toString(16)}`);
                              cursor = probe;
                              foundNext = true;
                              break;
                          }
                      }
                  }
              }
              if (foundNext) continue;
              break;
          }

          const res = this.tryReadString(cursor);
          if (!res) {
              if (this.isValidHotspotTable(cursor, limit)) {
                  this.log(`  [INFO] Fin de table fichiers (sur échec string) détectée par structure Hotspot valide à 0x${cursor.toString(16)}`);
                  break;
              }

              let recovered = false;
              for(let scan = 4; scan < 64; scan += 1) { 
                  const probe = cursor + scan;
                  if (probe + 4 > limit) break;
                  
                  const possibleLen = this.readU32(probe);
                  if (possibleLen > 0 && possibleLen < 260) {
                      const strCheck = this.tryReadString(probe);
                      if (strCheck && this.looksLikeScriptParam(strCheck.text)) break;
                      if (strCheck && strCheck.text.length > 3 && /^[\w\s\-\.\\\/:]+$/.test(strCheck.text)) {
                          this.log(`  [RECOVERY] Structure invalide sautée (+${scan} bytes) à 0x${cursor.toString(16)} -> 0x${probe.toString(16)} ("${strCheck.text}")`);
                          cursor = probe;
                          recovered = true;
                          break;
                      }
                  }
              }
              if (recovered) continue;
              break; 
          }

          const filename = res.text;
          if (filename.toLowerCase() === 'toolbar') isToolbarScene = true;

          if (filename.toLowerCase().includes(' if ') || filename.includes(' = ') || filename.includes(' then ')) break;
          if (this.looksLikeScriptParam(filename)) {
              this.log(`  [INFO] Fin de table détectée par paramètre script : "${filename}"`);
              break;
          }

          const paramOffset = res.nextOffset;
          if (paramOffset + 4 > limit) break;
          
          const param = this.readU32(paramOffset);
          
          const isFileExtension = /\.(bmp|wav|avi|htm|html|dll|vnp|cur|ico)$/i.test(filename);
          const isEmptySlot = filename.toLowerCase() === 'empty';
          const isSystemName = filename.toLowerCase() === 'toolbar';

          if (slotIndex === 1 && !isFileExtension && !isEmptySlot && !isSystemName && filename.length > 0) {
              detectedSceneName = filename;
              cursor = paramOffset + 4;
              continue;
          }

          files.push({ slot: slotIndex++, filename, param, offset: cursor });
          cursor = paramOffset + 4;

          if (filename.toLowerCase() === 'perdu.htm') {
              let foundWav = false;
              for (let scan = 0; scan < 200; scan++) {
                  const ptr = cursor + scan;
                  if (ptr + 14 > limit) break;
                  const checkLen = this.readU32(ptr);
                  if (checkLen === 9) {
                      if (this.uint8Data[ptr+4] === 112 && this.uint8Data[ptr+12] === 118) {
                          this.log(`  [FIX] Saut de corruption après 'perdu.htm' détecté (+${scan} bytes) -> resync sur 'perdu.wav'`);
                          cursor = ptr; 
                          foundWav = true;
                          break;
                      }
                  }
              }
              if (foundWav) continue; 
          }
          
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
          const heuristicHotspotStart = this.scanForHotspots(cursor, limit);
          
          if (heuristicHotspotStart !== -1) {
              parseMethod = isToolbarScene ? 'signature' : 'heuristic_recovered';
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

             if (id === 21 || id === 3) {
                 const strRes = this.tryReadString(scriptPtr + 4);
                 if (strRes) {
                     if (strRes.text.includes('score <= 0 then addbmp d3')) detectedSceneName = "Scène d3";
                     if (strRes.text.includes('score >= 0 then addbmp d2')) detectedSceneName = "Scène d2";
                     if (strRes.text.includes('fin2.avi')) detectedSceneName = "Scène AVI";
                 }
             }

             if (id > 50000) break; 

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
                  let cmdCount = this.readU32(hsPtr);
                  
                  // ALIGNEMENT FIX : Si cmdCount est aberrant, vérifier si un décalage de 2 octets (padding) existe
                  if (cmdCount > 1000 && hsPtr + 6 <= limit) {
                      const aligned = this.readU32(hsPtr + 2);
                      if (aligned < 100) {
                          hsPtr += 2;
                          cmdCount = aligned;
                      }
                  }

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
                  
                  // CursorID peut être alphanumérique/large (ex: "49i")
                  const cursorId = this.readU32(hsPtr); 
                  const pointCount = this.readU32(hsPtr + 4);
                  
                  if (pointCount > 500) {
                       break;
                  }

                  hsPtr += 8;
                  const points = [];
                  let hasInvalidCoords = false;

                  for(let p=0; p<pointCount; p++) {
                      if (hsPtr + 8 > limit) break;
                      const x = this.readI32(hsPtr);
                      const y = this.readI32(hsPtr+4);

                      if (Math.abs(x) > 2000 || Math.abs(y) > 2000) {
                          hasInvalidCoords = true;
                          this.log(`  [WARN] Hotspot ${i}: coordonnées invalides (${x}, ${y}) - rejeté`);
                          break;
                      }

                      points.push({ x, y });
                      hsPtr += 8;
                  }

                  if (hasInvalidCoords) break;

                  // --- STRUCTURE HYBRIDE : COMMANDES APRES GEOMETRIE ---
                  // Si on avait 0 commandes mais une géométrie valide,
                  // il est possible que les commandes soient stockées ICI (après les points).
                  if (cmdCount === 0 && points.length > 0 && hsPtr + 8 < limit) {
                       // Vérifions si on a un pattern de commande : [CmdCount u32] [ID u32]
                       let potentialCmdCount = this.readU32(hsPtr);
                       // Padding check 2 bytes
                       if (potentialCmdCount === 0 && this.readU32(hsPtr + 2) > 0 && this.readU32(hsPtr+2) < 20) {
                           hsPtr += 2;
                           potentialCmdCount = this.readU32(hsPtr);
                       }
                       
                       // Pattern de padding 4 bytes nulls fréquent
                       if (potentialCmdCount === 0 && this.readU32(hsPtr + 4) > 0 && this.readU32(hsPtr+4) < 20) {
                           hsPtr += 4;
                           potentialCmdCount = this.readU32(hsPtr);
                       }

                       if (potentialCmdCount > 0 && potentialCmdCount < 20) {
                           const nextID = this.readU32(hsPtr + 4);
                           // Si l'ID suivant est plausible (ex: 0=Graphique, 21=Logic, 27=Font...)
                           if (nextID < 50 || nextID === 9999) {
                               hsPtr += 4; // Skip CmdCount
                               for (let c = 0; c < potentialCmdCount; c++) {
                                  if (hsPtr >= limit) break;
                                  const id = this.readU32(hsPtr);
                                  const subtype = this.readU32(hsPtr + 4);
                                  const res = this.tryReadString(hsPtr + 8);
                                  if (res) {
                                      commands.push({ id, subtype, param: res.text });
                                      hsPtr = res.nextOffset;
                                  } else {
                                      break;
                                  }
                               }
                           }
                       }
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

      const tooltipScanStart = hsPtr !== -1 ? Math.min(hsPtr, cursor) : cursor;
      const detectedTooltips = this.scanForTooltips(tooltipScanStart, limit);
      if (detectedTooltips.length > 0) {
          this.log(`  [INFO] ${detectedTooltips.length} tooltip(s) trouvé(s)`);
      }
      recoveredHotspots.push(...detectedTooltips);

      // Récupération des commandes "orphelines"
      if (cursor < scriptEnd) {
          recoveredHotspots.push(...this.recoverCommandsFromGap(cursor, scriptEnd));
      }

      let finalGapPtr = hsPtr !== -1 ? hsPtr : cursor;
      if (finalGapPtr < limit - 16) {
          recoveredHotspots.push(...this.recoverCommandsFromGap(finalGapPtr, limit));
      }

      // 7. NEW : DEEP GEOMETRY SCAN & MERGE INTELLIGENT (COALESCENCE)
      
      // A. Deep Geometry Scan
      const potentialGeometries = this.scanForGeometryStructures(finalGapPtr, limit, hotspots);
      if (potentialGeometries.length > 0) {
          this.log(`  [DEEP SCAN] ${potentialGeometries.length} structures géométriques orphelines trouvées.`);
      }

      // B. Sort Recovered Items (Commands) by Offset
      recoveredHotspots.sort((a, b) => a.offset - b.offset);

      const mergedHotspots = [...hotspots];
      
      // C. Coalesce Commands (Regrouper Font + Text + Logic proches)
      const coalescedHotspots: Hotspot[] = [];
      let currentGroup: Hotspot | null = null;

      for (const item of recoveredHotspots) {
          // Si c'est un tooltip ou une géométrie pure (si jamais il y en a), on ne groupe pas
          if (item.isTooltip || (item.geometry.pointCount > 0)) {
              coalescedHotspots.push(item);
              currentGroup = null;
              continue;
          }

          // RUPTURE DE FUSION : Si le nouvel élément est un marqueur de début (Config Police), on casse le groupe
          // (ex: On a fini 'Question Bonus', et on trouve 'Config Police' pour 'La Momie')
          const isStructuralStart = item.commands.some(c => c.subtype === 39 || c.param.toLowerCase().includes('comic sans') || c.param.toLowerCase().includes('arial'));

          if (currentGroup && isStructuralStart) {
              currentGroup = null; // Force start new group
          }

          // Si on a un groupe actif et que l'item est proche
          if (currentGroup && (item.offset - currentGroup.offset < 1000)) { 
              currentGroup.commands.push(...item.commands);
              // On garde le "parent" comme référence
          } else {
              // Nouveau groupe
              currentGroup = item;
              coalescedHotspots.push(item);
          }
      }

      // D. Associer Géométries aux Groupes Coalescés
      // On tente de marier les groupes de commandes avec les géométries trouvées juste après
      
      // On ajoute d'abord toutes les géométries comme orphelines
      const geometryPool = [...potentialGeometries];

      coalescedHotspots.forEach(cmdHotspot => {
          if (cmdHotspot.isTooltip) {
              mergedHotspots.push(cmdHotspot);
              return;
          }

          if (cmdHotspot.geometry.pointCount > 0) {
              mergedHotspots.push(cmdHotspot);
              return;
          }

          // Chercher une géométrie orpheline située APRES ce groupe de commandes, mais pas trop loin
          // On cherche la PREMIÈRE géométrie qui suit l'offset de la commande
          const geoIndex = geometryPool.findIndex(g => 
              g.offset > cmdHotspot.offset && 
              (g.offset - cmdHotspot.offset) < 2000 // Fenêtre très large car script peut être long
          );

          if (geoIndex !== -1) {
              // FUSION !
              const geo = geometryPool[geoIndex];
              cmdHotspot.geometry = geo.geometry;
              this.log(`  [MERGE] Commande Groupée @0x${cmdHotspot.offset.toString(16)} associée à Géométrie @0x${geo.offset.toString(16)}`);
              
              // On retire cette géométrie du pool pour ne pas la réutiliser
              geometryPool.splice(geoIndex, 1);
              mergedHotspots.push(cmdHotspot);
          } else {
              // Pas de géométrie trouvée
              // Classification finale : Logique pure ou Hotspot cassé ?
              
              // Si contient subtype 6, c'est une navigation, on garde en hotspot même sans géométrie
              const hasNav = cmdHotspot.commands.some(c => c.subtype === 6 || c.param.toLowerCase().includes('scene '));
              
              if (hasNav) {
                  mergedHotspots.push(cmdHotspot);
              } else {
                  // Sinon, on considère que c'est du script d'init
                  const isLogic = cmdHotspot.commands.every(c => {
                       if (c.id === 3) return true;
                       const text = c.param.toLowerCase();
                       if (text.includes(' = ') || text.includes(' if ') || text.startsWith('run') || text.startsWith('set_') || text.startsWith('inc_')) return true;
                       return false; 
                  });

                  if (isLogic) {
                      cmdHotspot.commands.forEach(cmd => {
                          initScript.commands.push({
                              id: cmd.id,
                              subtype: cmd.subtype,
                              param: cmd.param,
                              offset: cmdHotspot.offset,
                              isRecovered: true
                          });
                      });
                  } else {
                      // Cas par défaut : on garde comme hotspot incomplet
                      mergedHotspots.push(cmdHotspot);
                  }
              }
          }
      });

      // Ajouter les géométries restantes (zones mortes ?)
      // Si une géométrie a une commande "recoveredCmd" attachée par le scanner, on l'utilise !
      geometryPool.forEach(geo => {
          const recoveredCommands: HotspotCommand[] = [];
          if (geo.recoveredCmd) {
              const inferred = this.inferCommandType(geo.recoveredCmd);
              recoveredCommands.push({
                  id: inferred.id,
                  subtype: inferred.subtype,
                  param: geo.recoveredCmd
              });
          }

          mergedHotspots.push({
              index: -1,
              offset: geo.offset,
              commands: recoveredCommands,
              geometry: geo.geometry,
              isRecovered: true
          });
      });

      if (files.length > 0 && files[0].filename.toLowerCase().includes('fin2.avi')) {
          detectedSceneName = "Scène AVI";
      }
      if (files.length > 0 && files[0].filename.toLowerCase().includes('fin perdu')) {
          detectedSceneName = "Fin Perdu";
      }

      const sceneType = this.inferSceneType(id, files, mergedHotspots, isToolbarScene);

      return {
          id,
          offset: start,
          length: limit - start,
          files,
          initScript,
          config,
          hotspots: mergedHotspots,
          warnings,
          parseMethod,
          sceneType,
          sceneName: detectedSceneName
      };
  }

  // Détecte le type de scène basé sur son contenu
  private inferSceneType(id: number, files: SceneFile[], hotspots: Hotspot[], isToolbar: boolean): SceneType {
      const filenames = files.map(f => f.filename.toLowerCase());
      const allFilenames = filenames.join(' ');

      if (id === 0 && files.length > 50) return 'global_vars';
      if (isToolbar || filenames.some(f => f === 'toolbar')) return 'toolbar';
      if (filenames.some(f => f.includes('vnoption') || f.includes('option.dll'))) return 'options';
      if (allFilenames.includes('credit') || allFilenames.includes('générique')) return 'credits';
      if (allFilenames.includes('perdu') || allFilenames.includes('gagné') || allFilenames.includes('fin ') || filenames.some(f => f.startsWith('fin '))) return 'game_over';
      if (files.length === 1 && filenames[0].endsWith('.cur')) return 'unknown';

      return 'game';
  }
}
