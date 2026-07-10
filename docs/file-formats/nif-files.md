# NIF Files

NIF (NetImmerse Format) is the primary 3D mesh format used in Bethesda games. NIFs contain geometry, skinning, materials, physics, and more. They can vary significantly between games in the blocks used and the format of those blocks.

## Overview

**Full name:** NetImmerse File Format  
**Extension:** `.nif`  
**Type:** Binary tree structure  
**Games:** Morrowind, Oblivion, Skyrim LE/SE, Fallout 3/NV/4/76

NIF is a scene graph format — a hierarchical tree of blocks (nodes) where each block represents part of the 3D scene (mesh, bone, shader, collision, etc.).

## File Structure

```
NIF File
├── Header (version, game type)
├── Block Index
└── Blocks (nodes in tree)
    ├── NiNode (scene root, bones)
    ├── BSTriShape (mesh geometry) [Skyrim SE, FO4]
    ├── NiTriShape (mesh geometry) [Skyrim LE]
    ├── BSLightingShaderProperty (materials)
    ├── NiSkinInstance (rigging data)
    ├── bhkCollisionObject (physics)
    └── (many other block types)
```

Each block has:
- **Type** - What kind of data (NiNode, BSTriShape, etc.)
- **Properties** - Data fields (vertices, bone indices, flags, etc.)
- **References** - Pointers to other blocks (parent, children, skin data, etc.)

The full defintion of the nif format is in nif.xml, available at (TODO: Reference the niftools site).

## Game Differences

### Skyrim LE (32-bit)

**Mesh format:** NiTriShape  
**Partitions:** SBP_* system (SBP_30_HEAD, SBP_32_BODY, etc.)  
**Materials:** BSLightingShaderProperty in NIF  
**Vertex precision:** Full float32

### Skyrim SE (64-bit)

**Mesh format:** BSTriShape (optimized)  
**Partitions:** Same SBP_* system as LE  
**Materials:** BSLightingShaderProperty in NIF  
**Vertex precision:** Full float32  
**Special:** BSDynamicTriShape for morphable heads

### Fallout 4 (64-bit)

**Mesh format:** BSTriShape  
**Havok version:** hk_2014.1.0-r1 (64-bit pointers)  
**Partitions:** Segment/subsegment system (SSF files)  
**Materials:** BGSM/BGEM external files (not in NIF)  
**Vertex precision:** Half-float16 for positions (heads at origin)  
**Vertex alpha:** Reused for wind-sway weight in trees  
**Special features:**
- Connect points (weapon/armor/workshop attachments)
- FaceBones system (separate set of bones for character morphs)
- Skin bones for bone weights (`_skin` suffix, special parenting)

## Core Block Types

### Scene Structure Blocks

#### NiNode
Generic node that groups other blocks. Used for:
- Scene root (topmost block)
- Bones in skeleton
- Organization/hierarchy

**Key properties:**
- Name (e.g., "NPC Root [Root]", "NPC Spine [Spn0]")
- Transform (position, rotation, scale)
- Children (list of child blocks)

#### BSFadeNode
Bethesda subclass of NiNode — same fields, but the engine applies LOD distance fading when it's the **root block** of a static NIF.

**Use as root for:** statics, clutter, weapons, any STAT/MSTT/FURN model.
**Don't use as root for:** skinned meshes (armor, bodies, skeletons) — keep those as plain `NiNode`.

A static with a `NiNode` root may render in NifSkope but go invisible in-game or CTD when dynamically enabled. Other Bethesda root types: `BSLeafAnimNode` (foliage), `BSTreeNode` (LOD trees), `BSOrderedNode` (forced draw order).

Non-root nodes (bones, group nodes) stay as plain `NiNode`; the rule applies only to the topmost block.

### Mesh Geometry Blocks

#### NiTriShape (Skyrim LE, older games)
Legacy mesh format.

**Key data:**
- Vertices (positions, normals, UVs)
- Triangles (vertex indices)
- Vertex colors
- Skin instance reference (rigging)
- Shader property reference (material)

#### BSTriShape (Skyrim SE, Fallout 4)

Modern optimized mesh format, smaller file size than NiTriShape.

`[SSE]` Partitions embedded in BSTriShape.

`[FO4]` Vertex positions as half-float16; segments/subsegments for dismemberment.

#### BSDynamicTriShape (Skyrim SE only)
Special BSTriShape variant that supports runtime morphing.

**Used for:**
- Character heads (expression morphs)
- CharGen-enabled meshes (all headparts)

### Skinning (Rigging) Blocks

#### NiSkinInstance
Links mesh vertices to skeleton bones.

**Properties:**
- Skeleton root (NiNode)
- Bone list (array of NiNode references)
- Skin data (NiSkinData reference)
- Skin partition (NiSkinPartition reference)

