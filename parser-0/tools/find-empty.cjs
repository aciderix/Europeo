#!/usr/bin/env node
const fs = require('fs');
const data = JSON.parse(fs.readFileSync('/home/user/Europeo/couleurs1/couleurs1_parsed.json', 'utf-8'));

console.log('=== RECHERCHE DE TOUS LES "EMPTY" ===\n');

data.scenes.forEach(s => {
  // Chercher dans les fichiers
  s.files.forEach((f, idx) => {
    if (f.filename?.toLowerCase() === 'empty') {
      console.log(`Scène ${s.id}, fichier[${idx}]: "${f.filename}"`);
    }
  });

  // Chercher dans les hotspots (tooltips)
  s.hotspots?.forEach((h, idx) => {
    h.commands?.forEach(c => {
      if (c.param?.toLowerCase() === 'empty') {
        console.log(`Scène ${s.id}, hotspot[${idx}]: tooltip "${c.param}"`);
      }
    });
    if (h.tooltip?.text?.toLowerCase() === 'empty') {
      console.log(`Scène ${s.id}, hotspot[${idx}]: tooltip "${h.tooltip.text}"`);
    }
  });
});

console.log('\n=== SCÈNES AVEC "EMPTY" DANS FICHIERS ===');
data.scenes.forEach(s => {
  const emptyCount = s.files.filter(f => f.filename?.toLowerCase() === 'empty').length;
  if (emptyCount > 0) {
    console.log(`Scène ${s.id}: ${emptyCount} Empty`);
  }
});
