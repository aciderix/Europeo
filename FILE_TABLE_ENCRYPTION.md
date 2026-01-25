# File Table Encryption - VnStudio Engine

**Source**: `Infos/Code_Reconstruit_V2/_common_functions.cpp.txt` (sub_405557, ligne 2187)
**Applicable**: Versions >= 0x2000D

## Contexte

Les fichiers VND avec version >= 0x2000D ont la **première string** de leur file table cryptée avec la clé `"Password"`.

### Versions VND Connues

| Version Hex | Version Dec | Nom | File Table Cryptée |
|-------------|-------------|-----|-------------------|
| 0x20000 | 131072 | 2.0 | ❌ Non |
| 0x2000A | 131082 | 2.10 | ❌ Non |
| 0x2000B | 131083 | 2.11 | ❌ Non |
| 0x2000D | 131085 | 2.13 | ✅ **OUI** |

**Note**: La version "2.13" dans nos fichiers de test pourrait correspondre à 0x2000D, mais nos VND ne semblent pas avoir de file table cryptée.

## Algorithme de Décryptage (sub_405557)

### Pseudo-Code Source

```cpp
int __cdecl sub_405557(int a1, unsigned int a2, string *a3)
{
  __int16 v3;     // Hash de la clé
  unsigned int i;
  __int16 v6;     // Buffer pour extraction hex
  void *s;        // Buffer décrypté
  unsigned int v8; // Taille du string

  // 1. Convertir clé en uppercase
  to_upper((const string *)v13);

  // 2. Calculer hash de la clé
  v3 = string::hash((string *)v13);

  // 3. Allouer buffer de sortie
  v8 = *(_DWORD *)(*(_DWORD *)a2 + 6) >> 1; // length / 2
  s = (void *)operator new[](v8 + 1);
  memset(s, 0, v8 + 1);

  // 4. Décrypter par blocs de 4 chars hex
  for (i = 0; i < v8; i += 2)
  {
    // Extraire 4 chars hex (ex: "4A3F")
    string::substr((string *)&v12, a2, 2 * i);
    sscanf(*(const char **)(v12 + 2), "%4hX", &v6);

    // Décrypter: soustraire hash
    *(_WORD *)((char *)s + i) = v6 - v3;

    // Inverser signe du hash pour prochaine itération
    v3 = -v3;
  }

  // 5. Retourner string décrypté
  string::assign(a3, (const string *)v11, 0, 0xFFFFFFFF);
  return *(_DWORD *)(*(_DWORD *)a3 + 6);
}
```

### Algorithme Détaillé

1. **Uppercase Clé**: `"Password"` → `"PASSWORD"`
2. **Hash**: Calculer `hash("PASSWORD")` → `h` (int16)
3. **Boucle Décryptage**:
   - Pour chaque paire d'octets du string crypté (format hex):
     - Extraire 4 chars hex → valeur `v` (ex: `"4A3F"` → `0x4A3F`)
     - Décrypter: `decrypted_word = v - h`
     - Stocker comme 2 bytes dans buffer de sortie
     - Inverser hash: `h = -h`
4. **Retour**: Buffer décrypté comme string

### Fonction Hash

**Non documentée** dans le pseudo-code disponible. Probablement:
- CRC16 ou checksum custom sur le string uppercase
- Utilisé pour XOR/ADD sur chaque mot de 16 bits

## Implémentation Python (Hypothétique)

