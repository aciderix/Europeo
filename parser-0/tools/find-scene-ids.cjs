#!/usr/bin/env node
/**
 * Cherche les IDs de scène explicites dans le VND
 * Hypothèse: L'ID pourrait être stocké au début de chaque scène
 */
const fs = require('fs');

const jsonPath = process.argv[2] || '/home/user/Europeo/couleurs1/couleurs1_parsed.json';
const vndPath = jsonPath.replace('_parsed.json', '.vnd');

const data = JSON.parse(fs.readFileSync(jsonPath, 'utf-8'));
const raw = fs.readFileSync(vndPath);

console.log('=== RECHERCHE IDs EXPLICITES DANS LE VND ===\n');

// Pour chaque scène, regarder les premiers bytes
console.log('Scène | Offset    | Méthode            | Premiers 16 bytes (hex) | Interprétation');
console.log('-'.repeat(100));

for (const scene of data.scenes) {
  const offset = scene.offset;
  const method = scene.parseMethod.padEnd(18);

  // Lire les premiers bytes
  const bytes = [];
  for (let i = 0; i < 16 && offset + i < raw.length; i++) {
    bytes.push(raw[offset + i]);
  }
  const hexStr = bytes.map(b => b.toString(16).padStart(2, '0')).join(' ');

  // Interpréter comme différents types
  const u32_0 = raw.readUInt32LE(offset);
  const u32_4 = offset + 4 < raw.length ? raw.readUInt32LE(offset + 4) : 0;
  const u16_0 = raw.readUInt16LE(offset);
  const u16_2 = raw.readUInt16LE(offset + 2);

  let interp = `u32: ${u32_0}, ${u32_4} | u16: ${u16_0}, ${u16_2}`;

  // Est-ce que le premier u32 ou u16 ressemble à un ID de scène?
  const possibleId = u16_0 <= 100 ? `ID=${u16_0}?` : '';

  console.log(`${scene.id.toString().padStart(5)} | 0x${offset.toString(16).padStart(6, '0')} | ${method} | ${hexStr} | ${possibleId}`);
}

// Chercher un pattern où le premier nombre correspond à l'ID attendu
console.log('\n=== ANALYSE DES PREMIERS BYTES ===\n');

// Pour les scènes avec signature, vérifier si le config a des infos
console.log('Scènes avec signature - analyse du config:');
console.log('Scène | Config Offset | Flag | ints[0] | ints[1] | ints[2]');
console.log('-'.repeat(70));

for (const scene of data.scenes.filter(s => s.parseMethod === 'signature')) {
  const c = scene.config;
  console.log(`${scene.id.toString().padStart(5)} | 0x${c.offset.toString(16).padStart(6, '0')}   | ${c.flag.toString().padStart(4)} | ${(c.ints[0] || 0).toString().padStart(7)} | ${(c.ints[1] || 0).toString().padStart(7)} | ${(c.ints[2] || 0).toString().padStart(7)}`);
}
