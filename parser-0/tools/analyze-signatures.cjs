#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const jsonPath = process.argv[2] || '../couleurs1/couleurs1_parsed.json';
const vndPath = jsonPath.replace('_parsed.json', '.vnd');

const data = JSON.parse(fs.readFileSync(path.resolve(__dirname, jsonPath), 'utf-8'));
const raw = fs.readFileSync(path.resolve(__dirname, vndPath));

// Trouver toutes les signatures
const signatures = [];
for (let i = 0; i < raw.length - 4; i++) {
  if (raw.readUInt32LE(i) === 0xFFFFFFDB) {
    signatures.push(i);
  }
}

console.log('=== ANALYSE DES SCÈNES SANS SIGNATURE ===\n');

const scenesWithoutSig = [];
const scenesWithSig = [];

for (const scene of data.scenes) {
  const start = scene.offset;
  const end = scene.offset + scene.length;
  const sigInRange = signatures.filter(s => s >= start && s < end);

  if (sigInRange.length === 0) {
    scenesWithoutSig.push(scene);
    console.log(`Scène ${scene.id} @ 0x${start.toString(16)} - 0x${end.toString(16)}: AUCUNE signature`);
    console.log(`  Method: ${scene.parseMethod}`);
    console.log(`  Fichiers: ${scene.files.map(f => f.filename).slice(0, 3).join(', ')}`);
    console.log(`  Hotspots: ${scene.hotspots.length}`);
    console.log();
  } else {
    scenesWithSig.push(scene);
  }
}

console.log(`\n=== RÉSUMÉ ===`);
console.log(`Scènes avec signature: ${scenesWithSig.length}`);
console.log(`Scènes sans signature: ${scenesWithoutSig.length}`);
console.log(`Signatures totales: ${signatures.length}`);

// La différence suggère combien de vraies scènes manquent
const expectedScenes = signatures.length; // Chaque vraie scène devrait avoir 1 signature
console.log(`\nSi chaque vraie scène a 1 signature: ${expectedScenes} scènes attendues`);
console.log(`Scènes parsées: ${data.scenes.length}`);

if (data.scenes.length > expectedScenes) {
  console.log(`\n⚠️ ${data.scenes.length - expectedScenes} scènes sont probablement des faux positifs`);
}
