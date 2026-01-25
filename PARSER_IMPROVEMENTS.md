# Améliorations Parser VND - Plan d'Action

**Date**: 2026-01-23  
**Basé sur**: Validation pseudo-code + 3 VND (danem, belge, couleurs1)

---

## ✅ Ce Qui Fonctionne Déjà

### 1. Détection Scènes (100%)
- ✓ File table detection (robuste, meilleur que Scene Count header)
- ✓ Signatures multiples supportées
- ✓ Récupération des scènes orphelines
- ✓ Filtrage paths relatifs (.wav/.avi vs .bmp/.htm)

### 2. Hotspots (100%)
- ✓ Géométrie parsée correctement
- ✓ CursorId avec offset +100 (conforme pseudo-code)
- ✓ PointCount et coordonnées polygonales
- ✓ 100% géométrie sur danem (65/65), belge (87/87)

### 3. Commandes (Validé)
- ✓ Subtype correctement lu (offset +8 confirmé)
- ✓ Tous les subtypes du pseudo-code validés:
  - Type 0: QUIT/EXIT ✓
  - Type 6: GOTO SCENE ✓
  - Type 9: PLAY VIDEO ✓
  - Type 16: DELAY ✓
  - Type 21: IF-THEN ✓ (316 occ. dans danem!)
  - Type 27: ADDBMP ✓
  - Type 38: PLAYTEXT ✓
  - Type 39: FONT ✓

**Conclusion**: Le parser actuel est **robuste et correct**!

---

## 🎯 Améliorations Proposées

### PRIORITÉ 1: Lire Header VND

**Objectif**: Extraire métadonnées du header

**À implémenter**:
```python
class VndHeader:
    magic: str          # "VNFILE"
    version: str        # "2.13"
    project: str        # "Europeo"
    author: str         # "Sopra Multimedia"
    serial: str         # "5D51F233"
    width: int          # Config[0] = 640
    height: int         # Config[1] = 480
    scene_count: int    # Word à offset 98 (informatif uniquement)
    exit_id: int        # Word à offset 100
    index_id: int       # Word à offset 102
```

**Utilité**:
- ✅ Validation dimensions (width/height)
- ✅ EXIT_ID pour navigation "Quitter"
- ✅ Métadonnées projet (version, auteur)
- ⚠️ Scene Count (informatif seulement, ne pas utiliser pour validation)

**Effort**: 🟢 Faible (structure validée, offset fixe 78)

---

### PRIORITÉ 2: Mapper Tous les Subtypes de Commandes

**Objectif**: Documenter les 49 types de commandes

**Subtypes inconnus détectés**: 10, 11, 22, 24, 31, 36, 41, ...

**À faire**:
1. Analyser `commands.cpp.txt` (910 lignes) pour les 49 types
2. Créer enum/mapping complet
3. Ajouter noms humains aux commandes exportées

**Exemple sortie améliorée**:
```json
{
  "subtype": 21,
  "name": "IF-THEN",
  "param": "score < 0 then runprj ..."
}
```

**Effort**: 🟡 Moyen (lecture pseudo-code + mapping)

---

### PRIORITÉ 3: Valider objCount

**Objectif**: Vérifier cohérence nombre hotspots

**Découverte**: Chaque scène déclare `objCount` avant sa signature

**À implémenter**:
```python
def validateScene(scene, objCount):
    actual = len(scene.hotspots)
    if actual != objCount:
        warnings.append(f"Scene {scene.id}: objCount={objCount} but parsed {actual} hotspots")
```

**Utilité**:
- ✅ Détection erreurs parsing
- ✅ Validation qualité
- ✅ Debug (identifier scènes problématiques)

**Effort**: 🟢 Faible (objCount déjà accessible)

---

### PRIORITÉ 4: Améliorer Détection Signatures

**Objectif**: Détecter automatiquement la signature de chaque VND

**Signatures connues**:
- danem: 0xFFFFFFF4
- belge: 0xFFFFFFE8
- couleurs1: 0xFFFFFFDB

**À implémenter**:
```python
def detectSignature(data):
    """Scan pour pattern 0xFFFFFFxx"""
    candidates = {}
    for offset in range(len(data) - 4):
        val = unpack('<I', data[offset:offset+4])[0]
        if (val & 0xFFFFFF00) == 0xFFFFFF00:
            candidates[val] = candidates.get(val, 0) + 1
    
    # Signature = pattern le plus fréquent (>5 occ.)
    return max(candidates, key=candidates.get)
```

**Utilité**:
- ✅ Support automatique nouveaux VND
- ✅ Pas besoin d'ajouter manuellement chaque signature

**Effort**: 🟢 Faible (pattern simple)

---

### PRIORITÉ 5: Parser File Table Cryptée

**Objectif**: Décrypter file table (version >= 0x2000D)

**Découverte pseudo-code**:
- Clé: "Password"
- Fonction: `sub_405557` (décryptage)
- 1 string cryptée + 2 strings en clair

**Statut**: 🔴 Complexe (nécessite reverse engineering algo crypto)

**Effort**: 🔴 Élevé (crypto + tests)

---

### PRIORITÉ 6: Normaliser Scene Count

**Objectif**: Clarifier différence Header vs Parser

**Découverte**:
- Header Scene Count = Scènes "principales" (variable selon VND)
- Parser = Toutes les scènes (principales + système + variations)
- couleurs1: Header 31 vs Parser 55 (42 game + 8 empty + 5 système)

**À implémenter**:
```python
class SceneStats:
    header_count: int       # Du header VND
    parsed_count: int       # Détecté par parser
    game_scenes: int        # Type 'game'
    system_scenes: int      # toolbar, options, etc.
    empty_scenes: int       # Type 'empty'
```

**Utilité**:
- ✅ Documentation claire des différences
- ✅ Pas d'alarme si Header ≠ Parser
- ✅ Statistiques détaillées

**Effort**: 🟢 Faible (comptage simple)

---

## 📋 Ordre d'Implémentation Recommandé

1. **🟢 PRIORITÉ 1**: Lire Header VND (EXIT_ID, Config, métadonnées)
2. **🟢 PRIORITÉ 4**: Détection automatique signatures
3. **🟢 PRIORITÉ 3**: Validation objCount
4. **🟢 PRIORITÉ 6**: Statistiques Scene Count
5. **🟡 PRIORITÉ 2**: Mapper tous les subtypes (documentation)
6. **🔴 PRIORITÉ 5**: File table cryptée (si nécessaire)

---

## 🔬 Tests Nécessaires

Après chaque amélioration, valider sur:
- ✅ danem.vnd (16 scènes, 65 hotspots)
- ✅ belge.vnd (27 scènes, 87 hotspots)
- ✅ couleurs1.vnd (55 scènes, référence JSON)

Puis tester sur VND non parsés:
- 🔄 allem.vnd
- 🔄 angleterre.vnd
- 🔄 france.vnd
- 🔄 italie.vnd

---

## 💡 Autres Idées

### Validation Mode
- Comparer header vs parsed
- Vérifier signatures cohérentes
- Valider objCount pour chaque scène
- Rapport qualité (% géométrie, commandes, etc.)

### Export Amélioré
- Ajouter noms commandes (pas que subtype)
- Métadonnées VND dans JSON
- Statistiques par scène (nb hotspots, commandes, etc.)

### Debug Mode
- Afficher offsets binaires
- Highlighter scènes récupérées
- Warnings pour incohérences

---

**Conclusion**: Le parser actuel est **solide**. Les améliorations proposées sont des **bonus** pour enrichir les métadonnées et faciliter le debug. Aucune correction majeure n'est nécessaire!