#### BSDismemberSkinInstance (Skyrim/FO4)
Extends NiSkinInstance with dismemberment data.

**Per-partition data:**
- Dismemberment flags (head, torso, arms, etc.)
- Body part index

#### NiSkinData
Bone-to-vertex binding information.

**Per-bone data:**
- Bone bind transform
- Vertex weights (which vertices this bone affects)
- Weight values (influence strength 0.0-1.0)

**Constraint:** Each vertex can have **maximum 4 bone weights** in Skyrim/FO4.

#### NiSkinPartition
Divides mesh into partitions. Skyrim does not do real dismemberment--these partitions are used to remove parts of the body or other armors that are covered by an armor. E.g. tall boots cover feet and calves, so the lower legs on the body armor may be removed.

`[Skyrim]` **Partitions (SBP_* system):**
```
SBP_30_HEAD      - Head slot
SBP_32_BODY      - Torso
SBP_33_HANDS     - Hands
SBP_34_FOREARMS  - Forearms
SBP_35_AMULET    - Necklace
SBP_36_RING      - Ring
SBP_37_FEET      - Boots
SBP_38_CALVES    - Legs
SBP_39_SHIELD    - Shield
SBP_40_TAIL      - Tails (custom races)
SBP_41_LONGHAIR  - Hair
SBP_42_CIRCLET   - Circlet
SBP_43_EARS      - Ears
SBP_44_BODYADDON - ModBodyAddon slots
...
SBP_130_HEAD to SBP_143_EARS  - Additional skinned head/hair parts
SBP_150_DECAP_HEAD            - Decapitation
SBP_230_HEAD (BP_EXTRADATA_START) - Editor markers for extra data attachment points
```

`[FO4]` **Segments/subsegments:**
- Segments may or may not contain subsegments
- For bodyparts, segments have a fixed order:
    - 0: empty
    - 1: head
    - 2: right arm
    - 3: torso
    - 4: left arm
    - 5: right leg
    - 6: left leg
- Subsegments split up the bodypart. Order is from closest-to-torso to extremity. Dismemberment happens in the reverse order.
- Has an associated external SSF (Segment SubSegment File)
- Has material

See [Partition Names](../../reference/partition-names.md) for complete list.

### Material/Shader Blocks

#### BSLightingShaderProperty (Skyrim, Skyrim SE)
Defines how a mesh is rendered.

**Shader flags:**
- SLSF1_* (Set 1): Vertex alpha, vertex colors, etc.
- SLSF2_* (Set 2): Environment mapping, tree anim, etc.

See [Shader Flags](../../reference/shader-flags.md) for complete list.

References textures through a separate BSShaderTextureSet block

#### BSEffectShaderProperty
For special effects (glows, magic effects, water).

**Properties:**
- Base texture
- Greyscale texture
- Emissive color/multiplier
- Falloff parameters

#### BSShaderTextureSet
Container for texture paths. Some slots are used differently depending on the shader flags.

**Holds up to 10 texture paths:**
- [0] Diffuse
- [1] Normal
- [2] Glow/Subsurface
- [3] Parallax
- [4] Cubemap
- [5] Environment mask
- [6] Tint/Detail
- [7] Backlight
- [8] Specular (SE)
- [9] Lighting (SE)

Paths are relative to `Data/` folder and auto-append `.dds` if missing.

#### BGSM/BGEM Files (Fallout 4)
FO4 uses **external material files** instead of embedding shader properties in NIFs.

**BGSM (Material):**
- Texture paths
- Alpha blend vs alpha test
- Shader flags
- No vertex color toggle (determined by vertex format)

**BGEM (Effect Material):**
- For effects, glows, blood decals

**In NIF:** BSLightingShaderProperty name references external BGSM path.

See [Textures & Materials](textures-materials.md) for BGSM format details.

### Collision Blocks

#### bhkCollisionObject (Skyrim)
Attaches collision shapes to scene nodes.

**Properties:**
- Target (which NiNode this collision belongs to)
- Collision filter (layers, flags)
- Rigid body reference

See [Physics & Collision](physics-collision.md) for details and collision structure.

### Extra Data Blocks

#### NiStringExtraData
Arbitrary string metadata.

**Common uses:**
- "BODYTRI" - Reference to TRI morph file
- "HDT" - HDT-SMP physics config path
- Various editor markers

#### BSBehaviorGraphExtraData (Skyrim)
References behavior files for animation control.

**Properties:**
- Behavior graph file path
- Used for NPC animation blending

#### BSClothExtraData (FO4)
References cloth simulation data.

### Animation Blocks (NIF-Embedded)

NIFs can contain embedded animations for objects (not character animations — those are in HKX files).

