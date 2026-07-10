# Bethesda Modding Library - Structure Plan

## Overview

**This is a multi-file documentation structure.** Each section will be its own markdown file, with relative links connecting them (e.g., `[NIF Format](file-formats/nif-files.md)`). This allows both human navigation and AI context loading of specific topics.

This document outlines the proposed structure for consolidating Bethesda modding knowledge from multiple projects (xEditDev, PyNifly) into a unified reference library.

**Source Locations:**
- `C:\Modding\xEditDev` - Plugin/ESP development, esplib toolkit
- `C:\Modding\PyNifly` - NIF mesh/animation toolkit, Blender addon
- https://github.com/BadDogSkyrim/PyNifly/wiki - PyNifly documentation
- User memory notes - Skyrim debugging experiences

**Goals:**
- Single authoritative reference for Bethesda file formats
- Consolidate scattered knowledge and debugging notes
- Practical examples and code snippets
- Game-specific differences clearly documented
- Easy to navigate and search
- Machine-readable for AI consumption (schemas, decision trees, validators)

**Scope:**
- **Games Covered:** Skyrim LE, Skyrim SE, Fallout 4
- **Games Explicitly Excluded:** Starfield, Fallout 76, Fallout 3, Fallout New Vegas
  - (May add FO76/FO3/FONV in future if content becomes available)
- **File Types:** ESP/ESM, NIF, HKX, TRI, DDS, BGSM/BGEM, HDT XML, BSA, PEX
- **Tools:** PyNifly (primary), esplib (primary), xEdit (reference), Creation Kit (reference)

**Organization Principles:**
- **Format vs Tool:** File format specifications are tool-agnostic. Tool-specific conventions (PyNifly shape key prefixes, esplib schema syntax) are clearly marked as such.
- **Universal vs Game-Specific:** Information applicable to all games goes in "File Formats" section. Game differences go in "Game-Specific Information."
- **Blender-Agnostic Explanations:** When discussing Blender workflows, explain concepts in game terms first (e.g., "bone weights" before "vertex groups," "skeleton" before "armature")

**File Structure:**
```
Bethesda Library/
├── README.md                           # Index with links to all sections
├── file-formats/
│   ├── plugins.md                      # ESP/ESM/ESL format
│   ├── nif-files.md                    # NIF mesh format
│   ├── animations.md                   # HKX format
│   ├── physics-collision.md            # Havok physics, HDT-SMP
│   ├── morphs-shapekeys.md             # TRI files
│   ├── textures-materials.md           # DDS, BGSM/BGEM
│   ├── archives.md                     # BSA format
│   └── scripts.md                      # PEX format
├── game-specific/
│   ├── skyrim-le.md
│   ├── skyrim-se.md
│   ├── fallout4/                       # FO4 needs subdirectory - significant unique content
│   │   ├── overview.md                 # Core differences from Skyrim
│   │   ├── connect-points.md           # Weapon/armor attachment system
│   │   ├── workshop-system.md          # Settlement building objects
│   │   ├── facebones.md                # Facial animation system
│   │   └── material-system.md          # BGSM/BGEM details
├── tools/
│   ├── pynifly/
│   │   ├── overview.md
│   │   ├── installation.md
│   │   ├── importing.md
│   │   ├── exporting.md
│   │   ├── animations.md
│   │   ├── python-api.md
│   │   └── example-scripts.md
│   ├── esplib/
│   │   ├── overview.md
│   │   ├── schema-system.md
│   │   ├── record-definitions.md
│   │   ├── usage-patterns.md
│   │   └── cli-tools.md
│   ├── xedit-reference.md              # Brief reference only (no Pascal)
│   └── other-tools.md                  # NifSkope, etc. (brief reference)
├── workflows/                           # Common Tasks & Workflows
│   ├── character-creation.md
│   ├── armor-clothing.md
│   ├── meshes-modeling.md
│   ├── animations.md
│   ├── physics-collisions.md
│   └── textures-materials.md
├── debugging/
│   ├── ctd-crashes.md
│   ├── mesh-issues.md
│   ├── animation-issues.md
│   ├── physics-issues.md
│   └── plugin-issues.md
├── reference/
│   ├── record-types.md
│   ├── bone-names.md
│   ├── shader-flags.md
│   ├── partition-names.md
│   └── expression-morphs.md
└── ai-reference/                        # AI-specific structured data
    ├── glossary.md                      # Precise terminology
    ├── validation-rules.md              # Constraints and rules
    ├── decision-trees.md                # When to use X vs Y
    ├── code-templates.md                # Complete working examples
    ├── state-machines.md                # Multi-step workflows
    ├── file-path-conventions.md         # Where files go
    └── default-values.md                # Standard defaults
```

**Cross-Reference Convention:**
- Use relative markdown links: `[link text](../category/file.md)`
- For specific sections: `[link text](../category/file.md#section-heading)`
- For AI consumers: Each file should be self-contained enough to load independently, with links to dependencies

---

## Proposed Top-Level Structure

Below is the detailed content outline for each file. The file paths correspond to the directory structure shown above.

---

### 1. File Formats (`file-formats/`)

Core documentation on Bethesda game file formats - binary structures, parsing rules, and encoding details.

#### 1.1 Plugins (`file-formats/plugins.md`)
- **Overview** - Plugin types, load order, form IDs
- **File Structure** - Headers, groups, records, subrecords
- **Compression** - Compressed records (flag 0x00040000, zlib)
- **String Tables** - STRINGS/DLSTRINGS/ILSTRINGS for localized plugins
- **XXXX Overflow** - Handling subrecords > 65535 bytes
- **Record Definitions** - By game (Skyrim, FO4, etc.)
  - Common records (NPC_, RACE, ARMO, ARMA, WEAP, etc.)
  - Game-specific records