```python
def decrypt_filetable_string(encrypted_hex: str, key: str = "Password") -> str:
    """
    Décrypte un string de file table VND (version >= 0x2000D)

    Args:
        encrypted_hex: String crypté en format hex (ex: "4A3F5B2C...")
        key: Clé de décryptage (default: "Password")

    Returns:
        String décrypté
    """
    # 1. Hash de la clé uppercase
    key_upper = key.upper()
    hash_val = string_hash_vnstudio(key_upper)  # Fonction hash custom

    # 2. Décrypter par blocs de 4 chars hex
    result = bytearray()
    for i in range(0, len(encrypted_hex), 4):
        # Extraire 4 chars hex
        hex_block = encrypted_hex[i:i+4]
        encrypted_word = int(hex_block, 16)

        # Décrypter: soustraire hash (avec wrap-around 16-bit)
        decrypted_word = (encrypted_word - hash_val) & 0xFFFF

        # Stocker comme 2 bytes (little endian)
        result.append(decrypted_word & 0xFF)
        result.append((decrypted_word >> 8) & 0xFF)

        # Inverser hash pour prochaine itération
        hash_val = -hash_val

    # 3. Convertir en string (Windows-1252)
    return result.decode('cp1252', errors='replace')


def string_hash_vnstudio(s: str) -> int:
    """
    Hash custom VnStudio (fonction exacte à reverse engineer)

    Hypothèses:
    - CRC16 ou checksum additive
    - Retourne int16 signé (-32768 à 32767)
    """
    # PLACEHOLDER - fonction exacte non documentée
    # Besoin de reverse engineering sur europeo.exe
    hash_val = 0
    for char in s:
        hash_val = ((hash_val << 5) - hash_val + ord(char)) & 0xFFFF

    # Convertir en int16 signé
    if hash_val >= 0x8000:
        hash_val -= 0x10000

    return hash_val
```

## Format File Table (Version >= 0x2000D)

```
Offset | Type   | Description
-------|--------|-------------
0      | String | String crypté (décrypté avec "Password" → offset +4 structure)
+X     | String | String 2 en clair (offset +8 structure)
+Y     | String | String 3 en clair (offset +12 structure)
```

**Stockage structure**:
- Offset +4: String décrypté (premier string)
- Offset +8: String 2 (clair)
- Offset +12: String 3 (clair)

## Détection Version Cryptée

### Dans le Header VND

```python
def is_encrypted_filetable(version_string: str) -> bool:
    """
    Détermine si la file table est cryptée basé sur la version

    Version >= 0x2000D (131085 décimal, "2.13" ?)
    """
    # Tentative parse version
    if "2.13" in version_string or "2.14" in version_string:
        return True  # Version >= 2.13 probablement cryptée

    return False
```

## Limitations Actuelles

1. **Fonction Hash Non Documentée**
   - Le pseudo-code ne révèle pas l'implémentation de `string::hash()`
   - Reverse engineering de `europeo.exe` nécessaire
   - Alternative: Bruteforce avec fichiers test

2. **Pas de Fichier Test Crypté**
   - Tous nos VND (danem, belge, couleurs1) sont version 2.13
   - Mais leurs file tables ne semblent pas cryptées
   - Besoin de VND avec version confirmée >= 0x2000D

3. **Format Hex Non Validé**
   - Le string crypté est supposé en format hex ("4A3F5B2C...")
   - Pas de confirmation empirique sur fichiers réels

## Prochaines Étapes P6

1. **Reverse Engineer Hash Function**
   - Analyser `europeo.exe` avec IDA/Ghidra
   - Localiser `string::hash()` implementation
   - Valider avec cas de test connus

2. **Trouver Fichier VND Crypté**
   - Tester VND restants (allem, angleterre, france, italie)
   - Chercher version >= 0x2000D
   - Valider décryptage sur données réelles

3. **Implémenter dans Parser**
   - Ajouter `decryptFileTableString()` à vnd_parser.py
   - Détecter version cryptée dans `parseSceneBlock()`
   - Décrypter avant parsing file table

## Références

- **Pseudo-Code**: `_common_functions.cpp.txt` lignes 2187-2227 (sub_405557)
- **File Table Parser**: `_common_functions.cpp.txt` lignes 9676-9695 (sub_416781)
- **Clé**: `"Password"` (hardcodée ligne 9690: `aPassword`)

## Statut Implémentation

- ❌ **Non Implémenté** - Fonction hash manquante
- ❌ **Non Testé** - Pas de fichier VND crypté disponible
- ✅ **Documenté** - Algorithme et structure compris
- 🔄 **En Attente** - Reverse engineering hash + fichier test
