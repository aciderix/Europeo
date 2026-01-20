#!/usr/bin/env node
const fs = require('fs');

const jsonPath = process.argv[2] || '/home/user/Europeo/couleurs1/couleurs1_parsed.json';
const data = JSON.parse(fs.readFileSync(jsonPath, 'utf-8'));

console.log('=== MÉTHODE DE PARSING PAR SCÈNE ===\n');

const byMethod = {};
for (const s of data.scenes) {
  const m = s.parseMethod;
  if (!byMethod[m]) byMethod[m] = [];
  byMethod[m].push(s.id);
}

for (const [method, ids] of Object.entries(byMethod)) {
  console.log(`${method} (${ids.length}): ${ids.join(', ')}`);
}

console.log('\n=== SCÈNES HEURISTIQUES (SANS SIGNATURE) ===\n');
const heuristics = data.scenes.filter(s => s.parseMethod !== 'signature');
for (const s of heuristics) {
  const firstFile = s.files[0]?.filename || 'N/A';
  console.log(`Scène ${s.id} [${s.sceneType}]: ${firstFile}`);
  console.log(`  Offset: 0x${s.offset.toString(16)}, Taille: ${s.length} bytes`);
  console.log(`  Méthode: ${s.parseMethod}`);
}

const sigCount = data.scenes.length - heuristics.length;
console.log('\n=== HYPOTHÈSE: SCÈNES HEURISTIQUES = DÉCALAGE ===');
console.log(`Scènes avec signature: ${sigCount}`);
console.log(`Scènes heuristiques: ${heuristics.length}`);

// Les IDs des scènes heuristiques
const heuristicIds = heuristics.map(s => s.id).sort((a,b) => a-b);
console.log(`IDs heuristiques: ${heuristicIds.join(', ')}`);

// Vérifier si retirer les scènes heuristiques résout le problème
console.log('\n=== SI ON RECALCULE LES IDs SANS HEURISTIQUES ===');
const signatureScenes = data.scenes.filter(s => s.parseMethod === 'signature');
console.log(`Scènes avec signature uniquement: ${signatureScenes.length}`);

// Mapping: index séquentiel → ID original
console.log('\nMapping ID original → nouvel index:');
for (let i = 0; i < signatureScenes.length; i++) {
  const s = signatureScenes[i];
  if (s.id !== i) {
    console.log(`  Scène originale ${s.id} → index ${i} (décalage: ${s.id - i})`);
  }
}

// Destinations manquantes: 46, 51, 52, 53, 54
console.log('\n=== DESTINATIONS MANQUANTES: OÙ SONT-ELLES? ===');
const missing = [46, 51, 52, 53, 54];
for (const m of missing) {
  // Chercher si une scène avec signature pourrait correspondre
  const offset = heuristics.length;
  const adjustedId = m - offset;
  const candidate = signatureScenes.find(s => s.id === adjustedId);
  if (candidate) {
    console.log(`Scène ${m} (ajusté -${offset}) → Scène ${adjustedId}: ${candidate.files[0]?.filename || 'N/A'}`);
  } else {
    console.log(`Scène ${m} (ajusté -${offset} = ${adjustedId}): INTROUVABLE`);
  }
}
