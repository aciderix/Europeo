#!/usr/bin/env node
/**
 * Liste complète des destinations de scènes dans un fichier parsé
 */
const fs = require('fs');

const jsonPath = process.argv[2] || '/home/user/Europeo/couleurs1/couleurs1_parsed.json';
const data = JSON.parse(fs.readFileSync(jsonPath, 'utf-8'));

console.log('='.repeat(80));
console.log('LISTE COMPLÈTE DES DESTINATIONS - ' + jsonPath.split('/').pop());
console.log('='.repeat(80));

// Collecter toutes les destinations
const allDestinations = [];

for (const scene of data.scenes) {
  const sceneType = scene.sceneType || 'unknown';

  // Extraire des hotspots
  for (const hs of scene.hotspots) {
    for (const cmd of hs.commands) {
      const param = cmd.param || '';

      // Pattern: scene X
      const sceneMatches = [...param.matchAll(/\bscene\s+(\d+)/gi)];
      for (const m of sceneMatches) {
        allDestinations.push({
          from: scene.id,
          fromType: sceneType,
          to: parseInt(m[1]),
          type: 'scene',
          context: param.substring(0, 60),
          source: 'hotspot'
        });
      }

      // Pattern: runprj ...vnp X
      const runprjMatches = [...param.matchAll(/runprj\s+([^\s]+)\s+(\d+)/gi)];
      for (const m of runprjMatches) {
        const target = m[1];
        const sceneNum = parseInt(m[2]);
        const isInternal = target.toLowerCase().includes('couleurs1');

        allDestinations.push({
          from: scene.id,
          fromType: sceneType,
          to: sceneNum,
          type: isInternal ? 'runprj_internal' : 'runprj_external',
          target: target,
          context: param.substring(0, 60),
          source: 'hotspot'
        });
      }
    }
  }

  // Extraire du initScript
  for (const cmd of scene.initScript?.commands || []) {
    const param = cmd.param || '';

    const sceneMatches = [...param.matchAll(/\bscene\s+(\d+)/gi)];
    for (const m of sceneMatches) {
      allDestinations.push({
        from: scene.id,
        fromType: sceneType,
        to: parseInt(m[1]),
        type: 'scene',
        context: param.substring(0, 60),
        source: 'initScript'
      });
    }

    const runprjMatches = [...param.matchAll(/runprj\s+([^\s]+)\s+(\d+)/gi)];
    for (const m of runprjMatches) {
      const target = m[1];
      const sceneNum = parseInt(m[2]);
      const isInternal = target.toLowerCase().includes('couleurs1');

      allDestinations.push({
        from: scene.id,
        fromType: sceneType,
        to: sceneNum,
        type: isInternal ? 'runprj_internal' : 'runprj_external',
        target: target,
        context: param.substring(0, 60),
        source: 'initScript'
      });
    }
  }
}

// Trier par scène source
allDestinations.sort((a, b) => a.from - b.from || a.to - b.to);

// Afficher par scène source
console.log('\n--- DESTINATIONS PAR SCÈNE SOURCE ---\n');

let currentFrom = -1;
for (const dest of allDestinations) {
  if (dest.from !== currentFrom) {
    currentFrom = dest.from;
    console.log(`\nScène ${dest.from} [${dest.fromType}]:`);
  }

  const arrow = dest.type === 'scene' ? '→' :
                dest.type === 'runprj_internal' ? '⟶' : '⟹';
  const targetInfo = dest.target ? ` (${dest.target})` : '';

  console.log(`  ${arrow} ${dest.to}${targetInfo}`);
  console.log(`      "${dest.context}..."`);
}

// Statistiques
console.log('\n' + '='.repeat(80));
console.log('STATISTIQUES');
console.log('='.repeat(80));

// Destinations internes uniques
const internalDests = new Set(
  allDestinations
    .filter(d => d.type === 'scene' || d.type === 'runprj_internal')
    .map(d => d.to)
);
const sortedInternal = [...internalDests].sort((a, b) => a - b);

console.log(`\nDestinations internes (couleurs1) uniques: ${sortedInternal.length}`);
console.log(`  ${sortedInternal.join(', ')}`);

// Vérifier lesquelles existent
const existingIds = new Set(data.scenes.map(s => s.id));
const missingDests = sortedInternal.filter(d => !existingIds.has(d));
const existingDests = sortedInternal.filter(d => existingIds.has(d));

console.log(`\nDestinations EXISTANTES: ${existingDests.length}`);
console.log(`  ${existingDests.join(', ')}`);

console.log(`\nDestinations MANQUANTES: ${missingDests.length}`);
if (missingDests.length > 0) {
  console.log(`  ${missingDests.join(', ')}`);
}

// Destinations externes
const externalDests = allDestinations.filter(d => d.type === 'runprj_external');
const byTarget = {};
for (const d of externalDests) {
  const key = d.target.toLowerCase();
  if (!byTarget[key]) byTarget[key] = new Set();
  byTarget[key].add(d.to);
}

console.log(`\nDestinations externes (autres VNP):`);
for (const [target, scenes] of Object.entries(byTarget)) {
  console.log(`  ${target}: ${[...scenes].sort((a,b)=>a-b).join(', ')}`);
}

// Résumé final
console.log('\n' + '='.repeat(80));
console.log('RÉSUMÉ');
console.log('='.repeat(80));
console.log(`Total destinations trouvées: ${allDestinations.length}`);
console.log(`Destinations internes uniques: ${sortedInternal.length}`);
console.log(`  - Existantes: ${existingDests.length}`);
console.log(`  - Manquantes: ${missingDests.length}`);
console.log(`Fichiers externes référencés: ${Object.keys(byTarget).length}`);
