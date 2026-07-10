# Archive Files (BSA)

BSA (Bethesda Softworks Archive) files are compressed archive containers used to package game assets.

## Overview

**Extension:** `.bsa`  
**Format:** Proprietary binary archive  
**Compression:** zlib (optional per-file)

**Purpose:**
- Package multiple files into single archive
- Reduce file count (filesystem performance)
- Optional compression (save disk space)
- Load order integration with plugins

**Games:** All Bethesda games (Morrowind through Fallout 76)

## File Structure

```
BSA File
├── Header
│   ├── Magic bytes ("BSA\0")
│   ├── Version
│   ├── Flags (compressed, named directories, etc.)
│   ├── Folder count
│   ├── File count
│   └── Folder names length
├── Folder Records
│   ├── Folder hash
│   ├── File count in folder
│   └── File records offset
├── File Records
│   ├── Filename hash
│   ├── File size
│   ├── File data offset
│   └── (per file)
├── Folder Names (if enabled)
│   └── Null-terminated strings
├── File Names
│   └── Null-terminated strings
└── File Data
    ├── File 1 data (possibly compressed)
    ├── File 2 data
    └── ...
```

## BSA Versions

### Skyrim LE

**Version:** 104  
**Format:** BSA v1.04

**Features:**
- Named directories
- Per-file compression flag
- Embedded file names
- String table

### Skyrim SE

**Version:** 105  
**Format:** BA2 (not BSA!)

**File types:**
- `.ba2` - General archive (textures, meshes, etc.)
- Different format than LE BSA

**See BA2 section below.**

### Fallout 4

**Version:** 1 (BA2 format)  
**Format:** BA2 v1

**File types:**
- `*_Main.ba2` - Meshes, materials, sounds
- `*_Textures.ba2` - Textures (DDS)

**Special features:**
- Texture-specific compression
- DDS header stored separately

## BSA Flags

**Archive flags:**
- `0x001` - Include directory names
- `0x002` - Include file names
- `0x004` - Compressed by default
- `0x008` - Retain directory names
- `0x010` - Retain file names
- `0x020` - Retain file name offsets
- `0x040` - Xbox 360 archive
- `0x080` - Retain strings during startup
- `0x100` - Embedded file names

**File type flags:**
- `0x0001` - Meshes (.nif)
- `0x0002` - Textures (.dds)
- `0x0004` - Menus (.xml)
- `0x0008` - Sounds (.wav, .xwm)
- `0x0010` - Voices (.fuz)
- `0x0020` - Shaders (.hlsl)
- `0x0040` - Trees (.spt)
- `0x0080` - Fonts (.fnt)
- `0x0100` - Misc (.txt, etc.)

## Load Order

### Skyrim LE

BSAs load automatically if named to match plugin.

**Pattern:** `<PluginName>.bsa`

**Example:**
```
MyMod.esp          → Loads MyMod.bsa automatically
MyMod.bsa
```

**Explicit loading:** Add to `Skyrim.ini`:
```ini
[Archive]
sResourceArchiveList=Skyrim - Misc.bsa, Skyrim - Shaders.bsa, MyMod.bsa
```

**Load order:** BSAs load in same order as their plugin (if auto-loaded).

### Skyrim SE / Fallout 4

**BA2 format** (not BSA).

**Naming:**
- `<Plugin> - Main.ba2` - Main assets
- `<Plugin> - Textures.ba2` - Textures

**Auto-load:** Matches plugin name (without .esp/.esm).

**Example:**
```
MyMod.esp
MyMod - Main.ba2      → Auto-loads
MyMod - Textures.ba2  → Auto-loads
```

## Compression

### Per-File Compression (BSA)

**Flag per file:** Each file can be compressed or uncompressed independently.

**Compression:** zlib (deflate)

**Tradeoffs:**
- **Compressed:** Smaller file, slower load (CPU decompression)
- **Uncompressed:** Larger file, faster load

**Recommendations:**
- **Compress:** Textures, audio (large, load once)
- **Don't compress:** Frequently accessed files (loading screens, UI)

### BA2 Compression (SE/FO4)

**General archives:** Optional zlib compression per file.

**Texture archives:** Special DDS compression:
- DDS header extracted and stored separately
- Pixel data compressed
- Faster DX11 texture loading

## Creating BSA Files

### Cathedral Assets Optimizer (CAO)

**All-in-one tool** for BSA packing and asset optimization.

**Features:**
- Pack folders to BSA/BA2
- Optimize meshes (NIF)
- Optimize textures (DDS)
- Batch processing

**Workflow:**
1. Place files in folder structure
2. Open CAO
3. **BSA → Create Archive**
4. Select folder
5. Choose BSA version (Skyrim LE/SE/FO4)
6. Set compression options
7. **Run**

**Best for:** Most users, easiest workflow.

### BSArch (Command-line)

**Command-line BSA packer.**

**Usage:**
```powershell
# Pack BSA (Skyrim LE)
BSArch.exe pack "MyFolder" "MyMod.bsa" -tes5 -z

# Pack BA2 (Skyrim SE)
BSArch.exe pack "MyFolder" "MyMod - Main.ba2" -sse -z

# Pack BA2 textures (FO4)
BSArch.exe pack "TexturesFolder" "MyMod - Textures.ba2" -fo4 -tex
```

**Flags:**
- `-tes5` - Skyrim LE format
- `-sse` - Skyrim SE format
- `-fo4` - Fallout 4 format
- `-z` - Compress files
- `-tex` - Texture archive (BA2)

### Creation Kit Archive Tool

**Official tool** (ships with Creation Kit).

