# File Formats Overview

This section covers the core binary file formats used in Bethesda games (Skyrim and Fallout 4).

## File Types Covered

### Plugin Files
**[ESP/ESM/ESL](plugins.md)** - Game data and modifications
- Plugin types
- FormIDs and masters
- Compression and string tables

### 3D Assets
**[NIF Files](nif-files.md)** - Meshes, materials, and geometry
- Shapes and skinning
- Shaders and partitions
- Game-specific differences

**[HKX Files](animations.md)** - Havok animations and skeletons
- HKX skeletons and animations
- Compressed animations
- Annotation markers

**[TRI Files](morphs-shapekeys.md)** - Morph data
- Facial expressions
- Character customization sliders
- BodySlide morphs

### Visual Assets
**[DDS Files](textures-materials.md)** - Textures
- Compression formats
- Mipmaps and normal maps

**[BGSM/BGEM](textures-materials.md)** - Fallout 4 materials
- Texture references
- Material properties

### Physics
**[HDT-SMP XML](physics-collision.md)** - Skinned mesh physics
- Collision shapes
- Bone constraints
- VirtualGround setup

**[Havok Collision](physics-collision.md)** - Rigid body physics
- Collision shapes
- Body properties

### Archives & Scripts
**[BSA Files](archives.md)** - Archive format
- Compression and directory structure

**[PEX Files](scripts.md)** - Compiled Papyrus scripts
- VMAD records

## Key Concepts

### Game Differences
- **Skyrim LE** - 32-bit pointers, NiTriShape, hk_2010.2.0-r1
- **Skyrim SE** - 64-bit pointers, BSTriShape, hk_2010.2.0-r1
- **Fallout 4** - 64-bit pointers, BSTriShape, segments, BGSM, hk_2014.1.0-r1
- **Starfield** - Creation Engine 2; geometry-less NIF (`BSGeometry` → external `.mesh`), layered `.mat` materials, component-based plugins, in-house animation. See the dedicated **[Starfield](../game-specific/starfield/overview.md)** section — its formats differ enough to stand apart from the pages above.

### File Relationships
```
Plugin (ESP)
  ├─> References NIF meshes
  │     ├─> Contains material/shader data
  │     ├─> References DDS textures (Skyrim)
  │     ├─> References BGSM/BGEM (FO4)
  │     ├─> May include collision (bhk*)
  │     └─> May reference TRI morphs
  ├─> References HKX animations
  │     └─> Requires matching skeleton
  └─> May reference PEX scripts (VMAD)
```

### Data Flow
1. **Plugin** defines what exists in the game world
2. **NIF** provides 3D geometry and appearance
3. **HKX** provides motion and bone structure
4. **TRI** provides shape variations
5. **DDS/BGSM** provides surface appearance
6. **XML/Physics** provides dynamic behavior

## Navigation

Each format has its own detailed page with:
- Binary structure specifications
- Parsing rules and constraints
- Game-specific differences
- Common issues and solutions
- Code examples (PyNifly, esplib)

Ready to dive in? Pick a format from the sidebar!
