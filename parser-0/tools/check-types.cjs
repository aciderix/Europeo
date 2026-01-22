#!/usr/bin/env node
const fs = require('fs');

const jsonPath = process.argv[2] || '/home/user/Europeo/couleurs1/couleurs1_parsed.json';
const data = JSON.parse(fs.readFileSync(jsonPath, 'utf-8'));

console.log('=== TYPES DE SCÈNES DÉTECTÉS ===\n');

const byType = {};
for (const scene of data.scenes) {
  const type = scene.sceneType || 'NOT_SET';
  if (!byType[type]) byType[type] = [];
  byType[type].push(scene.id);
}

for (const [type, ids] of Object.entries(byType)) {
  console.log(`${type}: ${ids.join(', ')}`);
}

console.log('\n=== DÉTAIL META-SCÈNES ===');
for (const scene of data.scenes) {
  if (scene.sceneType && scene.sceneType !== 'game') {
    const firstFile = scene.files[0]?.filename || 'N/A';
    console.log(`Scène ${scene.id} [${scene.sceneType}]: ${firstFile}`);
  }
}

// Statistiques
const gameScenes = data.scenes.filter(s => s.sceneType === 'game').length;
const metaScenes = data.scenes.length - gameScenes;
console.log(`\n=== RÉSUMÉ ===`);
console.log(`Total scènes: ${data.scenes.length}`);
console.log(`Scènes de jeu: ${gameScenes}`);
console.log(`Meta-scènes: ${metaScenes}`);
