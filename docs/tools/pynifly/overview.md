# PyNifly Overview

PyNifly is a Blender addon that provides import and export functionality for NIF (NetImmerse Format) and HKX (Havok) files used in Bethesda games. It's the primary tool for working with 3D meshes and animations for Skyrim and Fallout 4 modding.

## What PyNifly Does

**Mesh Import/Export:**
- Import NIF files into Blender for editing
- Export modified meshes back to NIF format
- Handles complex features: skinning, shaders, partitions, segments, collisions
- Preserves game-specific data structures

**Animation Support:**
- Direct import/export of HKX animations (no hkxcmd needed)
- Skeleton import from HKX files
- NIF-embedded animations (transform controllers)
- Annotation markers

**Morph/Shape Key Handling:**
- TRI file import/export (facial expressions, chargen morphs)
- BodySlide morph support
- Multi-weight exports (_0 and _1 files in one operation)

**Special Features:**
- FO4 connect points (weapon attachments, armor parts)
- FO4 segments and subsegments
- Skyrim partitions (SBP_* system)
- Collision shapes (bhkCollisionObject, bhkPhysicsSystem)
- Shader property setup

## Supported Games

| Game | Version | Notes |
|------|---------|-------|
| **Skyrim LE** | 32-bit | NiTriShape, hk_2010.2.0-r1 |
| **Skyrim SE** | 64-bit | BSTriShape, BSDynamicTriShape, hk_2010.2.0-r1 |
| **Fallout 4** | 64-bit | BSTriShape, segments, BGSM materials, hk_2014.1.0-r1 |
| Fallout 76 | 64-bit | Limited support |
| Fallout 3/NV | 32-bit | Limited support |

**Note:** This library focuses on **Skyrim LE, Skyrim SE, and Fallout 4**. FO76/FO3/FONV support exists but is not extensively documented here.

## How It Works

PyNifly uses Bodyslide/Outfit Studio's **nifly** library as its core technology. This means it shares the same robust NIF parsing and writing code that OS uses, ensuring compatibility and reliability.

### Architecture Layers

```
┌─────────────────────────────────────┐
│   Blender UI (addon interface)     │
├─────────────────────────────────────┤
│   PyNifly Python (io_scene_nifly)  │  ← Blender integration
├─────────────────────────────────────┤
│   pyn (Python wrapper)              │  ← Python API layer
├─────────────────────────────────────┤
│   NiflyDLL (C++ wrapper)            │  ← DLL interface
├─────────────────────────────────────┤
│   nifly library                     │  ← Core NIF parsing (from Outfit Studio)
└─────────────────────────────────────┘
```

You can use PyNifly at different levels:
- **Blender addon** - Import/export through Blender's File menu
- **Python API** - Direct scripting with `from pyn import pynifly`
- **Standalone scripts** - Process NIFs without Blender UI

## Key Features in Detail

### Import-and-Forget Design

PyNifly preserves game-specific metadata during import, so you can:
1. Import a NIF
2. Edit the mesh in Blender
3. Export back to NIF
4. Get correct results without manual setup

No need to remember obscure flags or manually set shader properties — PyNifly remembers them for you.

### Handles Complex Meshes

**Skinning (rigging):**
- Up to 4 bone weights per vertex
- Automatic skin partition creation
- Unweighted vertex detection

**Partitions/Segments:**
- Skyrim: SBP_30_HEAD, SBP_32_BODY, etc. (via vertex groups)
- FO4: Material:Subsegment system with SSF files

**Shaders:**
- BSLightingShaderProperty (Skyrim)
- BSEffectShaderProperty
- BGSM/BGEM material files (FO4)
- Automatic Blender material node setup

### Multi-Weight Export (Skyrim)

Export _0 and _1 files in one operation:
- Create shape keys named `_0` and `_1` in Blender
- Export once
- PyNifly generates both `armor_0.nif` and `armor_1.nif`

### Expression and Chargen Morphs

**Skyrim/FO4 TRI files:**
- Expressions: Aah, BMP, ChimpA, etc.
- Chargen: Face customization sliders
- Auto-find: `mesh.tri` and `mesh_chargen.tri`

**BodySlide TRI format:**
- Shape keys prefixed with `>` export as BodySlide morphs
- BODYTRI extra data references