- **Master Resolution** - How overrides and conflicts work
- **FormID Structure** - Plugin index + local ID

#### 1.2 NIF Files (`file-formats/nif-files.md`)
- **Overview** - NetImmerse/Gamebryo format, game differences
- **File Structure** - Blocks, node tree, shapes
- **Shapes & Geometry**
  - BSTriShape (Skyrim SE, FO4) - primary mesh container
  - NiTriShape (Skyrim LE) - legacy mesh container
  - Vertices, triangles, normals
  - UV coordinates (and V-flip conventions)
  - **Note:** NIF files contain many other block types (controllers, properties, etc.), but this section focuses on mesh data representation. Other blocks covered in their relevant sections (Animations, Shaders, Physics, etc.)
- **Skinning & Rigging**
  - Bone weights (4 weight limit per vertex)
  - How vertices attach to bones (weight painting)
  - Skin partition data structures
  - **Blender Implementation:** Vertex groups (game bone → Blender vertex group), Armature modifier (connects mesh to skeleton)
- **Shaders & Materials**
  - BSLightingShaderProperty (Skyrim)
  - BSEffectShaderProperty
  - Texture slots (diffuse, normal, specular, etc.)
  - Shader flags (SLSF1_, SLSF2_)
  - BGSM/BGEM (FO4 material files)
- **Partitions & Segments**
  - Skyrim partitions (SBP_* naming)
  - FO4 segments and subsegments
  - SSF files
- **Vertex Data**
  - Vertex colors (COLOR attribute)
  - Vertex alpha (opacity vs wind-sway weight)
  - Custom normals
  - Vertex alpha special cases (trees use alpha as sway weight)
- **Extra Data Nodes**
  - BehaviorGraphExtraData (Skyrim)
  - BSClothExtraData (FO4)
  - BODYTRI references
  - NiStringExtraData
- **Connect Points** (FO4 weapons/armor)
- **Root Nodes** - Scene root handling
- **Transforms & Positioning**
  - Object transforms vs vertex positions
  - Half-precision float issues (FO4 heads at origin)
  - Scale factors (uniform scale requirement)
- **NIF-Embedded Animations**
  - Transform animations (NiTransformController)
  - Shader float animations (emissive, alpha, glossiness, U/V offset)
  - Shader color animations (emission, specular)
  - Alpha threshold animations
  - Visibility animations (NiVisController)
  - Named animations in NIFs (chests, doors, flags)
  - Linear and Bezier interpolation
  - **Note:** NIF-embedded animations are distinct from HKX character animations - little overlap in implementation

#### 1.3 Animations (`file-formats/animations.md`)
- **HKX Format** - Havok packfile structure
  - Skyrim LE (32-bit, hk_2010.2.0-r1)
  - Skyrim SE (64-bit, hk_2010.2.0-r1)
  - Fallout 4 (64-bit, hk_2014.1.0-r1)
- **Skeleton Files** - Bone hierarchy and rest pose
  - hkaSkeleton structure
  - Bone names and parent indices
  - Skin bones (FO4 _skin bone parenting)
- **Animation Files** - Compressed bone transforms
  - hkaSplineCompressedAnimation
  - hkaAnimationBinding
  - Keyframes and interpolation
- **Annotation Markers** - Text keys at specific times
  - NiTextKeyExtraData (NIF-embedded)
  - HKX annotation events
- **File Relationships** - Skeleton HKX ↔ Animation HKX ↔ Character NIF
- **Pointer Resolution** - Fixup tables (local, global, virtual)

#### 1.4 Physics & Collision (`file-formats/physics-collision.md`)
- **Havok Packfile Format (FO4)**
  - bhkPhysicsSystem structure
  - hknpPhysicsSystemData
  - Body properties encoding
    - Truncated float16 encoding
    - Friction, restitution, damping
    - Mass, density, inertia
    - Gravity factor
  - Collision response types
  - Vanilla defaults (friction=0.5, restitution=0.4, etc.)
- **Collision Shapes**
  - bhkBoxShape, bhkSphereShape
  - bhkConvexVerticesShape
  - bhkCapsuleShape
  - MOPP (not yet supported in PyNifly)
- **HDT-SMP (Skinned Mesh Physics)**
  - hdtSkinnedMeshConfigs XML format
  - per-triangle-shape definitions
  - VirtualGround collision (ground clip prevention)
    - **MUST** be defined before bones in XML
    - prenetration vs penetration element names
    - Weighted to NPC Root [Root]
    - Ragdoll flip issue (VirtualGround flips with dead NPCs)
  - Bone constraints and stiffness
  - FSMP MCM auto-reset issues (can cause CTDs)
- **bhkRigidBody**
  - Skyrim: bhkRigidBodyCInfo2010
  - FO4: bhkRigidBodyCInfo2014 (different field layout)
- **Collision Object Types**
  - bhkCollisionObject (legacy)
  - bhkNPCollisionObject (FO4)
- **Elric** (FO4 collision compiler)
  - Converts legacy to FO4 native format
  - Block ordering requirements
  - Requires meshes/ folder structure

#### 1.5 Morphs & Shape Keys (`file-formats/morphs-shapekeys.md`)
- **TRI Files** - Morph/expression data
  - Skyrim/FO4 format (binary)
  - BodySlide/Outfit Studio format
  - Expression morphs (Aah, BrowDownLeft, etc.)
  - Chargen morphs (character customization sliders)
