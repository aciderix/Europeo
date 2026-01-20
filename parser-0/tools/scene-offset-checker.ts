#!/usr/bin/env npx tsx
/**
 * Script de diagnostic pour détecter les décalages de numérotation de scènes
 * Analyse les commandes de navigation et vérifie la cohérence
 */

import * as fs from 'fs';
import * as path from 'path';

interface SceneNav {
  fromScene: number;
  toScene: number;
  command: string;
  offset: string;
}

interface SceneInfo {
  id: number;
  offset: number;
  offsetHex: string;
  filesCount: number;
  hotspotsCount: number;
  firstFile: string;
  isToolbar: boolean;
  isGlobalVars: boolean;
  navigatesTo: number[];
  navigatedFrom: number[];
}

function main() {
  const args = process.argv.slice(2);

  if (args.length < 1) {
    console.log('Usage: npx tsx tools/scene-offset-checker.ts <fichier_parsed.json>');
    console.log('Exemple: npx tsx tools/scene-offset-checker.ts ../couleurs1/couleurs1_parsed.json');
    process.exit(1);
  }

  const jsonPath = path.resolve(args[0]);
  if (!fs.existsSync(jsonPath)) {
    console.error(`Fichier non trouvé: ${jsonPath}`);
    process.exit(1);
  }

  const data = JSON.parse(fs.readFileSync(jsonPath, 'utf-8'));
  const scenes = data.scenes;

  console.log(`\n${'='.repeat(70)}`);
  console.log('ANALYSEUR DE DÉCALAGE DE SCÈNES');
  console.log(`${'='.repeat(70)}`);
  console.log(`Fichier: ${jsonPath}`);
  console.log(`Nombre de scènes: ${scenes.length}\n`);

  // 1. Collecter les infos de chaque scène
  const sceneInfos: SceneInfo[] = [];
  const navigations: SceneNav[] = [];

  for (const scene of scenes) {
    const firstFile = scene.files[0]?.filename || '';
    const isToolbar = firstFile.toLowerCase() === 'toolbar' ||
                      scene.files.some((f: any) => f.filename.toLowerCase() === 'toolbar');
    const isGlobalVars = scene.files.length > 50; // Scène 0 avec variables globales

    const info: SceneInfo = {
      id: scene.id,
      offset: scene.offset,
      offsetHex: `0x${scene.offset.toString(16).toUpperCase()}`,
      filesCount: scene.files.length,
      hotspotsCount: scene.hotspots.length,
      firstFile: firstFile.substring(0, 40),
      isToolbar,
      isGlobalVars,
      navigatesTo: [],
      navigatedFrom: []
    };

    // Extraire les navigations depuis les hotspots
    for (const hs of scene.hotspots) {
      for (const cmd of hs.commands) {
        const param = cmd.param || '';

        // Pattern: "scene X" ou "scene X then..."
        const sceneMatch = param.match(/\bscene\s+(\d+)/i);
        if (sceneMatch) {
          const targetScene = parseInt(sceneMatch[1]);
          info.navigatesTo.push(targetScene);
          navigations.push({
            fromScene: scene.id,
            toScene: targetScene,
            command: param.substring(0, 60),
            offset: `0x${hs.offset.toString(16)}`
          });
        }

        // Pattern: "runprj ...\\xxx.vnp Y"
        const runprjMatch = param.match(/runprj\s+[^\s]+\.vnp\s+(\d+)/i);
        if (runprjMatch) {
          const targetScene = parseInt(runprjMatch[1]);
          info.navigatesTo.push(targetScene);
          navigations.push({
            fromScene: scene.id,
            toScene: targetScene,
            command: param.substring(0, 60),
            offset: `0x${hs.offset.toString(16)}`
          });
        }
      }
    }

    // Aussi dans initScript
    for (const cmd of scene.initScript?.commands || []) {
      const param = cmd.param || '';
      const sceneMatch = param.match(/\bscene\s+(\d+)/i);
      if (sceneMatch) {
        const targetScene = parseInt(sceneMatch[1]);
        info.navigatesTo.push(targetScene);
      }
    }

    sceneInfos.push(info);
  }

  // Construire les relations inverses
  for (const nav of navigations) {
    const targetInfo = sceneInfos.find(s => s.id === nav.toScene);
    if (targetInfo) {
      targetInfo.navigatedFrom.push(nav.fromScene);
    }
  }

  // 2. Identifier les scènes suspectes (toolbar, etc.)
  console.log('--- SCÈNES SUSPECTES (non-jeu) ---\n');
  const suspectScenes: number[] = [];

  for (const info of sceneInfos) {
    if (info.isToolbar) {
      console.log(`[!] Scène ${info.id} @ ${info.offsetHex}: TOOLBAR détecté`);
      suspectScenes.push(info.id);
    }
    if (info.isGlobalVars) {
      console.log(`[!] Scène ${info.id} @ ${info.offsetHex}: Variables globales (${info.filesCount} fichiers)`);
      suspectScenes.push(info.id);
    }
    if (info.filesCount === 0 && info.hotspotsCount === 0) {
      console.log(`[?] Scène ${info.id} @ ${info.offsetHex}: Scène vide`);
      suspectScenes.push(info.id);
    }
  }

  // 3. Vérifier les destinations qui n'existent pas
  console.log('\n--- DESTINATIONS INVALIDES ---\n');
  const maxSceneId = Math.max(...sceneInfos.map(s => s.id));
  let invalidDestCount = 0;

  for (const nav of navigations) {
    if (nav.toScene > maxSceneId) {
      console.log(`[ERR] Scène ${nav.fromScene} → Scène ${nav.toScene} (N'EXISTE PAS!)`);
      console.log(`      Commande: ${nav.command}`);
      invalidDestCount++;
    }
  }

  if (invalidDestCount === 0) {
    console.log('Aucune destination invalide trouvée.');
  }

  // 4. Vérifier les allers-retours
  console.log('\n--- VÉRIFICATION ALLERS-RETOURS ---\n');
  let missingReturnCount = 0;

  for (const info of sceneInfos) {
    if (info.isToolbar || info.isGlobalVars) continue;

    for (const destId of [...new Set(info.navigatesTo)]) {
      const destInfo = sceneInfos.find(s => s.id === destId);
      if (destInfo && !destInfo.isToolbar && !destInfo.isGlobalVars) {
        // Est-ce que la destination a un retour vers nous?
        const hasReturn = destInfo.navigatesTo.includes(info.id);
        if (!hasReturn && destInfo.navigatesTo.length > 0) {
          // La destination va ailleurs, pas de retour
          // C'est normal pour certaines scènes (menus, etc.)
        }
      }
    }
  }

  // 5. Table de correspondance avec décalage potentiel
  console.log('\n--- TABLE DES SCÈNES (ID Parser vs Position réelle estimée) ---\n');
  console.log('ID Parser | Offset     | Fichiers | Hotspots | Premier fichier');
  console.log('-'.repeat(70));

  let realSceneIndex = 0;
  for (const info of sceneInfos) {
    let marker = '  ';
    if (info.isToolbar) marker = 'TB';
    else if (info.isGlobalVars) marker = 'GV';

    // Si c'est une vraie scène (pas toolbar/globalvars), incrémenter
    const realId = info.isToolbar || info.isGlobalVars ? '-' : realSceneIndex.toString();
    if (!info.isToolbar && !info.isGlobalVars) realSceneIndex++;

    const diff = info.id !== parseInt(realId) && realId !== '-' ? ` [DÉCALAGE: ${info.id - parseInt(realId)}]` : '';

    console.log(`${marker} ${info.id.toString().padStart(3)} (=${realId.padStart(3)}) | ${info.offsetHex.padStart(10)} | ${info.filesCount.toString().padStart(8)} | ${info.hotspotsCount.toString().padStart(8)} | ${info.firstFile}${diff}`);
  }

  // 6. Analyser les navigations pour détecter le décalage
  console.log('\n--- ANALYSE DES NAVIGATIONS (cherche incohérences) ---\n');

  // Grouper les destinations par scène source
  const destBySource: Map<number, number[]> = new Map();
  for (const nav of navigations) {
    if (!destBySource.has(nav.fromScene)) {
      destBySource.set(nav.fromScene, []);
    }
    destBySource.get(nav.fromScene)!.push(nav.toScene);
  }

  // Chercher des patterns: si scène X va vers Y, et Y va vers X+décalage, c'est suspect
  console.log('Navigations principales:');
  for (const [fromId, toIds] of destBySource) {
    const uniqueDests = [...new Set(toIds)].sort((a,b) => a-b);
    if (uniqueDests.length > 0) {
      const fromInfo = sceneInfos.find(s => s.id === fromId);
      if (fromInfo && !fromInfo.isToolbar && !fromInfo.isGlobalVars) {
        console.log(`  Scène ${fromId} → [${uniqueDests.join(', ')}]`);
      }
    }
  }

  // 7. NOUVELLE ANALYSE: Relations bidirectionnelles pour détecter le décalage
  console.log('\n--- ANALYSE BIDIRECTIONNELLE (détection décalage) ---\n');

  interface BiDirectionalCheck {
    parentScene: number;
    childScene: number;
    direction: 'up' | 'down'; // up = vers scène supérieure, down = vers inférieure
    hasReturn: boolean;
    returnTargets: number[];
    expectedReturn: number;
    actualReturn: number | null;
    offset: number | null;
  }

  const biChecks: BiDirectionalCheck[] = [];

  for (const info of sceneInfos) {
    if (info.isToolbar || info.isGlobalVars) continue;

    const uniqueDests = [...new Set(info.navigatesTo)];

    for (const destId of uniqueDests) {
      const destInfo = sceneInfos.find(s => s.id === destId);
      if (!destInfo || destInfo.isToolbar || destInfo.isGlobalVars) continue;

      const destUniqueDests = [...new Set(destInfo.navigatesTo)];
      const direction: 'up' | 'down' = destId > info.id ? 'up' : 'down';

      // Chercher si la destination a un lien de retour vers nous
      const hasReturn = destUniqueDests.includes(info.id);

      // Chercher les destinations de la scène enfant qui pointent vers des scènes
      // dans la même direction relative (retour vers parent ou plus loin vers enfant)
      let returnTargets: number[] = [];
      if (direction === 'up') {
        // On est allé vers une scène supérieure, chercher ses liens vers scènes inférieures
        returnTargets = destUniqueDests.filter(d => d < destId);
      } else {
        // On est allé vers une scène inférieure, chercher ses liens vers scènes supérieures
        returnTargets = destUniqueDests.filter(d => d > destId);
      }

      // Calculer l'écart si on trouve un retour
      let actualReturn: number | null = null;
      let offset: number | null = null;

      if (returnTargets.length > 0) {
        // Trouver le retour le plus proche de notre ID
        const closest = returnTargets.reduce((prev, curr) =>
          Math.abs(curr - info.id) < Math.abs(prev - info.id) ? curr : prev
        );
        actualReturn = closest;
        offset = closest - info.id;
      }

      biChecks.push({
        parentScene: info.id,
        childScene: destId,
        direction,
        hasReturn,
        returnTargets,
        expectedReturn: info.id,
        actualReturn,
        offset
      });
    }
  }

  // Afficher les cas avec décalage
  console.log('Liens avec DÉCALAGE détecté (retour ≠ origine):');
  console.log('-'.repeat(70));

  const offsetCases = biChecks.filter(c => c.offset !== null && c.offset !== 0);

  if (offsetCases.length === 0) {
    console.log('Aucun décalage détecté dans les liens bidirectionnels.');
  } else {
    // Grouper par valeur d'offset pour voir le pattern
    const offsetGroups: Map<number, BiDirectionalCheck[]> = new Map();
    for (const check of offsetCases) {
      const key = check.offset!;
      if (!offsetGroups.has(key)) offsetGroups.set(key, []);
      offsetGroups.get(key)!.push(check);
    }

    for (const [offsetVal, checks] of [...offsetGroups.entries()].sort((a, b) => a[0] - b[0])) {
      console.log(`\n  OFFSET = ${offsetVal > 0 ? '+' : ''}${offsetVal}:`);
      for (const c of checks.slice(0, 10)) { // Limiter à 10 exemples par offset
        const arrow = c.direction === 'up' ? '↗' : '↘';
        console.log(`    ${c.parentScene} ${arrow} ${c.childScene} : retour vers ${c.actualReturn} (attendu: ${c.expectedReturn})`);
      }
      if (checks.length > 10) {
        console.log(`    ... et ${checks.length - 10} autres cas`);
      }
    }
  }

  // Chercher où commence le décalage
  console.log('\n--- POINT DE DÉPART DU DÉCALAGE ---\n');

  // Trier par scène parent pour trouver la première occurrence
  const sortedOffsetCases = offsetCases.sort((a, b) => a.parentScene - b.parentScene);

  if (sortedOffsetCases.length > 0) {
    const firstOffset = sortedOffsetCases[0];
    console.log(`Premier décalage détecté:`);
    console.log(`  Scène ${firstOffset.parentScene} → Scène ${firstOffset.childScene}`);
    console.log(`  Direction: ${firstOffset.direction === 'up' ? 'vers scène supérieure' : 'vers scène inférieure'}`);
    console.log(`  Retour attendu: ${firstOffset.expectedReturn}`);
    console.log(`  Retour réel: ${firstOffset.actualReturn}`);
    console.log(`  Décalage: ${firstOffset.offset! > 0 ? '+' : ''}${firstOffset.offset}`);

    // Analyser les scènes autour
    console.log(`\nScènes autour du point de décalage:`);
    const nearbyIds = [firstOffset.parentScene - 2, firstOffset.parentScene - 1,
                       firstOffset.parentScene, firstOffset.parentScene + 1, firstOffset.parentScene + 2]
                       .filter(id => id >= 0 && id <= maxSceneId);

    for (const id of nearbyIds) {
      const info = sceneInfos.find(s => s.id === id);
      if (info) {
        const marker = id === firstOffset.parentScene ? '>>>' : '   ';
        const type = info.isToolbar ? '[TOOLBAR]' : info.isGlobalVars ? '[GLOBAL]' : '';
        console.log(`${marker} Scène ${id}: ${info.firstFile} ${type}`);
        if (info.navigatesTo.length > 0) {
          console.log(`       → ${[...new Set(info.navigatesTo)].sort((a,b)=>a-b).join(', ')}`);
        }
      }
    }
  } else {
    console.log('Aucun point de décalage identifié dans les liens bidirectionnels.');
  }

  // Afficher les liens cohérents (sans décalage) pour comparaison
  console.log('\n--- LIENS COHÉRENTS (retour = origine, offset = 0) ---\n');
  const coherentCases = biChecks.filter(c => c.hasReturn || (c.offset !== null && c.offset === 0));
  console.log(`${coherentCases.length} liens bidirectionnels cohérents trouvés.`);

  if (coherentCases.length > 0 && coherentCases.length <= 20) {
    for (const c of coherentCases) {
      const arrow = c.direction === 'up' ? '↗' : '↘';
      console.log(`  ${c.parentScene} ${arrow} ${c.childScene} : retour OK`);
    }
  } else if (coherentCases.length > 20) {
    console.log('  (trop nombreux pour afficher, premières scènes:');
    for (const c of coherentCases.slice(0, 10)) {
      const arrow = c.direction === 'up' ? '↗' : '↘';
      console.log(`  ${c.parentScene} ${arrow} ${c.childScene} : retour OK`);
    }
    console.log('  ...');
  }

  // 8. Résumé
  console.log(`\n${'='.repeat(70)}`);
  console.log('RÉSUMÉ');
  console.log(`${'='.repeat(70)}`);
  console.log(`Total scènes parsées: ${scenes.length}`);
  console.log(`Scènes suspectes (toolbar/vars): ${suspectScenes.length}`);
  console.log(`Vraies scènes de jeu: ${scenes.length - suspectScenes.length}`);
  console.log(`Destinations invalides: ${invalidDestCount}`);
  console.log(`Liens bidirectionnels analysés: ${biChecks.length}`);
  console.log(`Liens avec décalage: ${offsetCases.length}`);
  console.log(`Liens cohérents: ${coherentCases.length}`);
  console.log(`\nSi le jeu référence "scene 39" mais vous voyez la scène ${39 - suspectScenes.length},`);
  console.log(`le décalage probable est de ${suspectScenes.length} (nombre de scènes non-jeu).`);
}

main();
