#!/usr/bin/env node
const fs = require('fs');
const buffer = fs.readFileSync('/home/user/Europeo/couleurs1/couleurs1.vnd');

// Chercher "Empty" (5 bytes) avec son préfixe de longueur (05 00 00 00)
const pattern = Buffer.from([0x05, 0x00, 0x00, 0x00, 0x45, 0x6D, 0x70, 0x74, 0x79]); // len=5 + "Empty"

console.log('=== POSITIONS DE "Empty" DANS LE VND ===\n');

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
    console.log(`Empty @ 0x${i.toString(16).toUpperCase()} (${i})`);
  }
}

console.log(`\nTotal: ${positions.length} occurrences`);

// Charger les offsets de scènes
const data = JSON.parse(fs.readFileSync('/home/user/Europeo/couleurs1/couleurs1_parsed.json', 'utf-8'));
const sceneOffsets = data.scenes.map(s => ({ id: s.id, start: s.offset, end: s.offset + s.length }));

console.log('\n=== ASSOCIATION SCÈNE -> EMPTY ===');
positions.forEach(pos => {
  const scene = sceneOffsets.find(s => pos >= s.start && pos < s.end);
  if (scene) {
    console.log(`0x${pos.toString(16).toUpperCase()} -> Scène ${scene.id}`);
  } else {
    console.log(`0x${pos.toString(16).toUpperCase()} -> ???`);
  }
});

// Compter par scène
console.log('\n=== EMPTY PAR SCÈNE ===');
const countByScene = {};
positions.forEach(pos => {
  const scene = sceneOffsets.find(s => pos >= s.start && pos < s.end);
  if (scene) {
    countByScene[scene.id] = (countByScene[scene.id] || 0) + 1;
  }
});
Object.entries(countByScene).forEach(([id, count]) => {
  console.log(`Scène ${id}: ${count} Empty`);
});
