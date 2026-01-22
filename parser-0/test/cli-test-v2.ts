#!/usr/bin/env npx tsx
/**
 * VND Parser V2 Test - Teste les améliorations du parser
 * Usage: npx tsx test/cli-test-v2.ts <fichier.vnd> [maxScenes]
 */

import * as fs from 'fs';
import * as path from 'path';

// Import du parser V2 modifié
import { VNDSequentialParser } from './vndParser-v2.ts';

function main() {
  const args = process.argv.slice(2);

  if (args.length < 1) {
    console.log('Usage: npx tsx test/cli-test-v2.ts <fichier.vnd> [maxScenes]');
    process.exit(1);
  }

  const inputPath = path.resolve(args[0]);
  const maxScenes = args[1] ? parseInt(args[1]) : 50;

  if (!fs.existsSync(inputPath)) {
    console.error(`Erreur: Fichier non trouvé: ${inputPath}`);
    process.exit(1);
  }

  console.log(`\n${'='.repeat(60)}`);
  console.log(`VND Parser V2 - TEST`);
  console.log(`${'='.repeat(60)}`);
  console.log(`Fichier: ${inputPath}`);
  console.log(`Max scènes: ${maxScenes}`);

  const buffer = fs.readFileSync(inputPath);
  const arrayBuffer = buffer.buffer.slice(buffer.byteOffset, buffer.byteOffset + buffer.byteLength);

  console.log(`Taille: ${buffer.length} bytes\n`);

  const parser = new VNDSequentialParser(arrayBuffer);
  const result = parser.parse(maxScenes);

  // Stats
  console.log(`\n${'='.repeat(60)}`);
  console.log('STATISTIQUES V2');
  console.log(`${'='.repeat(60)}`);
  console.log(`Scènes: ${result.scenes.length}`);
  console.log(`Fichiers: ${result.scenes.reduce((a, s) => a + s.files.length, 0)}`);
  console.log(`Hotspots: ${result.scenes.reduce((a, s) => a + s.hotspots.length, 0)}`);

  // Compte les éléments recovered
  let recoveredCount = 0;
  let tooltipCount = 0;
  result.scenes.forEach(s => {
    s.hotspots.forEach(h => {
      if (h.isRecovered) recoveredCount++;
      if ((h as any).isTooltip) tooltipCount++;
    });
  });
  console.log(`Recovered: ${recoveredCount}`);
  console.log(`Tooltips: ${tooltipCount}`);

  // Sauvegarde
  const baseName = path.basename(inputPath, path.extname(inputPath));
  const jsonPath = path.join(path.dirname(inputPath), `${baseName}_v2.json`);
  fs.writeFileSync(jsonPath, JSON.stringify(result, null, 2));
  console.log(`\nJSON: ${jsonPath}`);

  // Affiche les éléments recovered pour comparaison
  console.log(`\n--- ÉLÉMENTS RECOVERED (pour vérification) ---`);
  result.scenes.forEach(s => {
    s.hotspots.filter(h => h.isRecovered).forEach(h => {
      console.log(`Scène ${s.id} @ 0x${h.offset.toString(16)}: ${h.commands[0]?.param?.substring(0, 50)}...`);
    });
  });
}

main();