- **Shape Key Conventions** *(PyNifly-specific, not in TRI format itself)*
  - Underscore prefix (_0, _1) for weight variants
  - Greater-than prefix (>) for BodySlide morphs 
  - Asterisk prefix (*) to exclude from export
- **BSDynamicTriShape** (Skyrim SE) - Morphable heads
- **BODYTRI Extra Data** - Reference from NIF to TRI file

#### 1.6 Textures & Materials (`file-formats/textures-materials.md`)
- **DDS Files** - DirectDraw Surface format
  - Compression formats (BC1, BC3, BC5, BC7)
  - Mipmaps
  - PNG workflow (convert for Blender compatibility)
- **BGSM/BGEM** (FO4 Material Files)
  - Alpha blend vs alpha test
  - Texture references
  - Material flags (tree, decal, etc.)
  - No vertex color toggle (determined by vertex format)
- **Texture Paths**
  - Relative to Data folder
  - Auto .dds extension on export
- **Normal Maps** - Tangent space encoding

#### 1.7 Archives (`file-formats/archives.md`)
- **BSA Files** - Bethesda archive format
  - Compression
  - Directory structure
  - Extraction/packing

#### 1.8 Scripts (`file-formats/scripts.md`)
- **PEX Files** - Compiled Papyrus scripts
  - Binary format
  - VMAD (Virtual Machine Adapter) in records

---

### 2. Game-Specific Information (`game-specific/`)

Differences and specifics per game.

#### 2.1 Skyrim LE (`game-specific/skyrim-le.md`)
- 32-bit pointers in HKX
- NiTriShape for meshes
- Body weight system (_0, _1 suffixes)
- Partition system (SBP_)
- hk_2010.2.0-r1 Havok

#### 2.2 Skyrim SE (`game-specific/skyrim-se.md`)
- 64-bit pointers in HKX
- BSTriShape for meshes
- BSDynamicTriShape for morphable heads
- Same partition system as LE
- hk_2010.2.0-r1 Havok

#### 2.3 Fallout 4 (`game-specific/fallout4/`)

FO4 has extensive unique systems requiring multiple files:

**`game-specific/fallout4/overview.md`:**
- 64-bit pointers in HKX
- BSTriShape for meshes
- Segment/subsegment system (SSF files)
- BGSM/BGEM materials instead of shader properties
- hk_2014.1.0-r1 Havok
- Connect points for weapons/armor
- FaceBones system (_faceBones suffix)
- Skin bones (_skin suffix, special parenting)
- Half-precision vertex positions (heads at origin)
- Vertex alpha reuse (trees: wind-sway weight, not opacity)
- bhkPhysicsSystem (packfile format)

**Additional FO4-specific topics** (each in separate files):
- `connect-points.md` - Weapon/armor attachment system
- `workshop-system.md` - Settlement building, MISC objects, snap points
- `facebones.md` - Facial animation rig details
- `material-system.md` - BGSM/BGEM deep dive

---

### 3. Tools & APIs (`tools/`)

Working with the formats programmatically.

#### 3.1 PyNifly (`tools/pynifly/`)
- **Overview** - Blender addon for NIF import/export
- **Installation & Setup**
  - Blender version compatibility (4.4+)
  - io_scene_nifly.zip installation
  - Upgrading (close Blender completely first)
  - Console logging (Windows → Toggle System Console)
- **Architecture**
  - Nifly layer (BS/OS core library)
  - DLL layer (C++ wrapper)
  - PyNifly layer (Python interface)
  - Blender addon layer
- **Importing NIFs**
  - Import options
    - Use Blender orientation
    - Create bones / rename bones
    - Pretty bone orientation
    - Import animations / collisions / tri files
    - Apply skin to mesh
    - Reference skeleton
  - Shaders (auto-created material nodes)
  - Partitions/segments (vertex groups)
  - Bones and armatures
  - Multiple file import
- **Working in Blender**
  - Shape keys (expressions, weights, chargen)
  - Partitions/segments (vertex groups)
  - Normals (custom split normals)
  - Vertex alphas (VERTEX_ALPHA color layer)
  - Quads and triangulation (handled on export)
  - Weight limit (4 groups per vertex)
- **Exporting NIFs**
  - Export options
    - Target game
    - Rename bones
    - Preserve bone hierarchy
    - Export BODYTRI extra data
    - Export pose position
    - Export modifiers
  - Multiple shape keys (separate files)
  - FO4 faceBones (dual armature)
  - Error handling (*MULTIPLE_PARTITIONS*, *NO_PARTITIONS*, *UNWEIGHTED_VERTICES*)
- **HKX Animations**
  - Import skeleton from HKX
  - Import/export animations
  - Native support (no hkxcmd needed)
  - Annotation markers
  - Frame rate (30 FPS default)
  - Bone renaming consistency
- **NIF Animations**
  - Named animations (Actions with fake user flag)
  - Apply Nif Animation command
  - pynActionSlots property
  - pynController property
- **Collisions**
  - Collision mesh representation
  - Import/export support
  - MOPP limitations
- **Python API** (`pyn.pynifly`)
  - `NifFile` class
  - Reading shapes and nodes
  - Direct script usage
- **Example Scripts** (from scripts/ folder)
  - Bone renaming
  - VirtualGround manipulation
  - HDT config checking
  - Collision inspection
  - Texture path replacement
  - Flag manipulation

