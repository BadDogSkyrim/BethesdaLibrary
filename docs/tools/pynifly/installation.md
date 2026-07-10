# PyNifly Installation

This guide covers installing PyNifly in Blender for Bethesda modding (Skyrim and Fallout 4).

## Prerequisites

### System Requirements

- **Windows** - PyNifly uses a Windows-only DLL (nifly library wrapper)
- **Blender 4.4 or later** - Download from [blender.org](https://www.blender.org/download/)
- **50 MB free disk space** - For addon and test files

**Note:** PyNifly does NOT work on:
- macOS or Linux (nifly DLL is Windows-only)
- Blender versions before 4.4
- Blender installed from Microsoft Store (use standalone installer)

### Recommended Setup

- **8 GB RAM minimum** - 16 GB recommended for complex meshes
- **Dedicated GPU** - For smooth Blender viewport performance
- **SSD storage** - Faster file operations

## Installation Steps

### 1. Download PyNifly

**Option A: Latest Release (Stable)**

1. Go to [PyNifly Releases](https://github.com/BadDogSkyrim/PyNifly/releases)
2. Download `io_scene_nifly-X.X.X.zip` (e.g., `io_scene_nifly-25.9.0.zip`)
3. **Do NOT unzip** - Blender installs from the zip file directly

**Option B: Development Version (Latest Features)**

1. Go to [PyNifly GitHub](https://github.com/BadDogSkyrim/PyNifly)
2. Click "Code" → "Download ZIP"
3. Extract the zip
4. Find `io_scene_nifly/` folder
5. Zip ONLY the `io_scene_nifly/` folder (create `io_scene_nifly.zip`)

### 2. Install in Blender

1. **Open Blender**
2. Go to **Edit** → **Preferences**
3. Click **Add-ons** tab
4. Click **Install...** button (top right)
5. Navigate to your downloaded `io_scene_nifly-X.X.X.zip`
6. Click **Install Add-on**
7. **Enable the addon:**
   - Search for "nifly" or "pynifly" in the addon list
   - Check the checkbox next to "Import-Export: Nif File format (Pynifly)"

You should now see:
```
☑ Import-Export: Nif File format (Pynifly)
```

### 3. Verify Installation

**Check import/export menus:**

1. Go to **File** → **Import**
   - You should see: "Nif File (.nif)", "HKX Animation", "Tri File (.tri)"

2. Go to **File** → **Export**
   - You should see: "Nif File (.nif)", "HKX Animation", "Skeleton HKX"

If you see these options, PyNifly is installed correctly! ✅

### 4. Configure Preferences (Optional but Recommended)

In **Edit** → **Preferences** → **Add-ons** → **PyNifly**, click the ▼ arrow to expand settings:

**Bone Naming:**
- ☑ **Blender-friendly bone names** (recommended)
  - Converts "NPC L Hand [LHnd]" → "NPC Hand.L [LHnd]"
  - Enables Blender's symmetry tools
- ☐ **NifTools-friendly bone names** (only if using NifTools compatibility mode)

**Import Defaults:**
- ☑ **Import tri files when found** - Auto-loads expression morphs
- ☑ **Import as shape keys** - Merges similar meshes when importing multiple files
- ☐ **Blender-friendly scene orientation** - Rotates scene 90° (personal preference)

**Texture Paths:**
Set these so materials display correctly in Blender's viewport.

**Skyrim Texture Paths 1–4:**
```
C:\Steam\steamapps\common\Skyrim Special Edition\Data\textures
C:\ModOrganizer\mods\YourMod\textures
```

**Fallout Texture Paths 1–4:**
```
C:\Steam\steamapps\common\Fallout 4\Data\textures
C:\ModOrganizer\mods\YourMod\textures
```

These paths tell Blender where to find DDS textures so imported meshes display with proper materials.

## Upgrading PyNifly

**Important:** Always close Blender completely before upgrading!

### Method 1: Remove and Reinstall (Recommended)

1. **Close Blender** (important!)
2. Open Blender
3. **Edit** → **Preferences** → **Add-ons**
4. Find PyNifly, click **Remove**
5. Restart Blender
6. Follow installation steps above with new version

### Method 2: Overwrite Install

1. **Close Blender completely**
2. Open Blender
3. **Edit** → **Preferences** → **Add-ons** → **Install...**
4. Select new `io_scene_nifly-X.X.X.zip`
5. Click **Install Add-on** (overwrites old version)
6. Restart Blender

**Why close Blender first?** Windows locks DLL files when they're loaded. If Blender is running, the nifly DLL can't be replaced, causing upgrade failures or crashes.

## Troubleshooting

### "PyNifly not in import menu"

**Solution:**
1. Check that addon is **enabled** (checkbox checked)
2. Restart Blender
3. Try re-installing from zip file

### "DLL load failed" or "Module not found"

**Causes:**
- Blender installed from Microsoft Store (unsupported)
- Missing Visual C++ Redistributables
- Corrupted download

**Solutions:**
1. Uninstall Blender from Microsoft Store
2. Download standalone Blender from [blender.org](https://www.blender.org)
3. Install [Visual C++ Redistributables](https://aka.ms/vs/17/release/vc_redist.x64.exe)
4. Re-download PyNifly zip (may have been corrupted)

### "Import fails silently"

**Check the console for errors:**

**Windows:** Go to **Window** → **Toggle System Console**

This opens a console window showing Python errors. Error messages help diagnose issues:
- DLL errors
- Missing files
- Corrupted NIF data

### "Meshes import without textures"

**Solution:** Set texture paths in addon preferences (see Configuration above).

Blender needs to know where your game's texture files are. Without these paths, meshes import correctly but display as gray.

### "Can't export - target game not detected"

**Solution:** Manually select target game in export dialog.

When exporting meshes created from scratch (not imported), PyNifly can't auto-detect the game. Set **Target game** in the export file browser sidebar.

### "Blender crashes on import"

**Causes:**
- Corrupted NIF file
- Insufficient RAM
- Extremely complex mesh

**Solutions:**
1. Try importing in a new Blender file (rule out project-specific issues)
2. Check NIF in NifSkope first (verify it's not corrupted)
3. Close other programs (free up RAM)
4. If consistent, report as bug with sample file

## Testing Your Installation

### Quick Test: Import Vanilla Asset

1. Extract a NIF from your game (e.g., Skyrim's `meshes/armor/iron/ironarmor_0.nif`)
2. **File** → **Import** → **Nif File (.nif)**
3. Navigate to the NIF and import
4. You should see the armor mesh in Blender

If this works, PyNifly is fully functional!

### Test Export

1. Select the imported mesh
2. **File** → **Export** → **Nif File (.nif)**
3. Save as `test_export.nif`
4. Open in NifSkope to verify

## Logging and Debugging

### Enable Console Output

**Windows:** **Window** → **Toggle System Console**

The console shows:
- Import/export progress
- Warnings (unweighted vertices, missing partitions)
- Errors (DLL failures, corrupted data)
- Python tracebacks

### Common Warnings (Non-Fatal)

These warnings indicate potential issues but don't stop the operation:

```
WARNING: Mesh has unweighted vertices
→ Some vertices not assigned to bones (will be fixed on export)

WARNING: Multiple partitions found
→ Mesh has conflicting partition assignments

WARNING: Could not find texture: path/to/texture.dds
→ Texture file not in configured paths (mesh still imports)
```

### Common Errors (Fatal)

These errors stop the import/export:

```
ERROR: DLL load failed
→ nifly DLL not found or incompatible (reinstall addon)

ERROR: Failed to parse NIF file
→ Corrupted or unsupported NIF format

ERROR: No valid meshes selected for export
→ No Blender meshes selected before export
```

## Advanced: Standalone Python Usage

PyNifly can be used outside Blender for batch processing or analysis.

### Setup

```python
import sys
# Point to PyNifly's io_scene_nifly directory
sys.path.insert(0, 'C:/Blender/4.4/scripts/addons/io_scene_nifly')

from pyn import pynifly

# Now you can use PyNifly without Blender UI
nif = pynifly.NifFile('path/to/mesh.nif')
print(f"Shapes: {[s.name for s in nif.shapes]}")
```

**Use cases:**
- Batch rename textures
- Extract vertex counts from many NIFs
- Automate collision checks
- Generate mesh reports

See [Python API](python-api.md) [TBD] for details.

## Next Steps

Now that PyNifly is installed:

- **[Importing](importing.md) [TBD]** - Learn import options and workflows
- **[Exporting](exporting.md) [TBD]** - Export settings and best practices
- **[Workflows](../../workflows/meshes-modeling.md) [TBD]** - Common modeling tasks

## Getting Help

**Bug Reports:**
- [PyNifly Issues](https://github.com/BadDogSkyrim/PyNifly/issues)

**Questions:**
- [PyNifly Wiki](https://github.com/BadDogSkyrim/PyNifly/wiki)
- Skyrim/Fallout modding Discord servers
- Nexus Mods forums

**Include when reporting issues:**
- Blender version
- PyNifly version
- Operating system
- Console output (from Toggle System Console)
- Sample NIF file (if possible)

---

**Installation complete?** Head to [Importing](importing.md) [TBD] to start working with NIF files!
