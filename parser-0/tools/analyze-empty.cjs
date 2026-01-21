#!/usr/bin/env node
const fs = require('fs');
const buffer = fs.readFileSync('/home/user/Europeo/couleurs1/couleurs1.vnd');
const data = JSON.parse(fs.readFileSync('/home/user/Europeo/couleurs1/couleurs1_parsed.json', 'utf-8'));

// Positions des Empty
const emptyPositions = [0x7FE9, 0x804E, 0x865E, 0x86C3, 0x8728, 0x90F2, 0x9157, 0x91BC];

console.log('=== ANALYSE DÉTAILLÉE DES EMPTY ===\n');

emptyPositions.forEach(pos => {
  // Trouver la scène
  const scene = data.scenes.find(s => pos >= s.offset && pos < s.offset + s.length);
  if (!scene) return;

  // Déterminer si c'est dans la table de fichiers ou après
  const fileTableEnd = scene.files.length > 0 ?
    scene.files[scene.files.length - 1].offset + 100 : scene.offset + 100;

  const configOffset = scene.config?.offset || -1;

  let location;
  if (configOffset > 0 && pos > configOffset) {
    location = 'APRES CONFIG (hotspots/tooltips)';
  } else if (pos < fileTableEnd) {
    location = 'TABLE DE FICHIERS';
  } else {
    location = 'ZONE SCRIPT/CONFIG';
  }

  console.log(`0x${pos.toString(16).toUpperCase()} -> Scène ${scene.id}`);
  console.log(`  Scène offset: 0x${scene.offset.toString(16)}`);
  console.log(`  Config offset: ${configOffset > 0 ? '0x' + configOffset.toString(16) : 'N/A'}`);
  console.log(`  Position relative: ${pos - scene.offset} bytes dans la scène`);
  console.log(`  Location probable: ${location}`);
  console.log();
});

// Vérifier si Empty est dans les fichiers parsés
console.log('=== EMPTY DANS LES FICHIERS PARSÉS ===');
data.scenes.forEach(s => {
  s.files.forEach(f => {
    if (f.filename?.toLowerCase() === 'empty') {
      console.log(`Scène ${s.id}, slot ${f.slot}: Empty @ 0x${f.offset.toString(16)}`);
    }
  });
});