#### 3.2 esplib (`tools/esplib/`)
- **Overview** - Python library for ESP/ESM manipulation (`tools/esplib/overview.md`)
- **Package Structure**
  - `esplib.record` - Record and GroupRecord classes
  - `esplib.plugin` - Plugin loading/saving
  - `esplib.strings` - String table handling
  - `esplib.defs` - Schema/definition system
- **Schema System**
  - EspRecord, EspSubRecord
  - EspStruct, EspUnion, EspArray
  - EspInteger, EspFloat, EspString, EspFormID
  - EspFlags, EspEnum
  - EspContext for conditional resolution
- **Record Definitions**
  - `defs/tes5.py` - Skyrim record definitions
  - `defs/fo4.py` - Fallout 4 record definitions
  - Common definitions
- **Usage Patterns**
  - Loading plugins
  - Reading record fields
  - Creating patch files
  - Copying records
  - Master resolution
- **CLI Tools**
  - `esplib` command-line interface
  - Round-trip testing
  - Record inspection
- **Round-Trip Fidelity**
  - Byte-perfect save
  - Compression preservation
  - Timestamp/version preservation

#### 3.3 Other Tools (`tools/xedit-reference.md`, `tools/other-tools.md`)

**xEdit** - Brief reference only (no Pascal code - that's deprecated)
- **Common Patterns**
  - Record iteration
  - GetElementEditValues
  - SetElementEditValues
  - Master file access
**Other Tools:**
- **Creation Kit** - Brief reference (detailed CK workflows out of scope)
  - Loading plugins
  - Navmesh editing
  - Plugin corruption detection
- **NifSkope**
  - Manual NIF inspection
  - Show Nodes (bone pose visualization)
  - Block reordering issues (Elric crashes)
- **PyNifly Standalone** (non-Blender)
  - Direct script usage
  - `sys.path.insert(0, './io_scene_nifly')`
  - `from pyn import pynifly`
  - UV V-flip asymmetry issue

---

### 4. Common Tasks & Workflows (`workflows/`)

How-to guides for specific modding tasks.

#### 4.1 Character Creation (`workflows/character-creation.md`)
- **Creating Races**
  - RACE record structure
  - Head data
  - Tint masks (TINI, TINC, TIAS, TINV)
  - Skin textures
  - Body templates
- **NPCs**
  - NPC_ record structure
  - Face morphs
  - Head parts (HDPT references)
  - Tint layers
  - Default outfit (DOFT)
  - Texture lighting (QNAM)
- **Head Parts**
  - HDPT records
  - Types (hair, eyes, scars, eyebrows, facial hair)
  - Model files
  - TriShape requirements (Skyrim SE)
- **FaceGen**
  - TRI files (expressions + chargen)
  - Facegen NIFs (wrong bone positions, need reference skeleton)
  - FO4 faceBones workflow
  - Tint layer workflow

#### 4.2 Armor & Clothing (`workflows/armor-clothing.md`)
- **Armor Creation**
  - ARMO record
  - Armor addons (ARMA)
  - Body slots
  - Biped object flags
- **Armor Addons (ARMA)**
  - Primary race (RNAM)
  - Additional races
  - BOD2 body template
  - Model paths (MOD2, MOD4)
- **Body Weights**
  - _0 (thin) and _1 (muscular) meshes
  - Shape key workflow in Blender
  - Single export generates both files
- **BodySlide Integration**
  - BodySlide TRI format (> prefix)
  - BODYTRI extra data
  - Slider creation
  - OSD/OSP project files

#### 4.3 Meshes & Modeling (`workflows/meshes-modeling.md`)
- **Import Workflow**
  - Import skeleton first (for full bone set)
  - Import mesh onto skeleton
  - Import tris onto base mesh
  - Multiple file import (combine sensibly)
- **Blender Workflow**
  - Working with quads (triangulated on export)
  - UV seams (handled automatically)
  - Weight painting (4 group limit)
  - Shape keys for morphs
  - Collections for organizing nif parts
- **Export Workflow**
  - Select all parts to export
  - Target game selection
  - Bone renaming options
  - Modifier application
- **Common Issues**
  - Unweighted vertices
  - Multiple/missing partitions
  - Non-uniform scale (warning, uses scaled positions)
  - Seam visibility (custom normals or bevel)

#### 4.4 Animations (`workflows/animations.md`)
- **Importing HKX Skeleton**
  - Use skeleton.hkx, NOT skeleton.nif
  - Stores bone list and game type on armature
  - Common skeleton locations
- **Importing HKX Animations**
  - Select armature first
  - Creates Blender Action
  - Annotation markers on timeline
  - Frame rate setup (30 FPS)
- **Creating Animations**
  - Pose bones in Blender
  - Use Action Editor
  - Timeline markers for annotations
  - Bone renaming consistency
- **Exporting HKX**
  - Select armature
  - Choose target game
  - FPS setting (default 30)
  - No reference skeleton needed (uses armature data)
- **NIF Animations**
  - Named animations (Open, Close, etc.)
  - pynActionSlots property setup
  - NiControllerManager structure
  - Multiple animation export

#### 4.5 Physics & Collisions (`workflows/physics-collisions.md`)
- **HDT-SMP Setup**
  - XML config creation
  - VirtualGround **before** bones (critical!)
  - per-triangle-shape definitions
  - Bone constraints
  - Config file references in NIF
- **Ground Collision**
  - VirtualGround collision mesh
  - margin=5, prenetration=1, tag=ground
  - Weighted to NPC Root [Root]
  - Ragdoll flip limitation
- **Havok Collision (FO4)**
  - bhkPhysicsSystem in NIF
  - Body properties (friction, restitution, mass)
  - Elric compilation
  - Block ordering requirements
- **Debugging Physics**
  - FSMP MCM auto-reset (disable if causing CTDs)
  - Check actual game Data folder (not workspace)
  - Verify bone references in configs
  - Collision mesh weighting

#### 4.6 Textures & Materials (`workflows/textures-materials.md`)
- **Shader Setup (Skyrim)**
  - BSLightingShaderProperty
  - Texture slots (diffuse, normal, specular, etc.)
  - Shader flags
- **Material Setup (FO4)**
  - BGSM/BGEM files
  - Alpha blend vs alpha test
  - Vertex color handling
  - Tree materials (alpha as sway weight)
- **Texture Workflow**
  - DDS creation
  - PNG for Blender preview
  - Path conventions (relative to Data)
  - Normal map baking

#### 4.7 Packaging & Distribution
- **BSA Creation**
- **Plugin Finalization**
  - Testing in Creation Kit
  - In-game testing
  - Load order considerations

---

### 5. Debugging & Troubleshooting (`debugging/`)

Common issues and solutions.

#### 5.1 CTD (Crash to Desktop) (`debugging/ctd-crashes.md`)
- **Load-time CTDs**
  - Check crash logs for specific errors
  - NetImmerse.HasNode access violations (check HDT configs)
  - FSMP MCM auto-reset (disable FSMPM.esp)
  - Missing master files
- **Debugging Process**
  - Check actual game Data folder (not workspace!)
  - Use crash logs
  - Binary search (disable half the mods)
  - Test in clean save

#### 5.2 Mesh Issues (`debugging/mesh-issues.md`)
- **Clipping Through Ground**
  - VirtualGround defined too late in XML
  - Wrong element name (penetration vs prenetration)
  - Check VirtualGround weighting
  - Ragdoll flip (nearby dead NPCs affect living)
- **Weighting Problems**
  - Check for unweighted vertices (*UNWEIGHTED_VERTICES* group)
  - 4 weight limit per vertex
  - Tail roots should NOT be weighted to tail bones (felines)
  - Check skin bone parenting (FO4)
- **Missing Parts**
  - Partition issues (*NO_PARTITIONS*, *MULTIPLE_PARTITIONS*)
  - Wrong game export
  - Missing ARMA additional races
- **Texture Issues**
  - Wrong paths
  - Missing DDS files
  - Alpha channel problems (check BGSM settings)
- **Invisible Meshes**
  - Vertex alpha (FO4 non-tree materials)
  - Alpha test threshold
  - Backface culling
  - Scale issues

#### 5.3 Animation Issues (`debugging/animation-issues.md`)
- **Import Failures**
  - Wrong skeleton (use HKX not NIF)
  - Bone renaming inconsistency
  - Game version mismatch
- **Export Failures**
  - Missing bone data on armature
  - Non-uniform scale
  - Unsupported interpolation types
- **In-Game Issues**
  - Skeleton mismatch
  - Missing animation files
  - Wrong priority

#### 5.4 Physics Issues (`debugging/physics-issues.md`)
- **HDT Not Working**
  - Config file reference in NIF
  - XML syntax errors
  - VirtualGround ordering
  - FSMP compatibility
- **Collision Not Working**
  - Elric compilation errors
  - Wrong block order
  - Missing bhkPhysicsSystem
  - Body properties incorrect

#### 5.5 Plugin Issues (`debugging/plugin-issues.md`)
- **CK Won't Load**
  - Corrupted navmesh
  - Missing masters
  - Invalid record data
  - Compression issues
- **In-Game Errors**
  - FormID conflicts
  - Missing assets
  - Script errors (VMAD)

#### 5.6 Performance
- **Mesh Optimization**
  - Vertex count
  - Triangle count
  - Texture resolution
- **Physics Optimization**
  - Collision complexity
  - HDT bone count
  - Update rate

---

### 6. Reference Data (`reference/`)

Look-up tables and constants.

#### 6.1 Record Types (`reference/record-types.md`)
- **Common to All Games**
  - GMST (Game settings)
  - GLOB (Global variables)
  - ARMO (Armor)
  - WEAP (Weapons)
  - NPC_ (NPCs)
  - RACE (Races)
  - CELL (Cells)
  - WRLD (Worldspaces)
- **Skyrim-Specific**
  - HDPT (Head parts)
  - ARMA (Armor addon)
- **FO4-Specific**
  - OMOD (Object modifications)

#### 6.2 Bone Names (`reference/bone-names.md`)
- **Human Skeleton (Skyrim/FO4)**
  - NPC Root [Root]
  - NPC Pelvis [Pelv]
  - NPC Spine [Spn0], NPC Spine1 [Spn1], NPC Spine2 [Spn2]
  - NPC L/R Hand
  - HDT bone conventions
- **Creature Skeletons**
  - Dog, Draugr, Supermutant, etc.
  - Non-standard bone positions

#### 6.3 Shader Flags (`reference/shader-flags.md`)
- **SLSF1_** flags
  - SLSF1_VERTEX_ALPHA
  - (etc., full list)
- **SLSF2_** flags
  - SLSF2_VERTEX_COLORS
  - SLSF2_TREE_ANIM (wind effect)
  - (etc., full list)

#### 6.4 Partition Names (`reference/partition-names.md`)
- SBP_30_HEAD
- SBP_32_BODY
- SBP_33_HANDS
- (Full list)

#### 6.5 Subsegment Names (`reference/subsegment-names.md`)
- Naming convention (Material:Subsegment)
- SSF file format

#### 6.6 Expression Morph Names (`reference/expression-morphs.md`)
- **Skyrim**
  - Aah, BigAah, BMP, etc.
  - (Full list)
- **FO4**
  - (Full list)

#### 6.7 Common FormIDs (`reference/common-formids.md`)
- Vanilla races
- Default outfits
- Common armor pieces

---

## Implementation Notes

### Content Sources to Extract

**From xEditDev:**
- PROJECT_PLAN.md (esplib architecture)
- PLAN_ESPLIB_EXTENSION.md (record definitions)
- PLAN_FURRIFIER_*.md (NPC/race workflows)
- Code examples from bethesda_plugins/

**From PyNifly:**
- ANIMATIONS.md
- NIF_ANIMATIONS.md
- DEVELOPERS.md
- PROJECT_PLAN.md
- docs/*.md (format documentation)
- scripts/*.py (example code)

**From PyNifly Wiki:**
- Installation
- Usage guide
- Import/export options
- Game-specific summaries
- Troubleshooting

**From User Memory:**
- skyrim-debugging.md (HDT ground collision, CTD debugging, file formats)

### Organization Principles

1. **Format before workflow** - Understand the file structure before learning how to create content
2. **Game differences explicit** - Don't make readers guess which game a detail applies to
3. **Code examples inline** - Show, don't just tell
4. **Cross-references** - Link related concepts
5. **Progressive detail** - Overview → details → edge cases
6. **Searchability** - Good headers, clear terminology

### Next Steps

1. Create directory structure in Bethesda Library workspace
2. Extract content from source projects
3. Fetch and format wiki content
4. Write connecting narrative and examples
5. Build cross-reference index
6. Review and refine

---

## AI-Specific Additions (`ai-reference/`)

For AI consumers (where a modder points an AI at this library and says "build me X mod"), we need additional structured sections:

### 0. Core Concepts & Taxonomy (`ai-reference/glossary.md`)
**Purpose:** Establish precise definitions to prevent terminology confusion.

- **Glossary**
  - FormID vs EditorID vs BaseID
  - Record vs Subrecord vs Field
  - Shape vs Mesh vs Block vs Node
  - Bone vs Joint vs Skeleton
  - Partition vs Segment vs Subsegment
  - Override vs Patch vs Master
  - Skin vs Weight vs Rig
- **File Type Taxonomy**
  - What each extension means (.esp, .esm, .esl, .nif, .hkx, .tri, .dds, .bgsm, .xml, .pex, .bsa)
  - Which files can reference which (dependency graph)
  - Which files go where in Data folder structure
- **Coordinate Systems**
  - Game space vs Blender space
  - When to apply transformations
  - Handedness and axis orientation
- **Terminology Mapping** (Game ↔ Blender ↔ General 3D)
  - Skeleton = Armature = Bone hierarchy
  - Bone weight = Vertex group weight = Skin influence
  - Partition = Vertex group (Skyrim) / Mesh segment (general)
  - Shape key = Morph target = Blend shape
  - Mesh = NIF shape = Geometry data
  - Material = Shader property (Skyrim) / BGSM file (FO4)
  - UV map = Texture coordinates
  - Normal = Surface orientation vector
  - Tri = Morph data = Shape key data
- **Precision Rules**
  - When floating point precision matters
  - Half-precision float limitations (FO4 heads)
  - Integer overflow considerations

### 7. Validation Rules & Constraints (`ai-reference/validation-rules.md`)
**Purpose:** Explicit rules for what makes valid data, enabling AIs to self-check.

#### 7.1 ESP/ESM Validation
- FormID constraints (valid ranges, master index limits)
- Required subrecords per record type
- String encoding rules (null termination, localization)
- Size limits (XXXX overflow trigger at 65535 bytes)
- Flag compatibility matrix (which flags can coexist)

#### 7.2 NIF Validation
- Vertex limits per shape
- UV coordinate valid ranges (0-1, or repeating?)
- Weight constraints (4 bones max, sum to 1.0)
- Triangle winding order (clockwise/counter-clockwise by game)
- Bone name character restrictions
- Partition assignment rules (every face needs one)
- Collision shape requirements

#### 7.3 Animation Validation
- Keyframe count limits
- Frame rate constraints (standard 30 FPS)
- Bone name matching requirements (skeleton vs animation)
- Annotation marker format rules

#### 7.4 Physics Validation
- Mass/density/inertia relationships
- Friction/restitution valid ranges (0-1 typically)
- VirtualGround ordering requirement (MUST precede bones)
- XML well-formedness for HDT configs

### 8. Decision Trees (`ai-reference/decision-trees.md`)
**Purpose:** Explicit logic for "when to use X vs Y" decisions.

#### 8.1 Which Game Format?
```
IF target_game == "Skyrim SE" OR "FO4":
    use BSTriShape
ELIF target_game == "Skyrim LE":
    use NiTriShape
ENDIF

IF target_game == "Skyrim SE" AND has_facial_morphs:
    use BSDynamicTriShape
ENDIF
```

#### 8.2 Which Partition System?
```
IF game == "Skyrim":
    use SBP_* partitions
    create vertex groups: "SBP_30_HEAD", "SBP_32_BODY", etc.
ELIF game == "FO4":
    use segments/subsegments
    require SSF file
    create vertex groups: "Material:Subsegment" format
ENDIF
```

#### 8.3 Shader vs Material
```
IF game == "FO4":
    use BGSM/BGEM material files
    vertex color determined by vertex format flag, not shader flag
ELSE:
    use BSLightingShaderProperty in NIF
    set shader flags (SLSF1_*, SLSF2_*)
ENDIF
```

#### 8.4 When to Create Separate NIFs
```
IF creating body armor:
    create _0.nif (weight 0) AND _1.nif (weight 1)
ELIF creating head part:
    create single .nif + .tri files
ELIF creating FO4 head:
    create basehead.nif AND basehead_facebones.nif
ENDIF
```

### 9. Complete Code Templates (`ai-reference/code-templates.md`)
**Purpose:** Working, copy-paste code for common operations (no "..." or "fill in" placeholders).

#### 9.1 PyNifly: Read NIF Data
```python
import sys
sys.path.insert(0, 'C:/Modding/PyNifly/io_scene_nifly')
from pyn import pynifly

# Load a NIF file
nif = pynifly.NifFile('path/to/mesh.nif')

# List all shapes
for shape in nif.shapes:
    print(f"Shape: {shape.name}")
    print(f"  Vertices: {len(shape.verts)}")
    print(f"  Triangles: {len(shape.tris)}")
    print(f"  UVs: {len(shape.uvs)}")
    
# Access nodes (bones, collision, etc.)
for node_name, node in nif.nodes.items():
    print(f"Node: {node_name}")
    print(f"  Type: {type(node).__name__}")

# Check game type
print(f"Game: {nif.game}")  # 'SKYRIM', 'SKYRIMSE', 'FO4', etc.
```

#### 9.2 esplib: Read ESP Records
```python
from esplib import Plugin

# Load plugin
plugin = Plugin.load('path/to/plugin.esp')

# Iterate over NPC records
for record in plugin.iter_records('NPC_'):
    editor_id = record.get('EDID', {}).get('value', 'Unknown')
    print(f"NPC: {editor_id} (FormID: {record.form_id:08X})")
    
    # Access nested fields
    if 'ACBS' in record:
        flags = record['ACBS']['flags']
        is_female = bool(flags & 0x01)
        print(f"  Female: {is_female}")

# Create new plugin
new_plugin = Plugin.new_plugin('MyPatch.esp', masters=['Skyrim.esm'])

# Copy a record
vanilla_npc = plugin.get_record_by_formid(0x00000007)  # Player reference
new_plugin.copy_record(vanilla_npc, plugin)

# Save
new_plugin.save('output/MyPatch.esp')
```

#### 9.3 PyNifly: Create Simple Mesh
```python
# Complete working example - create a cube NIF
from pyn import pynifly
import sys
sys.path.insert(0, 'C:/Modding/PyNifly/io_scene_nifly')

# Create new NIF
nif = pynifly.NifFile()
nif.initialize('SKYRIMSE')

# Define cube vertices
verts = [
    (-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),  # bottom
    (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)       # top
]

# Define triangles (indices into verts)
tris = [
    (0,1,2), (0,2,3),  # bottom face
    (4,6,5), (4,7,6),  # top face
    (0,4,5), (0,5,1),  # front face
    (1,5,6), (1,6,2),  # right face
    (2,6,7), (2,7,3),  # back face
    (3,7,4), (3,4,0)   # left face
]

# Define UVs (one per vertex)
uvs = [(0,0), (1,0), (1,1), (0,1), (0,0), (1,0), (1,1), (0,1)]

# Create shape
shape_data = {
    'name': 'CubeMesh',
    'verts': verts,
    'tris': tris,
    'uvs': uvs,
    'normals': [(0,0,-1)]*4 + [(0,0,1)]*4  # simplified normals
}

nif.createShapeFromData('CubeMesh', shape_data, None)

# Save
nif.save('output/cube.nif')
```

### 10. State Machines & Workflows (`ai-reference/state-machines.md`)
**Purpose:** Multi-step processes with explicit state transitions.

#### 10.1 NPC Creation Workflow
```
State 1: RACE_DEFINED
  - RACE record exists in master or patch
  - Has required subrecords: EDID, HEAD, BODY
  → Can proceed to State 2

State 2: HEADPARTS_ASSIGNED  
  - All required HDPT types have at least one option
  - HDPT records exist and are valid
  → Can proceed to State 3

State 3: NPC_CREATED
  - NPC_ record created with EDID, RACE reference
  - ACBS flags set (male/female, unique, etc.)
  → Can proceed to State 4

State 4: APPEARANCE_SET
  - Head parts selected and referenced
  - Tint layers defined (if any)
  → Can proceed to State 5

State 5: EQUIPMENT_ASSIGNED
  - Default outfit (DOFT) set
  - Inventory items added
  → NPC complete, ready for testing
```

#### 10.2 Armor Creation Workflow
```
State 1: MESH_CREATED
  - Body mesh modeled in Blender
  - Skinned to skeleton
  - Partitions/segments assigned
  → Export NIF, proceed to State 2

State 2: NIF_EXPORTED
  - Both _0.nif and _1.nif exist (Skyrim)
  - NIFs pass validation (no unweighted verts, no missing partitions)
  → Proceed to State 3

State 3: ARMA_DEFINED
  - ARMA record created with EDID
  - Primary race (RNAM) set
  - BOD2 body template matches mesh partitions
  - Model paths (MOD2, MOD4) point to NIFs
  → Proceed to State 4

State 4: ARMO_DEFINED
  - ARMO record created
  - References ARMA
  - Body slot flags set
  - Equip type set
  → Proceed to State 5

State 5: TESTED
  - Armor appears in CK
  - Equips in-game without CTD
  - Model displays correctly
  → Complete
```

### Appendix A: Binary Format Schemas (`ai-reference/binary-schemas.md`)
**Purpose:** Complete struct definitions for parsing/writing binary files.

Provide JSON schemas or Python dataclass definitions for:
- ESP record headers
- NIF block structures (BSTriShape, NiNode, etc.)
- HKX packfile headers
- TRI file format
- BGSM material files

Example:
```python
@dataclass
class RecordHeader:
    """ESP/ESM record header (24 bytes)"""
    signature: str      # 4 bytes, e.g. "NPC_"
    data_size: int      # 4 bytes, uint32
    flags: int          # 4 bytes, uint32
    form_id: int        # 4 bytes, uint32
    timestamp: int      # 2 bytes, uint16
    version: int        # 2 bytes, uint16
    unknown: int        # 4 bytes, uint32
```

### Appendix B: File Path Conventions (`ai-reference/file-path-conventions.md`)
**Purpose:** Exact patterns for where files go, enabling path generation.

```
Skyrim Data folder structure:
  meshes/
    actors/character/
      character assets/
        skeleton.nif            # Human skeleton (static reference)
        skeleton.hkx            # Human skeleton (animation reference)
        malebody_0.nif          # Male body weight 0
        malebody_1.nif          # Male body weight 1
      _male/
        malehead.nif            # Male head base mesh
        malehead.tri            # Expression morphs
        maleheadchargen.tri     # Character customization morphs
    armor/
      iron/
        ironarmor_0.nif         # Iron armor weight 0
        ironarmor_1.nif         # Iron armor weight 1
        1stpersonironarmor_0.nif # First-person view (optional)
        1stpersonironarmor_1.nif

FO4 Data folder structure:
  meshes/
    actors/character/
      characterassets/
        skeleton.hkx            # Human skeleton
        basemaleface.nif        # Male face mesh
        basemaleface_facebones.nif
      basemalehead/
        basemaleface.tri        # Expressions
        basemaleheadchargen.tri # Chargen
  materials/
    armor/
      iron/
        ironarmor.bgsm          # Material definition (points to textures)
  textures/
    armor/
      iron/
        ironarmor_d.dds         # Diffuse
        ironarmor_n.dds         # Normal
        ironarmor_s.dds         # Specular

Pattern rules:
- NIF weight variants: basename_0.nif, basename_1.nif
- TRI files: match NIF basename + suffix (.tri or chargen.tri)
- FO4 facebones: basename_facebones.nif
- Texture paths in NIF/BGSM: relative to Data/, lowercase, forward slashes
```

### Appendix C: Default Values (`ai-reference/default-values.md`)
**Purpose:** What to use when values aren't specified.

```yaml
NPC_defaults:
  confidence: 3  # Confident
  assistance: 0  # Helps nobody
  aggression: 0  # Unaggressive
  disposition_base: 50  # Neutral
  mood: 0  # Neutral
  
Physics_defaults:
  friction: 0.5
  restitution: 0.4
  linear_damping: 0.1
  angular_damping: 0.05
  gravity_factor: 1.0
  max_linear_velocity: 104.4
  max_angular_velocity: 31.6

Animation_defaults:
  fps: 30
  interpolation: linear  # or bezier for smoother curves
  
Shader_defaults:
  glossiness: 33.0
  specular_strength: 1.0
  emissive_multiple: 1.0
```

---

## Open Questions

1. Should we include Creation Kit-specific workflows, or keep this to file formats and Python tools?
// I think no--describing the CK is out of scope
2. How much xEdit Pascal code to include vs Python equivalents?
// No pascal. That's dead.
3. Create separate "cookbook" section for common recipes (e.g. "convert NPC to furry race")?
// No, "Common Tasks and Workflows" should be sufficient.
4. Should scripts from PyNifly/scripts be documented individually or as a collection?
// I think not
5. **NEW:** Should we generate machine-readable schemas (JSON Schema, Protocol Buffers, etc.) for all binary formats?
// That sounds like a big deal. Not now.
6. **NEW:** Should we include a "Quick Reference Card" summarizing all decision trees on one page?
// No.
7. **NEW:** Should validation rules be executable (provide Python validators AIs can run)?
// No. If they're clear people can build what they need.
8. **NEW:** Should decision trees be provided as executable code (Python functions that take context and return choices)?
// No. 
  
---

## Scope Decisions

Based on initial planning, the following decisions define what's in and out of scope:

**In Scope:**
- ? File format specifications and Python tools (PyNifly, esplib)
- ? Complete working code examples (no placeholders)
- ? Common Tasks & Workflows section (sufficient for recipes/how-tos)
- ? Clear decision trees and validation rules (as prose descriptions)
- ? Game-specific sections for Skyrim LE/SE and Fallout 4

**Out of Scope:**
- ? Creation Kit-specific workflows (too tool-specific, not format/Python focused)
- ? Pascal/xEdit scripting (deprecated - Python equivalents only)
- ? Separate cookbook section (redundant with Workflows)
- ? Individual documentation of PyNifly example scripts (collection reference sufficient)
- ? Machine-readable schemas (JSON Schema, Protocol Buffers) - too much work for now
- ? Quick reference card - not necessary
- ? Executable validators - clear descriptions allow users to build what they need
- ? Executable decision tree functions - prose descriptions sufficient
- ? FO76, FO3, FONV support - may add later if content becomes available