See [need a page for this] for details of animation structure.
See [NIF Animations](../../workflows/animations.md#nif-embedded-animations) for workflows.

## Vertex Data

### Vertex Attributes

**Position:** 3D coordinates (X, Y, Z)
- `[Skyrim]` float32 (full precision)
- `[FO4]` float16 (half precision) — heads must be at origin

**Normal:** Surface orientation vector (X, Y, Z)
- Used for lighting calculations
- Should be unit length (magnitude 1.0)

**UV:** Texture coordinates (U, V)
- U: horizontal (0.0 = left, 1.0 = right)
- V: vertical (0.0 = top, 1.0 = bottom)
- The mapping between vertex and UV is 1:1. Vertices must be doubled where UV islands touch.

**Vertex Color:** RGBA (4 channels)
- RGB: Color tint
- A: Alpha (transparency) **or** other data (see below)

**Vertex Alpha Special Cases:**
- **Most materials:** Opacity/transparency
- `[FO4]` **Trees:** Wind-sway weight (not transparency)
- **BGSM flag:** "Use Vertex Alpha" determines interpretation

**Tangent/Bitangent:** For normal mapping (auto-calculated)

### Vertex Limits

**Skyrim LE:** 65535 vertices per shape (uint16 indices)  
**Skyrim SE:** 65535 vertices per shape  
**Fallout 4:** 65535 vertices per shape  

Meshes with more vertices must be split into multiple shapes.

### Bone Weight Constraints

Each vertex can reference **maximum 4 bones** with weights summing to 1.0.

**Example:**
```
Vertex 0:
  Bone 0 (Spine):     0.5
  Bone 1 (Pelvis):    0.3
  Bone 2 (L Thigh):   0.2
  Total:              1.0
```

## Transforms

### Object-Level Transforms

Nodes can have transforms (position, rotation, scale) applied at the **block level**.

**NiNode transform:**
- Translation (X, Y, Z offset)
- Rotation (3x3 matrix or quaternion)
- Scale (single value; nifs support uniform scale only)

**Vertex positions vs object transforms:**
- Vertex positions are in **local space**
- Object transform converts local → world space

### Half-Precision Float Issues (FO4)

FO4 stores vertex positions as **half-float16** (16-bit floats).

**Precision:** ~3 decimal places  
**Range:** ±65504

**Problem:** This is not enough precision to represent a human-sized object smoothly. A head placed at Z 120 (head height) will have visible stepping.

**Solution:** FO4 head meshes are positioned at origin (0, 0, 0) in mesh space, then positioned via skeleton bone transforms.

## Debugging NIFs

### Tools

**NifSkope** - Visual NIF inspector
- View block tree
- Inspect properties
- Check references
- **Limitation:** Comes as close as any tool to showing what the mesh will look like in game, but still not perfect.

**PyNifly (Blender)** - Import and inspect in 3D
- See mesh as rendered
- Bone weights and armatures imported
- Shader set up to represent visual appearance in game.

**PyNifly (Python)** - Script-based analysis
- Batch checking
- Automated validation
- Extract statistics

### Common Issues

**Unweighted Vertices**
- **Symptom:** Mesh parts don't move with skeleton
- **Cause:** Vertices not assigned to bones
- **Fix:** Weight paint missing vertices

**Wrong Partitions**
- **Symptom:** Armor doesn't hide body parts correctly
- **Cause:** Mesh vertices not in correct SBP partition
- **Fix:** Assign vertices to proper partition vertex groups

**Texture Paths**
- **Symptom:** Purple/missing textures in-game
- **Cause:** Texture path wrong or file missing
- **Fix:** Check BSShaderTextureSet paths, ensure DDS files exist

**Vertex Limit Exceeded**
- **Symptom:** Export fails or mesh corrupted
- **Cause:** More than 65535 vertices in one shape
- **Fix:** Split mesh into multiple shapes

`[FO4]` **Half-Precision Precision Loss**
- **Symptom:** Visible vertex stepping/banding
- **Cause:** Mesh positioned far from origin
- **Fix:** Center mesh at origin, use bone transforms for positioning

## Related Topics

- **[Animations](animations.md)** - HKX skeletal animations
- **[Physics & Collision](physics-collision.md)** - bhk* collision blocks
- **[Morphs & Shape Keys](morphs-shapekeys.md)** - TRI files
- **[Textures & Materials](textures-materials.md)** - DDS, BGSM/BGEM
- **[PyNifly](../tools/pynifly/overview.md)** - Working with NIFs in Blender

## External Resources

- [NifTools Documentation](https://github.com/niftools/nifxml)
- [NIF Format XML Specs](https://github.com/niftools/nifxml/tree/develop/nif.xml)
- [NifSkope](https://github.com/niftools/nifskope)
- [Nifly Library](https://github.com/ousnius/nifly) - Powers PyNifly

---

**Ready to work with NIFs?** Check out [PyNifly workflows](../../workflows/meshes-modeling.md).

_Reviewed 2026-04-25, Bad Dog_