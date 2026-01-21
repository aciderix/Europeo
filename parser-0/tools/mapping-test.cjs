#!/usr/bin/env node
const fs = require('fs');
const data = JSON.parse(fs.readFileSync('/home/user/Europeo/couleurs1/couleurs1_parsed.json', 'utf-8'));

// Exclure: 0 (global_vars), 25, 28 (Toolbar vide), 29, 30 (metadata)
const excludeIds = [0, 25, 28, 29, 30];
const emptySlots = { 16: 2, 21: 3, 22: 3 };

console.log('=== MAPPING EXCLUANT METADATA (0, 25, 29, 30) ===\n');

let slot = 1;
const scenes = data.scenes
  .filter(s => !excludeIds.includes(s.id))
  .sort((a, b) => a.id - b.id);

console.log('Parsé | Slot | Fichier');
console.log('-'.repeat(60));

for (const s of scenes) {
  const file = (s.files[0]?.filename || '').substring(0, 30);
  console.log(`${s.id.toString().padStart(5)} | ${slot.toString().padStart(4)} | ${file}`);

  const currSlot = slot;
  slot++;

  if (emptySlots[s.id]) {
    const count = emptySlots[s.id];
    console.log(`      | [${count} EMPTY après slot ${currSlot}]`);
    slot += count;
  }
}

// Chercher fontain2
console.log('\n=== VÉRIFICATION FONTAIN2 ===');
slot = 1;
for (const s of scenes) {
  if (s.files.some(f => f.filename?.includes('fontain'))) {
    console.log(`Fontain2 (parsé ${s.id}) = slot ${slot}`);
    break;
  }
  slot++;
  if (emptySlots[s.id]) slot += emptySlots[s.id];
}

// Vérification avec scène 1 → 39
console.log('\n=== SCÈNE 1 NAVIGUE VERS 39 ===');
const scene1 = data.scenes.find(s => s.id === 1);
const dest39 = scene1?.hotspots?.flatMap(h => h.commands)?.find(c => c.param === '39');
if (dest39) {
  console.log('Scène 1 a bien destination 39');
}

// Le slot 39 devrait être fontain2
slot = 1;
let slot39Scene = null;
for (const s of scenes) {
  if (slot === 39) {
    slot39Scene = s;
    break;
  }
  slot++;
  if (emptySlots[s.id]) slot += emptySlots[s.id];
}
if (slot39Scene) {
  console.log(`Slot 39 = parsé ${slot39Scene.id}: ${slot39Scene.files[0]?.filename}`);
} else {
  console.log('Slot 39 = EMPTY ou non trouvé');
}
