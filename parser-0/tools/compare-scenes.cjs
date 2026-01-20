#!/usr/bin/env node
/**
 * Compare les scènes parsées avec les destinations pour trouver le mapping
 */
const fs = require('fs');

const jsonPath = process.argv[2] || '/home/user/Europeo/couleurs1/couleurs1_parsed.json';
const data = JSON.parse(fs.readFileSync(jsonPath, 'utf-8'));

console.log('=== ANALYSE DU MAPPING DES IDs ===\n');

// Collecter toutes les destinations subtype 6 et scene X
const destinations = new Map();
const sources = new Map();

for (const scene of data.scenes) {
  const sceneId = scene.id;

  // Collecter les destinations
  for (const hs of scene.hotspots) {
    for (const cmd of hs.commands) {
      if (cmd.subtype === 6) {
        const destId = parseInt(cmd.param);
        if (!isNaN(destId)) {
          if (!destinations.has(destId)) destinations.set(destId, []);
          destinations.get(destId).push(sceneId);
        }
      }
      // Pattern "scene X"
      const matches = [...(cmd.param || '').matchAll(/\bscene\s+(\d+)/gi)];
      for (const m of matches) {
        const destId = parseInt(m[1]);
        if (!destinations.has(destId)) destinations.set(destId, []);
        destinations.get(destId).push(sceneId);
      }
    }
  }

  // Même chose pour initScript
  for (const cmd of scene.initScript?.commands || []) {
    if (cmd.subtype === 6) {
      const destId = parseInt(cmd.param);
      if (!isNaN(destId)) {
        if (!destinations.has(destId)) destinations.set(destId, []);
        destinations.get(destId).push(sceneId);
      }
    }
    const matches = [...(cmd.param || '').matchAll(/\bscene\s+(\d+)/gi)];
    for (const m of matches) {
      const destId = parseInt(m[1]);
      if (!destinations.has(destId)) destinations.set(destId, []);
      destinations.get(destId).push(sceneId);
    }
  }
}

// Trier les destinations
const sortedDests = [...destinations.keys()].sort((a, b) => a - b);
console.log('Destinations référencées (triées):', sortedDests.join(', '));
console.log('Total:', sortedDests.length);

// Comparer avec les IDs parsés
const parsedIds = data.scenes.map(s => s.id).sort((a, b) => a - b);
console.log('\nIDs parsés:', parsedIds.join(', '));
console.log('Total:', parsedIds.length);

// Trouver les intersections et différences
const destsSet = new Set(sortedDests);
const parsedSet = new Set(parsedIds);

const inBoth = sortedDests.filter(d => parsedSet.has(d));
const destsOnly = sortedDests.filter(d => !parsedSet.has(d));
const parsedOnly = parsedIds.filter(d => !destsSet.has(d));

console.log('\n=== COMPARAISON ===');
console.log('Dans les deux (destination = parsé):', inBoth.length);
console.log('Destinations SANS scène parsée:', destsOnly.join(', '));
console.log('Scènes parsées SANS destination:', parsedOnly.join(', '));

// Hypothèse: Les scènes "sans destination" sont les méta-scènes
console.log('\n=== HYPOTHÈSE: MÉTA-SCÈNES ===');
console.log('Scènes parsées jamais référencées comme destination:');
for (const id of parsedOnly) {
  const scene = data.scenes.find(s => s.id === id);
  const type = scene?.sceneType || 'unknown';
  const method = scene?.parseMethod || 'unknown';
  const firstFile = scene?.files[0]?.filename || 'N/A';
  console.log(`  ${id} [${type}] (${method}): ${firstFile}`);
}

// Si on retire les méta-scènes non-référencées, quel est le décalage?
console.log('\n=== CALCUL DU DÉCALAGE ===');
const metaSceneCount = parsedOnly.length;
console.log(`${metaSceneCount} scènes parsées ne sont jamais des destinations.`);

// Les destinations manquantes sont: 46, 51, 52, 53, 54
console.log('\nDestinations manquantes vs scènes parsées:');
for (const destId of destsOnly) {
  // Chercher quelle scène parsée pourrait correspondre
  // Si on ajoute le nombre de méta-scènes...
  const adjusted1 = destId - metaSceneCount;
  const scene1 = data.scenes.find(s => s.id === adjusted1);

  console.log(`  Destination ${destId}:`);
  if (scene1) {
    console.log(`    Si offset -${metaSceneCount}: scène ${adjusted1} = ${scene1.files[0]?.filename || 'N/A'} [${scene1.sceneType}]`);
  } else {
    console.log(`    Aucune correspondance avec offset -${metaSceneCount}`);
  }
}

// Vérifier les scènes game_over
console.log('\n=== SCÈNES GAME OVER ===');
const gameOverScenes = data.scenes.filter(s => s.sceneType === 'game_over');
for (const s of gameOverScenes) {
  console.log(`Scène ${s.id}: ${s.files[0]?.filename || s.initScript?.commands[0]?.param || 'N/A'}`);
}
console.log(`\nSi scène 54 = game over, elle correspond à scène parsée ${54 - metaSceneCount} ?`);
const candidate = data.scenes.find(s => s.id === 54 - metaSceneCount);
if (candidate) {
  console.log(`  Scène ${54 - metaSceneCount}: ${candidate.files[0]?.filename || 'N/A'} [${candidate.sceneType}]`);
}
