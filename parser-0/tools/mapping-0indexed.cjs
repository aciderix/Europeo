#!/usr/bin/env node
const fs = require('fs');
const data = JSON.parse(fs.readFileSync('/home/user/Europeo/couleurs1/couleurs1_parsed.json', 'utf-8'));

// Exclusion: 28 (Toolbar = texte indicatif)
const excludeIds = [28];
const emptySlots = { 16: 2, 21: 3, 22: 3 };

console.log('=== MAPPING 0-INDEXED (comme le jeu) ===\n');

let slot = 0;  // Commence à 0, pas 1
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

console.log(`\n=== TOTAL: slots 0-${slot-1} (${slot} slots) ===`);

// Vérification fontain2
console.log('\n=== VÉRIFICATION ===');
slot = 0;
for (const s of scenes) {
  if (s.files.some(f => f.filename?.includes('fontain'))) {
    console.log(`fontain2 (parsé ${s.id}) = slot ${slot}`);
  }
  if (s.files.some(f => f.filename?.toLowerCase().includes('perdu'))) {
    console.log(`fin perdu (parsé ${s.id}) = slot ${slot}`);
  }
  slot++;
  if (emptySlots[s.id]) slot += emptySlots[s.id];
}
