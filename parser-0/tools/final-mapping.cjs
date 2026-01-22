#!/usr/bin/env node
const fs = require('fs');
const data = JSON.parse(fs.readFileSync('/home/user/Europeo/couleurs1/couleurs1_parsed.json', 'utf-8'));

console.log('=== SCÈNES HEURISTIQUES = VRAIES SCÈNES MANQUANTES? ===\n');

const heurScenes = data.scenes.filter(s => s.parseMethod !== 'signature');
for (const s of heurScenes) {
  console.log(`Parsé ${s.id.toString().padStart(2)} [${s.sceneType}]: ${s.files[0]?.filename || 'N/A'}`);

  // Chercher si cette scène est référencée comme destination
  let refs = [];
  for (const scene of data.scenes) {
    for (const hs of scene.hotspots) {
      for (const cmd of hs.commands) {
        if (cmd.subtype === 6 && parseInt(cmd.param) === s.id) {
          refs.push(scene.id);
        }
        const m = (cmd.param || '').match(/scene\s+(\d+)/i);
        if (m && parseInt(m[1]) === s.id) {
          refs.push(scene.id);
        }
      }
    }
  }

  if (refs.length > 0) {
    console.log(`  → Référencée par scènes: ${[...new Set(refs)].join(', ')}`);
  } else {
    console.log('  → PAS référencée comme destination');
  }
}

console.log('\n=== DESTINATIONS MANQUANTES VS HEURISTIQUES ===');
const missingDests = [36, 44, 51, 52, 53, 54];
for (const d of missingDests) {
  const heur = heurScenes.find(s => s.id === d);
  if (heur) {
    console.log(`Dest ${d}: Scène heuristique ${heur.id} (${heur.files[0]?.filename})`);
  } else {
    // Chercher dans les scènes avec offset
    const adjusted = d - 7;
    const sig = data.scenes.find(s => s.id === adjusted && s.parseMethod === 'signature');
    if (sig && adjusted > 31) {
      console.log(`Dest ${d}: Avec offset -7 = parsé ${adjusted} (${sig.files[0]?.filename})`);
    } else {
      console.log(`Dest ${d}: ✗ INTROUVABLE`);
    }
  }
}

// Construire le mapping final
console.log('\n=== MAPPING FINAL PROPOSÉ ===');
const finalMapping = [];

for (const s of data.scenes) {
  let gameId;

  if (s.parseMethod !== 'signature') {
    // Scènes heuristiques gardent leur ID
    gameId = s.id;
  } else if (s.id <= 31) {
    // Scènes 1-31: pas de décalage
    gameId = s.id;
  } else {
    // Scènes après 31: offset +7
    gameId = s.id + 7;
  }

  finalMapping.push({
    parsed: s.id,
    game: gameId,
    method: s.parseMethod,
    file: (s.files[0]?.filename || 'N/A').substring(0, 30)
  });
}

console.log('Parsé | Jeu  | Méthode   | Fichier');
console.log('-'.repeat(70));
for (const m of finalMapping.filter(x => x.parsed >= 30 || x.method !== 'signature')) {
  console.log(`${m.parsed.toString().padStart(5)} | ${m.game.toString().padStart(4)} | ${m.method.substring(0, 9).padEnd(9)} | ${m.file}`);
}