**Location:** `<Game>/Tools/Archive.exe`

**GUI workflow:**
1. Open Archive.exe
2. **File → New**
3. Add files/folders
4. Set compression
5. **Save As** → Choose BSA name

**Limitations:**
- Clunky UI
- Slower than CAO
- Sometimes crashes

## Extracting BSA Files

### BSA Browser

**GUI tool** for browsing/extracting BSAs.

**Features:**
- Browse BSA contents
- Extract individual files or all
- Preview files (textures, meshes)

**Workflow:**
1. Open BSA Browser
2. **File → Open Archive**
3. Browse folders
4. Right-click → Extract

### BSArch (Command-line)

**Extract via command line:**

```powershell
# Extract entire BSA
BSArch.exe unpack "MyMod.bsa" "OutputFolder"

# Extract specific file
BSArch.exe extract "MyMod.bsa" "meshes\actors\character\character.nif" "output.nif"
```

### Cathedral Assets Optimizer

**Bulk extraction:**
1. Open CAO
2. **BSA → Extract Archive**
3. Select BSA/BA2
4. Choose output folder
5. **Run**

### 7-Zip / WinRAR (Skyrim LE only)

**7-Zip** can open LE BSA files directly (but not BA2).

**Workflow:**
- Right-click BSA → 7-Zip → Open Archive
- Extract like any archive

**Limitation:** LE BSAs only, not SE/FO4 BA2.

## BSA vs. Loose Files

**BSA advantages:**
- Fewer files (better filesystem performance)
- Automatic load order
- Compressed (smaller install size)
- Easier distribution (single file vs. thousands)

**Loose files advantages:**
- Overwrite BSA contents (higher priority)
- Easier editing (no unpack/repack)
- No extraction step for testing

**Best practice:**
- **Release mods:** Use BSA (easier for users)
- **Development:** Use loose files (faster iteration)

### Load Order Priority

**Priority (highest to lowest):**
1. Loose files in Data/
2. BSAs (in plugin load order, last wins)

**Example:**
```
Data/meshes/myfile.nif       ← Highest priority (loose file)
MyModB.bsa::meshes/myfile.nif  ← (loads after MyModA)
MyModA.bsa::meshes/myfile.nif  ← Lowest priority
```

**Use case:** Override BSA files without repacking - place loose file in Data/.

## Common Issues

### BSA Not Loading
- **Wrong name:** BSA name doesn't match plugin
- **Plugin not active:** Plugin disabled in load order
- **Not in Data/:** BSA not in correct location
- **Fix:** Rename BSA to match plugin, enable plugin, move to Data/

### Files Not Overriding
- **BSA priority:** Another BSA or loose file loading later
- **Plugin load order:** Plugin loading earlier than expected
- **Fix:** Check load order, use loose files to force override

### BSA Corrupt/Won't Open
- **Incomplete download:** Re-download mod
- **Wrong tool version:** Use updated BSArch/CAO
- **Wrong BSA version:** LE tool on SE BA2 (or vice versa)
- **Fix:** Re-download, use correct tool, verify BSA version

### Compressed Files Slow Loading
- **Over-compression:** Everything compressed unnecessarily
- **Hardware limitation:** Slow CPU bottleneck on decompression
- **Fix:** Repack with selective compression (don't compress frequently loaded files)

## BA2 Format (SE/FO4)

### Differences from BSA

**Structure:**
- Different header
- Separate texture format
- Chunk-based storage

**Types:**

#### GNRL (General Archive)

**Contains:** Meshes, materials, sounds, scripts, misc.

**Compression:** Optional zlib per chunk.

**File path:** `<Plugin> - Main.ba2`

#### DX10 (Texture Archive)

**Contains:** DDS textures only.

**Compression:** DDS pixel data compressed, header separate.

**Optimization:** Faster loading than BSA textures.

**File path:** `<Plugin> - Textures.ba2`

### Creating BA2

**Use BSArch or CAO** (same tools as BSA).

**Separate textures:**

**Option 1 - Automatic:** CAO detects DDS files and creates two BA2s.

**Option 2 - Manual:**
```powershell
# Main archive (no textures)
BSArch.exe pack "MainFolder" "MyMod - Main.ba2" -sse -z

# Texture archive (only DDS)
BSArch.exe pack "TexturesFolder" "MyMod - Textures.ba2" -sse -tex
```

**Folder structure:**
```
MyMod - Main.ba2
  ├─ meshes\
  ├─ materials\
  ├─ sounds\
  └─ scripts\

MyMod - Textures.ba2
  └─ textures\
```

### BA2 Load Order

**Same as BSA:** Automatic if named after plugin.

**Priority:**
1. Loose files
2. BA2s (plugin load order)

## Performance Tips

**Compress large files:** Textures, audio (infrequently loaded).

**Don't compress small files:** UI, scripts (frequently accessed).

`[FO4]` `[SSE]` **Split textures to separate BA2:** Faster DDS loading.

**Don't over-pack:** Very large BSAs (>2GB) can cause issues.

`[FO4]` `[SSE]` **Use BA2 instead of BSA:** Better performance than BSA format.

## Tools Summary

**Cathedral Assets Optimizer (CAO):** Best all-around tool (GUI).

**BSArch:** Best command-line tool (scripting, automation).

**BSA Browser:** Best extraction/preview tool.

**Archive.exe (CK):** Official tool (clunky, use CAO instead).

## See Also

- [Plugin Files](plugins.md) - BSA load order with plugins
- [Deployment Guide](../../DEPLOYMENT.md) - Packaging mods for release
- [Performance Tips](../../workflows/optimization.md) - BSA compression strategies
