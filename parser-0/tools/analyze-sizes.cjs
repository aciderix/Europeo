#!/usr/bin/env node
const fs = require('fs');

const jsonPath = process.argv[2] || '/home/user/Europeo/couleurs1/couleurs1_parsed.json';
const vndPath = jsonPath.replace('_parsed.json', '.vnd');

const data = JSON.parse(fs.readFileSync(jsonPath, 'utf-8'));
const raw = fs.readFileSync(vndPath);

console.log('=== TAILLE DES SCÈNES (triées par taille décroissante) ===\n');
console.log('ID\tTaille\tFichiers\tHotspots\tPremier fichier');

const sizes = data.scenes.map(s => ({
  id: s.id,
  size: s.length,
  files: s.files.length,
  hs: s.hotspots.length,
  first: (s.files[0]?.filename || 'N/A').substring(0, 30)
}));
sizes.sort((a, b) => b.size - a.size);

for (const s of sizes.slice(0, 15)) {
  const flag = s.size > 3000 ? '⚠️ GRANDE' : '';
  console.log(`${s.id}\t${s.size}\t${s.files}\t\t${s.hs}\t\t${s.first} ${flag}`);
}

// Analyser les scènes suspectes (très grandes)
console.log('\n=== SCÈNES TRÈS GRANDES (possibles fusions) ===');
for (const scene of data.scenes) {
  if (scene.length > 4000) {
    const start = scene.offset;
    const end = scene.offset + scene.length;

    console.log(`\nScène ${scene.id}: ${scene.length} bytes (0x${start.toString(16)} - 0x${end.toString(16)})`);

    // Chercher les signatures dans cette plage
    const sigs = [];
    for (let i = start; i < end - 4; i++) {
      if (raw.readUInt32LE(i) === 0xFFFFFFDB) {
        sigs.push(i);
      }
    }
    console.log(`  Signatures trouvées: ${sigs.length}`);
    if (sigs.length > 1) {
      console.log(`  ⚠️ PLUSIEURS signatures = plusieurs scènes fusionnées!`);
      for (const sig of sigs) {
        console.log(`    @ 0x${sig.toString(16)}`);
      }
    }
  }
}
