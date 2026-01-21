#!/usr/bin/env node
const fs = require('fs');
const buffer = fs.readFileSync('/home/user/Europeo/couleurs1/couleurs1.vnd');
const data = JSON.parse(fs.readFileSync('/home/user/Europeo/couleurs1/couleurs1_parsed.json', 'utf-8'));

console.log('=== ANALYSE COMPLÈTE DES "EMPTY" ===\n');

// Chercher toutes les occurrences de "Empty" avec différents formats
const patterns = [
  { name: 'Pascal (len=5)', bytes: [0x05, 0x00, 0x00, 0x00, 0x45, 0x6D, 0x70, 0x74, 0x79] },
  { name: 'Pascal (len=6 avec null)', bytes: [0x06, 0x00, 0x00, 0x00, 0x45, 0x6D, 0x70, 0x74, 0x79, 0x00] },
  { name: 'Raw "Empty"', bytes: [0x45, 0x6D, 0x70, 0x74, 0x79] }
];

// Recherche du pattern Pascal len=5 (le plus courant)
const pattern = Buffer.from([0x05, 0x00, 0x00, 0x00, 0x45, 0x6D, 0x70, 0x74, 0x79]);
const positions = [];

for (let i = 0; i < buffer.length - pattern.length; i++) {
  let match = true;
  for (let j = 0; j < pattern.length; j++) {
    if (buffer[i + j] !== pattern[j]) {
      match = false;
      break;
    }
  }
  if (match) {
    positions.push(i);
  }
}

console.log(`Trouvé ${positions.length} "Empty" (format Pascal len=5)\n`);

// Pour chaque Empty, analyser son contexte
const sceneOffsets = data.scenes.map(s => ({
  id: s.id,
  start: s.offset,
  end: s.offset + s.length,
  configOffset: s.config?.offset || -1,
  filesEnd: s.files.length > 0 ? s.files[s.files.length - 1].offset + 50 : s.offset
}));

positions.forEach((pos, idx) => {
  const scene = sceneOffsets.find(s => pos >= s.start && pos < s.end);

  console.log(`[${idx + 1}] Empty @ 0x${pos.toString(16).toUpperCase()}`);

  if (scene) {
    const relPos = pos - scene.start;
    const inFileTable = pos < scene.filesEnd;
    const afterConfig = scene.configOffset > 0 && pos > scene.configOffset;

    console.log(`    Scène: ${scene.id}`);
    console.log(`    Position relative: ${relPos} bytes`);
    console.log(`    Zone: ${inFileTable ? 'TABLE FICHIERS' : afterConfig ? 'HOTSPOTS/TOOLTIPS' : 'SCRIPT/CONFIG'}`);

    // Regarder le contexte autour
    const contextBefore = buffer.slice(Math.max(0, pos - 16), pos);
    const contextAfter = buffer.slice(pos + 9, Math.min(buffer.length, pos + 25));

    console.log(`    Avant: ${[...contextBefore].map(b => b.toString(16).padStart(2, '0')).join(' ')}`);
    console.log(`    Après: ${[...contextAfter].map(b => b.toString(16).padStart(2, '0')).join(' ')}`);
  }
  console.log();
});

// Compter par scène
console.log('=== RÉSUMÉ PAR SCÈNE ===');
const countByScene = {};
positions.forEach(pos => {
  const scene = sceneOffsets.find(s => pos >= s.start && pos < s.end);
  if (scene) {
    countByScene[scene.id] = (countByScene[scene.id] || 0) + 1;
  }
});

let total = 0;
Object.entries(countByScene).sort((a, b) => parseInt(a[0]) - parseInt(b[0])).forEach(([id, count]) => {
  console.log(`Scène ${id}: ${count} Empty`);
  total += count;
});
console.log(`\nTotal: ${total} Empty`);
