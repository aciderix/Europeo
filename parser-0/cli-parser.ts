#!/usr/bin/env npx ts-node
/**
 * VND Parser CLI - Version ligne de commande pour tester le parser
 * Usage: npx ts-node cli-parser.ts <fichier.vnd> [maxScenes]
 */

import * as fs from 'fs';
import * as path from 'path';
import { VNDSequentialParser } from './services/vndParser.ts';

// Polyfill TextDecoder pour Node.js si nécessaire
if (typeof TextDecoder === 'undefined') {
  const util = require('util');
  (global as any).TextDecoder = util.TextDecoder;
}

function main() {
  const args = process.argv.slice(2);

  if (args.length < 1) {
    console.log('Usage: npx ts-node cli-parser.ts <fichier.vnd> [maxScenes]');
    console.log('Exemple: npx ts-node cli-parser.ts ../couleurs1/couleurs1.vnd 50');
    process.exit(1);
  }

  const inputPath = path.resolve(args[0]);
  const maxScenes = args[1] ? parseInt(args[1]) : 50;

  if (!fs.existsSync(inputPath)) {
    console.error(`Erreur: Fichier non trouvé: ${inputPath}`);
    process.exit(1);
  }

  console.log(`\n${'='.repeat(60)}`);
  console.log(`VND Sequential Parser - CLI`);
  console.log(`${'='.repeat(60)}`);
  console.log(`Fichier: ${inputPath}`);
  console.log(`Max scènes: ${maxScenes}`);
  console.log(`${'='.repeat(60)}\n`);

  // Lire le fichier
  const buffer = fs.readFileSync(inputPath);
  const arrayBuffer = buffer.buffer.slice(buffer.byteOffset, buffer.byteOffset + buffer.byteLength);

  console.log(`Taille du fichier: ${buffer.length} bytes (${(buffer.length / 1024).toFixed(2)} KB)\n`);

  // Parser
  const parser = new VNDSequentialParser(arrayBuffer);
  const result = parser.parse(maxScenes);

  // Afficher les logs
  console.log('\n--- LOGS DU PARSER ---\n');
  result.logs.forEach(log => console.log(log));

  // Statistiques
  console.log(`\n${'='.repeat(60)}`);
  console.log('STATISTIQUES');
  console.log(`${'='.repeat(60)}`);
  console.log(`Scènes parsées: ${result.scenes.length}`);
  console.log(`Total fichiers: ${result.scenes.reduce((acc, s) => acc + s.files.length, 0)}`);
  console.log(`Total hotspots: ${result.scenes.reduce((acc, s) => acc + s.hotspots.length, 0)}`);
  console.log(`Total commandes init: ${result.scenes.reduce((acc, s) => acc + s.initScript.commands.length, 0)}`);

  // Résumé par scène
  console.log(`\n--- RÉSUMÉ PAR SCÈNE ---\n`);
  result.scenes.forEach(scene => {
    const status = scene.parseMethod === 'signature' ? '✓' :
                   scene.parseMethod === 'heuristic_recovered' ? '~' : '?';
    console.log(`[${status}] Scène #${scene.id} @ 0x${scene.offset.toString(16).toUpperCase()}`);
    console.log(`    Fichiers: ${scene.files.length}, Hotspots: ${scene.hotspots.length}, Init: ${scene.initScript.commands.length}`);
    if (scene.warnings.length > 0) {
      scene.warnings.forEach(w => console.log(`    ⚠ ${w}`));
    }
  });

  // Sauvegarder le JSON
  const baseName = path.basename(inputPath, path.extname(inputPath));
  const outputDir = path.dirname(inputPath);
  const jsonPath = path.join(outputDir, `${baseName}_parsed.json`);
  const logsPath = path.join(outputDir, `${baseName}_logs.txt`);

  fs.writeFileSync(jsonPath, JSON.stringify(result, null, 2));
  fs.writeFileSync(logsPath, result.logs.join('\n'));

  console.log(`\n${'='.repeat(60)}`);
  console.log('FICHIERS GÉNÉRÉS');
  console.log(`${'='.repeat(60)}`);
  console.log(`JSON: ${jsonPath}`);
  console.log(`Logs: ${logsPath}`);
}

main();
