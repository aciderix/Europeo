#!/usr/bin/env node
/**
 * Créer un mapping basé uniquement sur les scènes avec signature
 * pour voir si ça correspond aux destinations du jeu
 */
const fs = require('fs');

const jsonPath = process.argv[2] || '/home/user/Europeo/couleurs1/couleurs1_parsed.json';
const data = JSON.parse(fs.readFileSync(jsonPath, 'utf-8'));

// Scènes avec signature uniquement (exclure heuristic et heuristic_recovered)
const sigScenes = data.scenes.filter(s => s.parseMethod === 'signature');
console.log('=== SCÈNES AVEC SIGNATURE UNIQUEMENT ===');
console.log(`Total: ${sigScenes.length}\n`);

// Créer un mapping: index séquentiel (1-based) → scène parsée
console.log('Index (1-based) | ID Parsé | Fichier | Type');
console.log('-'.repeat(70));

for (let i = 0; i < sigScenes.length; i++) {
  const s = sigScenes[i];
  const gameId = i + 1; // Le jeu utilise probablement 1-based
  const firstFile = (s.files[0]?.filename || 'N/A').substring(0, 30);
  console.log(`${gameId.toString().padStart(14)} | ${s.id.toString().padStart(8)} | ${firstFile.padEnd(30)} | ${s.sceneType}`);
}

// Collecter les destinations
const allDests = new Set();
for (const scene of data.scenes) {
  for (const hs of scene.hotspots) {
    for (const cmd of hs.commands) {
      if (cmd.subtype === 6) {
        const d = parseInt(cmd.param);
        if (!isNaN(d)) allDests.add(d);
      }
      const matches = [...(cmd.param || '').matchAll(/\bscene\s+(\d+)/gi)];
      for (const m of matches) allDests.add(parseInt(m[1]));
    }
  }
  for (const cmd of scene.initScript?.commands || []) {
    if (cmd.subtype === 6) {
      const d = parseInt(cmd.param);
      if (!isNaN(d)) allDests.add(d);
    }
    const matches = [...(cmd.param || '').matchAll(/\bscene\s+(\d+)/gi)];
    for (const m of matches) allDests.add(parseInt(m[1]));
  }
}

// Vérifier si les destinations correspondent aux index
console.log('\n=== VÉRIFICATION DES DESTINATIONS ===\n');
const maxDest = Math.max(...allDests);
console.log(`Plus haute destination: ${maxDest}`);
console.log(`Nombre de scènes signature: ${sigScenes.length}`);

if (maxDest > sigScenes.length) {
  console.log(`⚠️ PROBLÈME: Le jeu référence scène ${maxDest} mais on n'a que ${sigScenes.length} scènes signature!`);
  console.log(`   Il manque ${maxDest - sigScenes.length} scènes.`);
}

// Comparer les destinations avec les IDs parsés des scènes signature
console.log('\n=== CORRESPONDANCE DESTINATIONS → SCÈNES SIGNATURE ===');
const sortedDests = [...allDests].sort((a, b) => a - b);

// Les scènes signature ont des IDs parsés: 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,26,27,28,31,32,33,34,35,38,39,40,41,42,43
const sigIds = sigScenes.map(s => s.id);
console.log('IDs des scènes signature:', sigIds.join(', '));

// Créer un mapping inversé: ID signature → index (1-based)
const idToIndex = new Map();
for (let i = 0; i < sigScenes.length; i++) {
  idToIndex.set(sigScenes[i].id, i + 1);
}

console.log('\nDestinations vs Index signature:');
for (const dest of sortedDests) {
  const sigScene = sigScenes.find(s => s.id === dest);
  if (sigScene) {
    console.log(`  Dest ${dest.toString().padStart(2)} → Scène ID ${dest} ✓ (index ${idToIndex.get(dest)})`);
  } else {
    // Chercher la scène la plus proche
    const closest = sigScenes.reduce((prev, curr) =>
      Math.abs(curr.id - dest) < Math.abs(prev.id - dest) ? curr : prev
    );
    console.log(`  Dest ${dest.toString().padStart(2)} → ✗ PAS DE SCÈNE (plus proche: ID ${closest.id})`);
  }
}

// Hypothèse alternative: les IDs parsés SONT les vrais IDs
// et les destinations manquantes correspondent à des scènes manquantes
console.log('\n=== CONCLUSION ===');
const missingDests = sortedDests.filter(d => !sigIds.includes(d));
console.log(`Destinations sans scène signature: ${missingDests.join(', ')}`);
console.log(`\nCes scènes sont peut-être:`);
console.log(`  1. Dans un autre fichier VND`);
console.log(`  2. Manquantes/corrompues dans le fichier`);
console.log(`  3. Référencées par erreur dans les scripts`);
