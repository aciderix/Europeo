#!/usr/bin/env node
/**
 * Test de fusion vnoptions.dll (29) + fleche.cur (30)
 * SANS modifier le parser original
 */
const fs = require('fs');
const data = JSON.parse(fs.readFileSync('/home/user/Europeo/couleurs1/couleurs1_parsed.json', 'utf-8'));

console.log('=== TEST FUSION VNOPTIONS (29) + FLECHE.CUR (30) ===\n');

// Simuler la fusion : on garde 29 et on merge les données de 30 dedans
const scene29 = data.scenes.find(s => s.id === 29);
const scene30 = data.scenes.find(s => s.id === 30);

console.log('AVANT FUSION:');
console.log(`  Scène 29: ${scene29.files.map(f => f.filename).join(', ')}`);
console.log(`    Hotspots: ${scene29.hotspots.length}`);
console.log(`    Offset: 0x${scene29.offset.toString(16)} - 0x${(scene29.offset + scene29.length).toString(16)}`);
console.log(`  Scène 30: ${scene30.files.map(f => f.filename).join(', ')}`);
console.log(`    Hotspots: ${scene30.hotspots.length}`);
console.log(`    Offset: 0x${scene30.offset.toString(16)} - 0x${(scene30.offset + scene30.length).toString(16)}`);

// Créer une copie fusionnée
const mergedScene29 = {
  ...scene29,
  files: [...scene29.files, ...scene30.files],
  hotspots: [...scene29.hotspots, ...scene30.hotspots],
  length: (scene30.offset + scene30.length) - scene29.offset
};

console.log('\nAPRÈS FUSION (simulée):');
console.log(`  Scène 29: ${mergedScene29.files.map(f => f.filename).join(', ')}`);
console.log(`    Hotspots: ${mergedScene29.hotspots.length}`);
console.log(`    Offset: 0x${mergedScene29.offset.toString(16)} - 0x${(mergedScene29.offset + mergedScene29.length).toString(16)}`);

// Créer la liste de scènes fusionnées (sans scène 30)
const mergedScenes = data.scenes
  .filter(s => s.id !== 30)
  .map(s => s.id === 29 ? mergedScene29 : s);

console.log(`\nNombre de scènes: ${data.scenes.length} → ${mergedScenes.length}`);

// Maintenant calculer le mapping avec cette liste fusionnée
console.log('\n=== MAPPING AVEC FUSION ===\n');

// Exclure seulement 28 (Toolbar) maintenant que 30 est fusionné avec 29
const excludeIds = [28];
const emptySlots = { 16: 2, 21: 3, 22: 3 };

let slot = 1;
const scenes = mergedScenes
  .filter(s => !excludeIds.includes(s.id))
  .sort((a, b) => a.id - b.id);

console.log('Parsé | Slot | Fichier');
console.log('-'.repeat(60));

let fontain2Slot = -1;

for (const s of scenes) {
  const file = (s.files[0]?.filename || '').substring(0, 30);

  // Vérifier si c'est fontain2
  if (s.files.some(f => f.filename?.includes('fontain'))) {
    fontain2Slot = slot;
  }

  // Afficher seulement les scènes clés
  if (s.id <= 5 || s.id >= 28 || [16, 21, 22].includes(s.id)) {
    console.log(`${s.id.toString().padStart(5)} | ${slot.toString().padStart(4)} | ${file}`);
  }

  const currSlot = slot;
  slot++;

  if (emptySlots[s.id]) {
    const count = emptySlots[s.id];
    console.log(`      | [${count} EMPTY]`);
    slot += count;
  }
}

console.log('\n=== VÉRIFICATION ===');
console.log(`Fontain2 (parsé 32) = slot ${fontain2Slot}`);
console.log(`Attendu: slot 39`);
console.log(`Résultat: ${fontain2Slot === 39 ? '✓ CORRECT' : '✗ INCORRECT'}`);

// Vérifier le total
console.log(`\nTotal slots: ${slot - 1}`);
console.log(`Attendu: ~52-54 slots`);

// Vérifier la scène 1
const scene1Slot = scenes.findIndex(s => s.id === 1) + 1 +
  (scenes.slice(0, scenes.findIndex(s => s.id === 1)).some(s => emptySlots[s.id]) ?
    Object.entries(emptySlots).filter(([id]) => parseInt(id) < 1).reduce((sum, [,v]) => sum + v, 0) : 0);

console.log(`\nScène 1 (village) = slot 2 (car slot 1 = variables)`);
