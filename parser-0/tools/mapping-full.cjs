#!/usr/bin/env node
const fs = require('fs');
const data = JSON.parse(fs.readFileSync('/home/user/Europeo/couleurs1/couleurs1_parsed.json', 'utf-8'));

// AUCUNE exclusion - 46 scènes + 8 Empty = 54 slots
const excludeIds = [];
const emptySlots = { 16: 2, 21: 3, 22: 3 };

console.log('=== MAPPING COMPLET (46 scènes + 8 Empty = 54 slots) ===\n');

let slot = 1;
const scenes = data.scenes.sort((a, b) => a.id - b.id);

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

console.log(`\n=== TOTAL: ${slot - 1} slots ===`);

// Vérification fontain2
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