### FO4-Specific Features

**Connect Points:**
- Weapon attachment points
- Armor attach points
- Workshop snap points
- Editor markers

**Segments/Subsegments:**
- Replaces Skyrim's partition system
- Material:Subsegment naming (e.g., "Metal:Torso")
- SSF files define segment structure

**FaceBones:**
- Dual armature system
- `_facebones.nif` for facial animation
- Skin bone parenting (`_skin` suffix)

### Collision Support

**Import:**
- Represents collision shapes as Blender meshes
- Rigid body physics setup
- Collision layer assignment

**Export:**
- bhkCollisionObject (Skyrim)
- bhkNPCollisionObject/bhkPhysicsSystem (FO4)

**Limitations:**
- MOPP (optimized collision) not yet supported
- FO4 Elric compiler required for some features

### Animation Workflow

**HKX Import:**
1. Import skeleton: `skeleton.hkx` → Blender armature
2. Import animation: `idle.hkx` → Blender action
3. Bones, keyframes, and annotations all imported

**HKX Export:**
1. Create animation in Blender
2. Export action to HKX
3. No hkxcmd dependency — PyNifly has native HKX support

**NIF-embedded animations:**
- Open/close animations (chests, doors)
- Transform controllers (position, rotation, scale)
- Shader property animations (emissive, alpha)

## Common Workflows

### Editing Existing Armor

```
1. Import armor NIF
2. Edit mesh in Blender
3. Export (same settings as import)
4. Test in-game
```

### Creating Custom Race

```
1. Import vanilla head NIF + TRI files
2. Sculpt new face shape
3. Adjust expressions (shape keys)
4. Export head NIF + TRI files
5. Create RACE record referencing new meshes
```

### Adding Animations

```
1. Import skeleton.hkx
2. Import reference animation.hkx (for timing)
3. Animate in Blender
4. Export new animation.hkx
5. Test with FNIS/Nemesis
```

## Advantages Over Other Tools

**vs. NifTools Blender Plugin:**
- Native FO4 support (NifTools has none)
- Modern Blender versions (4.4+)
- Active development
- HKX animation support without external tools

**vs. Outfit Studio:**
- Full Blender modeling tools
- Non-destructive workflow
- Better UV editing
- Advanced sculpting

**vs. Manual NifSkope editing:**
- Visual editing
- Batch operations via Python
- Less error-prone
- Faster iteration

## Limitations

**Windows only** - nifly DLL requires Windows

**Blender 4.4+** - Older Blender versions not supported

**Some FO4 features incomplete:**
- MOPP collision shapes (read-only)
- bhkRigidBody property encoding (nifly uses Skyrim layout)

**No Starfield support** - Starfield uses different formats

## When NOT to Use PyNifly

**For plugin (ESP/ESM) editing** → Use xEdit or Creation Kit

**For script compilation** → Use Papyrus compiler

**For BSA creation** → Use BSA packer tools

**For texture editing** → Use GIMP/Photoshop + DDS plugins

PyNifly is specifically for **mesh and animation files**. Other modding tasks require different tools.

## Next Steps

- **[Installation](installation.md)** - Set up PyNifly in Blender
- **[Importing](importing.md) [TBD]** - Bring NIFs into Blender
- **[Exporting](exporting.md) [TBD]** - Write modified meshes back to NIF
- **[Python API](python-api.md) [TBD]** - Script PyNifly operations
- **[Example Scripts](example-scripts.md) [TBD]** - Common automation tasks

## External Resources

- [PyNifly GitHub](https://github.com/BadDogSkyrim/PyNifly)
- [PyNifly Wiki](https://github.com/BadDogSkyrim/PyNifly/wiki)
- [Outfit Studio](https://github.com/ousnius/BodySlide-and-Outfit-Studio)
- [nifly library](https://github.com/ousnius/nifly)

## Credits

**Core Technology:**
- Ousnius - nifly library that powers PyNifly

**Critical NIF/HKX Encoding Information:**
- Candoran2, DagobaKing, Nikolivanov, Nitaigao, PredatorCZ

**Tool Contributors:**
- bitbanger, jgernandt, Reddraconi, ShroomTip, ZenithVal

---

**Ready to get started?** Head to [Installation](installation.md) to set up PyNifly in Blender.
