#!/usr/bin/env node
const fs = require('fs');
const data = JSON.parse(fs.readFileSync('/home/user/Europeo/couleurs1/couleurs1_parsed.json', 'utf-8'));

console.log('Nombre de scènes parsées:', data.scenes.length);

// Chercher fontain2
console.log('\n=== RECHERCHE FONTAIN2 ===');
data.scenes.forEach(s => {
  s.files.forEach(f => {
    if (f.filename?.toLowerCase().includes('fontain')) {
      console.log(`  Scène ${s.id}, fichier: ${f.filename}`);
    }
  });
});

// Afficher scène 32 en détail
console.log('\n=== DÉTAILS SCÈNE 32 ===');
const scene32 = data.scenes.find(s => s.id === 32);
if (scene32) {
  console.log('Fichiers:');
  scene32.files.forEach(f => console.log(`  - ${f.filename}`));
}

// Afficher scènes 28-35
console.log('\n=== SCÈNES 28-35 ===');
data.scenes.filter(s => s.id >= 28 && s.id <= 35).forEach(s => {
  console.log(`Scène ${s.id}: ${s.files.map(f => f.filename).join(', ')}`);
});
