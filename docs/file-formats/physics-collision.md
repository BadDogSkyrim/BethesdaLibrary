# Physics & Collision

Bethesda games use Havok physics for collision detection and dynamic simulation. There are two main physics systems:

1. **Havok Collision** - Rigid body physics for objects and characters (embedded in NIF)
2. **HDT-SMP** - Skinned mesh physics for cloth, hair, tails (external XML configs)

## Havok Collision (NIF-Embedded)

### Overview

Havok collision data is embedded directly in NIF files. It defines:
- Collision shapes (how objects physically interact)
- Rigid body properties (mass, friction, motion type)
- Constraints (hinges, ragdolls, etc.)

**Havok versions:**
- **Skyrim LE/SE:** hk_2010.2.0-r1 (32-bit for LE, 64-bit for SE)
- **Fallout 4:** hk_2014.1.0-r1 (64-bit, packfile format)

### Collision Block Types (Skyrim)

#### bhkCollisionObject
Top-level collision attachment to scene nodes.

**Properties:**
- Target: Which NiNode this collision belongs to
- Flags: Collision enabled/disabled
- Body reference: Points to bhkRigidBody

#### bhkRigidBody
Physics body with mass, motion, and collision shape.

**Motion types** (from Havok's `hkpMotion::MotionType` enum):
- `MO_SYS_INVALID` (0)
- `MO_SYS_DYNAMIC` (1) - Responds to forces (boxes, ragdolls, dropped items)
- `MO_SYS_SPHERE_INERTIA` (2) / `MO_SYS_SPHERE_STABILIZED` (3) - Spherical inertia approximations
- `MO_SYS_BOX_INERTIA` (4) / `MO_SYS_BOX_STABILIZED` (5) - Box inertia approximations
- `MO_SYS_KEYFRAMED` (6) - Controlled by animation/script (moving platforms, doors)
- `MO_SYS_FIXED` (7) - Static, never moves (walls, floors, world geometry)
- `MO_SYS_THIN_BOX` (8) - Thin-box optimization
- `MO_SYS_CHARACTER` (9) - Character controller

**Key properties:**
- Mass (kg) - Higher = harder to move
- Friction (0.0-1.0) - Surface drag
- Restitution (0.0-1.0) - Bounciness (0 = no bounce, 1 = perfectly elastic)
- Linear damping - Slows down movement
- Angular damping - Slows down rotation
- Max linear velocity - Speed cap
- Max angular velocity - Rotation speed cap
- Gravity factor - Multiplier for gravity (1.0 = normal, 0.0 = weightless)

**Layer/Filter:**
- Collision layer - What category this object belongs to
- Collision filter - Which layers it collides with

#### bhkRigidBodyT
Variant of `bhkRigidBody` with a built-in transform (translation + rotation) baked into the body itself. Used (in both Skyrim and FO4) when the collision body needs to sit at an offset from its target node without an intermediate NiNode. The "T" stands for "transform," not Fallout-specific.

### Collision Shapes

#### bhkBoxShape
Rectangular box collision.

**Properties:**
- Dimensions: Half-extents (X, Y, Z)
- Material: Surface type (stone, wood, flesh, etc.)

**Use cases:** Crates, walls, furniture

#### bhkSphereShape
Spherical collision.

**Properties:**
- Radius: Distance from center
- Material: Surface type

**Use cases:** Balls, heads, simple round objects

#### bhkCapsuleShape
Cylinder with hemispherical ends (pill shape).

**Properties:**
- Point 1, Point 2: Endpoints of central axis
- Radius 1, Radius 2: Radii at each end (usually same)
- Material: Surface type

**Use cases:** Arms, legs, tails, rope, staves

#### bhkConvexVerticesShape
Convex hull defined by vertices.

**Properties:**
- Vertices: List of 3D points
- Normals: Surface normals
- Material: Surface type

**Constraints:**
- Must be **convex** (no indentations)
- Max 255 vertices (practical limit ~64 for performance)

**Use cases:** Simple organic shapes, rocks

#### bhkMoppBvTreeShape
Mesh collision using Memory-Optimized Partial Polytope Bounding Volume Tree.

**Structure:**
- Contains multiple sub-shapes (triangles)
- Pre-computed acceleration structure for fast collision queries

**Use cases:** Complex static meshes (architecture, terrain)

**Warning:** Expensive for moving objects - use simpler shapes when possible.

#### bhkListShape
Container for multiple collision shapes.

**Use cases:** Combining shapes (e.g., multiple boxes for furniture)

### Havok Materials

Material types affect friction and sound:
- HAV_MAT_STONE
- HAV_MAT_WOOD
- HAV_MAT_METAL
- HAV_MAT_FLESH
- HAV_MAT_CLOTH
- HAV_MAT_SKIN (for creatures)
- HAV_MAT_DRAGON
- (many more...)

Each material has default friction/restitution values.

### Fallout 4 Physics

FO4 replaces Skyrim's per-block collision graph (`bhkRigidBody` + shape blocks) with
a **Havok packfile** — a serialized blob of the newer `hknp` ("Havok Physics, new")
runtime objects — embedded in the NIF.

**Key differences from Skyrim:**

- A NIF node carries a **`bhkNPCollisionObject`** (not `bhkCollisionObject`).
- The actual physics lives in a **`bhkPhysicsSystem`** block whose payload is a raw
  Havok packfile (`hk_2014.1.0`, 64-bit).
- Collision shapes are encoded inside the packfile, not as NIF blocks.
- Material/simulation properties are stored as **truncated float16** (the upper 16
  bits of a 32-bit float taken as a `uint16`).

#### Packfile contents

The packfile begins with an `hknpPhysicsSystemData` followed by **N rigid bodies**
and their shape objects. Shape types seen in vanilla:

| Shape | Meaning |
|-------|---------|
| `hknpConvexPolytopeShape` | A convex hull (vertices + face planes). |
| `hknpCompressedMeshShape` | A triangle mesh (quantized), for static geometry. |
| `hknpSphereShape` | A sphere (radius; centre in the body info). |
| `hknpDynamicCompoundShape` | **One body** whose shape is a *compound* of many child shapes with per-instance transforms (see below). |

#### bhkNPCollisionObject.bodyID — the body index

A `bhkNPCollisionObject` has a **`bodyID`** that indexes into its physics system's
body array — it selects *which* body in the shared system belongs to this NIF node.
Several nodes can share one physics system, each pointing at a different body (e.g.
`BOSRadarDish` has a `Main` node and a `Swivel` node sharing one system, `bodyID` 0
and 1).

!!! danger "Unset bodyID crashes the game"
    If a tool writes a `bhkNPCollisionObject` without setting `bodyID` (leaving the
    default sentinel `0xFFFFFFFF`), the engine indexes the body array out of bounds
    and dies on cell load in **`bhkNPCollisionObject::CreateInstance`**. A single-body
    system must use `bodyID = 0`.

#### hknpDynamicCompoundShape (compound bodies)

Furniture with lots of collision detail — the armor / weapons / cooking **workbenches**,
for instance — uses a single rigid body whose shape is an `hknpDynamicCompoundShape`:
a container of *N* child shapes (typically convex polytopes), each placed by an
**instance transform** (rotation + translation). The armor workbench is one body
holding **36** convex polytopes.

Crucially, the compound also owns a **bounding-volume BVH tree**, stored as a separate
`hknpDynamicCompoundShapeData` object the compound points to. The tree is an AABB
hierarchy over the child shapes (the armor bench's is 73 nodes over 36 leaves). The
engine walks it while building the compound's bounds.

!!! danger "A compound with no BVH tree crashes updateAabb"
    A regenerated compound that omits the `hknpDynamicCompoundShapeData` tree (or leaves
    a dangling pointer where it belongs) crashes on load in
    **`hknpDynamicCompoundShape::updateAabb`**. The tree is a spatial function of the
    child shapes' positions, so it must be rebuilt whenever they move. The pragmatic
    workaround for unmodified collision is to **preserve the original packfile bytes
    verbatim** rather than regenerate.

*Unconfirmed:* the shape base field `hknpShape::m_userData` (a `uint64`) holds a value
that is **shared across a compound and all its child shapes** within one file and
differs per file. The engine appears not to interpret it, but a compound and its
children should carry the same value (as vanilla does).

#### The FO4 furniture-collision crash chain

Malformed FO4 collision (e.g. from a third-party tool re-exporting a workbench) tends
to fail as a *sequence* of access-violation crashes on cell load — each one masks the
next, so fixing one reveals another:

1. **`BSSkin::Instance::UpdateModelBound`** — a static shape was given a *skin instance
   with zero bones*. In a furniture NIF that mixes a skinned mesh with static
   decoration, a shape with no bone weights must **not** be skinned; a zero-bone skin
   instance is a null the engine dereferences.
2. **`bhkNPCollisionObject::CreateInstance`** — `bodyID` unset / out of range (above).
3. **`hknpDynamicCompoundShape::updateAabb`** — compound missing its BVH tree (above).

Reading the faulting function name from an F4SE crash logger (e.g. Buffout/Addictol)
tells you exactly which layer failed.

#### Packfile binary format

The `bhkPhysicsSystem` payload is a standard Havok `hkPackfile` (`hk_2014.1.0-r1`,
64-bit little-endian). All offsets below were derived by decoding vanilla FO4 files.

**Global header (0x40 bytes):**

| Offset | Size | Field | Value |
|--------|------|-------|-------|
| 0x00 | 8 | magic | `57 E0 E0 57 10 C0 C0 10` |
| 0x0C | 4 | fileVersion | 11 |
| 0x10 | 4 | layoutRules | `08 01 00 01` (ptrSize=8, LE) |
| 0x14 | 4 | numSections | 3 |
| 0x18 | 4 | contentsSectionIndex | 2 (the data section) |
| 0x24 | 4 | contentsClassNameOffset | offset of `hknpPhysicsSystemData` in classnames |
| 0x28 | 18 | contentsVersion | `hk_2014.1.0-r1\0\xFF` |

**Three section headers** (0x40 bytes each, at 0x40/0x80/0xC0): `__classnames__`,
`__types__` (empty in FO4), `__data__`. Each header: `char name[20]` (0xFF-padded),
then `u32 absStart, localFixup, globalFixup, virtualFixup, exports, imports, end`
(the fixup/exports fields are *relative to absStart*). `__types__` is empty; the real
content is `__data__`.

**Classnames section** — a sequence of `{u32 hash; u8 0x09; char name[] (null-term)}`,
padded to 16 bytes with 0xFF. Useful hashes:

| Hash | Class |
|------|-------|
| `0xB857718B` | `hknpPhysicsSystemData` |
| `0x3CE9B3E3` | `hknpConvexPolytopeShape` |
| `0x4620D11C` | `hknpDynamicCompoundShape` |
| `0xF33DC3CC` | `hknpDynamicCompoundShapeData` |
| `0x7C574867` | `hkRefCountedProperties` |
| `0xE9191728` | `hknpShapeMassProperties` |

**Fixup tables** follow the data objects, in order (terminated by `0xFFFFFFFF`):

- **Local** (`{u32 src, u32 dst}`): pointer within the same section (e.g. an `hkArray`
  header → its data).
- **Global** (`{u32 src, u32 dstSection, u32 dst}`): pointer between sections (e.g. a
  body's shape pointer → the shape object).
- **Virtual** (`{u32 objOffset, u32 section, u32 classNameOffset}`): tags each object
  in `__data__` with its class (this is how you enumerate the objects).

**`hkArray` (16 bytes)**, used throughout: `u64 ptr` (patched by a local fixup),
`u32 size`, `u32 capacityAndFlags` (= `size | 0x80000000`).

##### Data section

Begins with an `hknpPhysicsSystemData` (PSD, 0x80 bytes) — six `hkArray` slots + pad.
The member names below are the Havok SDK's; older notes called these `body_props`,
`dyn_motion`, `dyn_inertia` and `ShapeEntry`, which obscures what they do:

| Slot @ | Array | Element | Count |
|--------|-------|---------|-------|
| 0x10 | `materials` | `hknpMaterial`, **0x50** | num_bodies |
| 0x20 | `motionProperties` | `hknpMotionProperties`, **0x40** | see below |
| 0x30 | `motionCinfos` | `hknpMotionCinfo`, **0x70** | number of *dynamic* bodies |
| 0x40 | `bodyCinfos` | `hknpBodyCinfo`, **0x60** | num_bodies |
| 0x50 | `constraintCinfos` | | 0 in static collision |
| 0x60 | `referencedObjects` | **pointer, 0x08** | num_bodies |
| 0x70 | `name` | `hkStringPtr` | |

> **`referencedObjects` has an 8-byte stride, not 16.** It is
> `hkArray<Ptr<hkReferencedObject>>` — one bare pointer per entry, not the 16 bytes an
> `hkArray` element usually takes. Writing it at 16 leaves every entry after the first
> null, and the engine then reads a null shape for bodies 1..N-1 and stores through it
> in `bhkNPCollisionObject::CreateInstance` while loading the cell. Body 0 sits at
> offset 0 either way, so single-body collision works and multi-body collision does not.

Rules measured across 1500 vanilla systems, all holding 1500/1500:

- `materials` count **equals** the body count, and body *i* uses material *i*.
- `motionCinfos` count **equals the number of dynamic bodies**, and their `motionId`s
  are `0 .. n-1` in body order.
- `referencedObjects` count equals the body count. Body *i*'s `bodyCinfos[i].shape` and
  `referencedObjects[i]` point at the **same** shape.

**`hknpBodyCinfo` (0x60):**

| Offset | Field |
|--------|-------|
| 0x00 | `shape` pointer (global fixup) |
| 0x08 | `reservedBodyId` (`0x7FFFFFFF`) |
| 0x0C | **`motionId`** — index into `motionCinfos`, or `0x7FFFFFFF` for a static body |
| 0x10 | `qualityId` (u8, `0xFF`) |
| 0x12 | **`materialId`** (u16) — index into `materials`; vanilla always uses the body's own index |
| 0x14 | **`collisionFilterInfo`** (u32) — the layer this body collides on |
| 0x18 | `flags` (i32) / 0x1C `collisionLookAheadDistance` |
| 0x20 | `name` / 0x28 `userData` |
| **0x30** | **`position`** (`hkVector4`) |
| **0x40** | **`orientation`** (`hkQuaternionf`, x y z w) |

> **`position` places the body**, it is not only centre-of-mass metadata. Over 400
> vanilla bodies carrying a transform: 288 are zero, 27 sit near the vertex centroid,
> and **84 are a genuine placement unrelated to the geometry**. Several bodies commonly
> share one local mesh sitting at the origin and are separated by this field alone, so
> discarding it stacks them all in one spot.

A body is **dynamic exactly when it references a motionCinfo**. Writing a dynamic
`motionId` without also writing that record — or the reverse — produces a body the
engine cannot instantiate.

**`hknpMotionCinfo` is 112 bytes (0x70)**, not 64: `motionPropertiesId` (u16) at 0x00,
`inverseMass` 0x04, `massFactor` 0x08, `inverseInertiaLocal` 0x20,
`centerOfMassWorld` 0x30, **`orientation` 0x40, `linearVelocity` 0x50,
`angularVelocity` 0x60**. Truncating it at 0x40 makes the engine read the next record
as this one's velocities.

**`motionPropertiesId`** indexes the system's own `motionProperties` array, or is
`0xFFFF` for "none" — which is what every vanilla record holds when the array is absent
(131/131 measured), leaving the engine to apply defaults. Note the FO4 runtime *also*
defines `hknpMotionPropertiesId::Preset` — `STATIC=0, DYNAMIC=1, KEYFRAMED=2,
FROZEN=3, DEBRIS=4` — but those are ids in the runtime `hknpMotionPropertiesLibrary`
after registration, **not** values found in a packfile. Don't conflate the two.

Material/simulation params in `hknpMaterial` use **truncated float16** — the upper 16
bits of a float32 as a `uint16` (`dynamicFriction` at +0x12, `restitution` at +0x16):

```python
decode = struct.unpack('<f', struct.pack('<I', u16 << 16))[0]
encode = struct.unpack('<I', struct.pack('<f', value))[0] >> 16
```

##### Shape objects

All `hknp` shapes share a base header from `hknpShape`: `+0x10` flags (u16),
**`+0x12` `numShapeKeyBits` (u8)**, `+0x13` `dispatchType`, `+0x14` convex radius
(float), **`+0x18` `m_userData` (u64)**, `+0x20` `properties`.

> **`numShapeKeyBits` is per shape and must be right.** It tells the engine how many
> bits of a shape key belong to this shape. For a compressed mesh it equals the shape
> data's `bitsPerKey` (700/700 vanilla shapes); for an `hknpDynamicCompoundShape` it is
> `numInstances.bit_length()` (1200/1200). Both are the same rule — enough bits to
> cover the largest key the shape can hand out, plus one. A fixed value makes the engine
> resolve a primitive the shape never wrote, and it then walks off the end of it inside
> `hknpCompressedMeshShape::getLeafShapes` — a *query-time* crash, so the cell loads and
> the game dies a minute later when something comes near.

A composite shape (`hknpCompositeShape`, the base of both the compressed mesh and the
compound) adds:

| Offset | Field |
|--------|-------|
| 0x30 | `edgeWeldingMap.secondaryKeyMask` = `0xFFFFFFFF` |
| 0x34 | `edgeWeldingMap.secondaryKeyBits` = 0 |
| 0x38 | `edgeWeldingMap.primaryKeyToIndex` — `hkArray<u16>`, empty; capacity word at 0x44 still carries `DONT_DEALLOCATE` (0x80000000) |
| 0x48 | `edgeWeldingMap.valueAndSecondaryKeys` — `hkArray<u16>`, empty; capacity word at 0x54 = 0x80000000 |
| 0x58 | `shapeTagCodecInfo` (u32) = **`0xFFFFFFFF`** in 500/500 vanilla shapes |

`m_userData` holds one value
**shared by a compound and all its child shapes** in a file, differing per file
(armor bench `0x064003D4`, weapons bench `0x2A1A6690`, stove `0xB26A84C5`); the engine
seems to ignore it but a compound and its children must agree.

- **`hknpConvexPolytopeShape`** (variable): 0x30 header, then `u16 numVerts, vertsOff`
  at 0x30; `u16 numVerts2, planesOff, numPlanes, facesOff, numFVI, fviOff` at 0x40;
  then `vertices[]` (16 bytes: `float x,y,z; u32 w = 0x3F000000 | (index&0xFF)`),
  `planes[]` (16 each), a 28-byte gap, `faces[]` (`u16 firstFVI; u8 numVtx; u8 flags`),
  gap, `fvi[]` (1 byte each), padded to 8.
- **`hknpSphereShape`** (0x50): `+0x14` radius (float, Havok space). Centre is in the
  body's BodyCInfo, not the shape.
- **`hknpCompressedMeshShape`** (0xC0) + a ShapeData object: quantized triangle mesh.
  See the section below — it needs more than its geometry to load.

##### hknpCompressedMeshShape + ShapeData

The shape object (0xC0) carries the composite header above plus a pointer to its data
at `+0x60` and **two `hkBitField`s the engine reads while querying the shape**:
`quadIsFlat` at `+0x68` (count `ceil(u78/32)` words, `u78` at `+0x78` = `(maxKey+2)/2`)
and `triangleIsInterior` at `+0x80` (count `ceil(u90/32)`, `u90` at `+0x90` =
`maxKey+1`). Leaving either empty is an access violation in `getLeafShapes`. Vanilla
clears `quadIsFlat` for all 16448 degenerate quads it ships and leaves
`triangleIsInterior` clear ~87% of the time. Words past the declared bit count are
uninitialised garbage — don't read meaning into them.

**`hknpCompressedMeshShapeData` is 0xD0 bytes.** `meshTree` starts at 0x10:

| Offset | Field |
|--------|-------|
| 0x10 | `meshTree.nodes` — `hkArray<Codec3Axis5>`, the **top-level BVH over sections** (2N-1 nodes for N sections) |
| 0x20 / 0x30 | `domain` AABB min / max |
| 0x40 | `numPrimitiveKeys` (i32) = triangle count |
| 0x44 | `bitsPerKey` (i32) = `(maxKeyValue + 1).bit_length()` |
| 0x48 | `maxKeyValue` (u32) |
| 0x50 | `sections` — `hkArray`, **0x60** each |
| 0x60 | `primitives` — the quads, 4×u8 indices |
| 0x70 | `sharedVerticesIndex` — `hkArray<u16>` |
| 0x80 | `packedVertices` — `hkArray<u32>` |
| 0x90 | `sharedVertices` — `hkArray<u64>` |
| 0xA0 | `primitiveDataRuns` |
| 0xB0 | `simdTree` (`hkcdSimdTree`; its `nodes` array is at 0xB8, count at 0xC0) |

**Section (0x60):** `nodes` `hkArray<Codec3Axis4>` at 0x00 (this section's own BVH),
`domain` AABB at 0x10/0x20, `codecParms` at 0x30 (base xyz then scale xyz),
`firstPackedVertex` 0x48, `(firstSharedIndex << 8) | numPackedVertices` at 0x4C,
`(firstQuad << 8) | numQuads` at 0x50, `numPackedVertices` 0x58, `numSharedIndices`
0x59, `leafIndex` (u16, into the top-level tree) 0x5A, `flags` 0x5D.

Vertices are 11-11-10-bit packed against the **section's own** AABB:
`qx=(v>>0)&0x7FF, qy=(v>>11)&0x7FF, qz=(v>>22)&0x3FF`, then
`x = section.base_x + qx*section.scale_x`. Primitives are **quads**, not triangles:
`(a,b,c,d)` is one triangle when `d == c`, otherwise two. Shared vertices (indices
`>= numPackedVertices`) are 21-21-22-bit packed against the **shape's** AABB.

**Per-section limits:** at most **127 quads** — a tree leaf stores its primitive as
`index * 2` in a byte — and 255 vertices. A mesh larger than that is split across
sections, each quantized against its own bounding box.

**Primitive keys** are `(sectionIndex << 8) | (localQuadIndex << 1) | triangleInQuad`.
So `maxKeyValue` comes from the **last section's last quad**, not from a global quad
count: `((numSections-1) << 8) | ((lastSectionQuads-1) << 1) | lastTriFlag`. Computing
it globally is identical for one section and badly wrong for many — it truncates
`bitsPerKey`, the engine decodes a bogus section index, and you get an access violation
while moving around (the file still *loads*).

**The BVH is required.** Writing the tree arrays empty makes `hkNativePackfileUtils::load`
walk a null pointer inside `hkcdStaticMeshTree`. Both levels quantize a node's AABB
against its **parent's decompressed** box, 4 bits per bound per axis, on a square curve:

```
min[i] = (hi_nibble^2 / 226) * parent_span + parent_min
max[i] = parent_max - (lo_nibble^2 / 226) * parent_span
```

Compression floors the nibbles, so a decoded box always *contains* the true box. Re-decompress
after compressing each node and use that as the child's reference, or drift accumulates.

- **`Codec3Axis4`** (4 bytes, per-section trees): three axis bytes then a data byte.
  Even → leaf, `primitive = data >> 1`. Odd → internal, `left = i + 1`,
  **`right = i + (data & 0xFE)`** — the offset is stored directly, not shifted.
- **`Codec3Axis5`** (5 bytes, the top-level tree): three axis bytes, then `hiData`,
  `loData`. Bit 7 of `hiData` set → internal and `(hiData<<8 | loData) & 0x7FFF` is
  *half* the offset to the right child; clear → leaf holding the section index. The
  **root node's axis bytes are zeroed**.

**`simdTree`** is a fixed constant, not something to build: every vanilla compressed mesh
— a one-quad floor through the 123-section Diamond City ground — carries exactly **two
empty `hkcdSimdTreeNode`s**. A node is **112 bytes** (an `hkcdFourAabb`: lo/hi bounds as
six 4-wide vectors, plus four link words); empty means lo lanes `0x7F7FFFEE` (+FLT_MAX),
hi lanes `0xFF7FFFEE` (-FLT_MAX), links zero. Declaring two nodes with less than 224
bytes behind them sends `hkcdSimdTree::rayCast` off the buffer.

##### Double-sided collision

A collision surface is made solid from **both** sides by carrying the same triangle
twice, wound opposite ways — `(0,1,2)` and `(2,1,0)`. 41 of 920 sampled vanilla
collision shapes do this; 12 also carry genuine same-winding repeats.

This matters for any tool that round-trips collision through a mesh editor. Blender
cannot hold two faces on one set of vertex indices *whatever their winding*
(`mesh.validate()` deletes the second regardless), so a naive importer that
deduplicates on the sorted indices treats a back face as a duplicate and silently makes
the wall one-sided. The fix is to give the repeat its own copy of the vertices; the
sharing is only Havok's space optimization.

##### hknpDynamicCompoundShape (0xD0) + instances + BVH tree

One body whose shape is a compound of N children. The compound object is **0xD0 bytes**
(the region past the usual 0x30 header carries its own AABB and a tree pointer):

| Offset | Field |
|--------|-------|
| 0x10 | flags — `0x02060004` (armor/weapons benches), `0x02040004` (11-leaf stove); *likely tree size/depth* |
| 0x18 | `m_userData` (shared with children) |
| 0x30 | `0xFFFFFFFF` sentinel |
| 0x40, 0x50 | empty `hkArray`s |
| 0x60 | **instances** `hkArray` (`ptr` via local fixup, `size = N`) |
| 0x80 | AABB min (`float x,y,z,w`, Havok space) |
| 0x90 | AABB max (`float x,y,z,w`) |
| 0xC0 | `u64 ptr` (global fixup) → `hknpDynamicCompoundShapeData` |

**Instance (0x80 each):** rotation stored **column-major** as three `vec3`s at
`+0x00/+0x10/+0x20` (with constant w-lanes 0.5/0.0/0.5), translation `vec3` at `+0x30`
(Havok units), `(1,1,1,1)` at `+0x40`, and the child **shape pointer at `+0x50`**
(global fixup → an `hknpConvexPolytopeShape`), `0xFFFFFFFF` at `+0x58`.

**`hknpDynamicCompoundShapeData`** holds an **AABB bounding-volume tree** (BVH) over the
children — armor bench: **73 nodes / 32 bytes each over 36 leaves**. Node layout:
`aabb_min (vec3)` at `+0x00`, `aabb_max (vec3)` at `+0x10`, and `u16 link_a, link_b`
at `+0x1C` (child/leaf references — link encoding not fully decoded). The engine walks
this tree in `hknpDynamicCompoundShape::updateAabb` at load; it is a spatial function
of the child positions, so a parser that *edits* shape positions must rebuild it (or
preserve the original bytes). *Note:* the Skyrim MOPP BVH is a related AABB-tree problem
and a likely reference for a builder.

A reference implementation of the full read/write path lives in the PyNifly project
(`pyn/bhk_autounpack.py`, `pyn/bhk_autopack.py`, and `docs/fo4_havok_packfile_format.md`).

**Common issue:** FO4 collision is more finicky to edit than Skyrim's — prefer the
Creation Kit's Havok export, copying collision from a working example, or a tool that
preserves the original packfile bytes when the collision geometry is unchanged.

## HDT-SMP (Skinned Mesh Physics)

### Overview

`[Skyrim]` HDT-SMP (Skinned Mesh Physics) adds dynamic cloth/hair/tail physics using external XML configuration files. The system simulates bones as spring-connected masses that respond to movement and collisions. There is no equivalent in Fallout 4.

**SKSE Plugin:** HDT-SMP.dll (required at runtime)  
**Config location:** `Data/SKSE/Plugins/hdtSkinnedMeshConfigs/*.xml`  
**Mesh markers:** NiStringExtraData "HDT" in NIF points to XML config

**Use cases:**
- Hair
- Capes, cloaks, scarves
- Tails
- Breast/butt physics
- Dangling accessories

### XML Configuration Structure

```xml
<?xml version="1.0" encoding="utf-8"?>
<system>
    <!-- Collision meshes MUST come first -->
    <per-triangle-shape name="VirtualGround">
        <margin>5</margin>
        <prenetration>1</prenetration>
        <tag>ground</tag>
    </per-triangle-shape>
    
    <!-- Bone definitions -->
    <bone name="TailBone01">
        <inertia x="0" y="0" z="0"/>
        <mass>5</mass>
        <linearDamping>0.5</linearDamping>
        <angularDamping>0.5</angularDamping>
        <gravityFactor>1</gravityFactor>
        
        <!-- Bone collision shape -->
        <capsule-shape>
            <margin>5</margin>
            <radius>2</radius>
            <length>15</length>
        </capsule-shape>
        
        <!-- Constraints -->
        <constraint>
            <stiffness>10</stiffness>
            <maxAngle>45</maxAngle>
        </constraint>
    </bone>
    
    <!-- More bones... -->
</system>
```

### Critical: Collision Mesh Order

**BLOCKING REQUIREMENT:** `<per-triangle-shape>` collision meshes **MUST** be defined **BEFORE** any `<bone>` elements.

**Wrong (causes collision failure):**
```xml
<system>
    <bone name="TailBone01">...</bone>  <!-- Defined first -->
    <per-triangle-shape name="VirtualGround">...</per-triangle-shape>  <!-- Too late! -->
</system>
```

**Correct:**
```xml
<system>
    <per-triangle-shape name="VirtualGround">...</per-triangle-shape>  <!-- First! -->
    <bone name="TailBone01">...</bone>  <!-- After collision -->
</system>
```

**Symptom if wrong:** Physics bones clip through ground despite correct mesh geometry.

### Per-Triangle Collision

Defines collision meshes that physics bones interact with.

#### VirtualGround
Prevents physics from clipping through the ground.

**Configuration:**
```xml
<per-triangle-shape name="VirtualGround">
    <margin>5</margin>
    <prenetration>1</prenetration>
    <tag>ground</tag>
</per-triangle-shape>
```

**Requirements:**
- Must be NiTriShape named "VirtualGround" in NIF
- Weighted to `NPC Root [Root]` bone
- Horizontal plane at character's feet

**Properties:**
- `margin` - Collision boundary thickness (5 = default)
- `prenetration` - How much to push back when penetrating (1 = default)
- `tag` - Identifier (use "ground" for floor collision)

**Known issue:** VirtualGround rotates with NPC Root during ragdoll, which can affect nearby living characters.

#### BodyCollision
Defines collision with body mesh for cloaks/clothing.

**Configuration:**
```xml
<per-triangle-shape name="BodyCollision">
    <margin>3</margin>
    <prenetration>0.5</prenetration>
</per-triangle-shape>
```

**Requirements:**
- NiTriShape in NIF (simplified body mesh)
- Lower poly than render mesh for performance

### Bone Configuration

Each physics bone needs:

#### Physical Properties

**Mass:**
```xml
<mass>5</mass>
```
- Higher = harder to move, more momentum
- Typical: 1-10 (hair lighter, tails heavier)

**Damping:**
```xml
<linearDamping>0.5</linearDamping>
<angularDamping>0.5</angularDamping>
```
- Controls how quickly movement slows down
- Higher = stops faster, less swing
- Range: 0.0-1.0
- Typical: 0.3-0.7

**Gravity:**
```xml
<gravityFactor>1</gravityFactor>
```
- Multiplier for gravity effect
- 1 = normal gravity, 0 = weightless, 2 = double gravity

**Inertia:**
```xml
<inertia x="0" y="0" z="0"/>
```
- Resistance to rotation on each axis
- Usually leave at 0 for automatic calculation

#### Collision Shape

Each bone needs a collision shape to interact with world and other bones.

**Capsule (most common):**
```xml
<capsule-shape>
    <margin>5</margin>
    <radius>2</radius>
    <length>15</length>
</capsule-shape>
```
- Cylinder with rounded ends
- Good for hair strands, tails, rope

**Sphere:**
```xml
<sphere-shape>
    <margin>5</margin>
    <radius>5</radius>
</sphere-shape>
```
- Ball shape
- Good for beads, joints, simple shapes

**Box:**
```xml
<box-shape>
    <margin>5</margin>
    <halfExtents x="5" y="5" z="5"/>
</box-shape>
```
- Rectangular box
- Good for flat cloth panels

**Margin:** Collision padding in game units. Larger = more conservative collisions.

#### Constraints

Constraints limit how bones can rotate relative to their parent.

**Basic constraint:**
```xml
<constraint>
    <stiffness>10</stiffness>
    <maxAngle>45</maxAngle>
</constraint>
```

**Stiffness:**
- How strongly bone resists bending
- Higher = stiffer, less flexible
- Range: 0-100+
- Typical: 5-20 (hair), 10-40 (tails), 50+ (rigid cloth)

**MaxAngle:**
- Maximum angle bone can bend from rest position (degrees)
- Smaller = more restricted movement
- Typical: 30-60 degrees

**Cone constraint (advanced):**
```xml
<constraint>
    <stiffness>10</stiffness>
    <coneAngle>30</coneAngle>
    <twistAngle>15</twistAngle>
</constraint>
```
- `coneAngle` - Side-to-side bend limit
- `twistAngle` - Rotation around bone axis

### Mesh Weight Requirements

**Critical for tails:** Root tail bone (e.g., TailBone01) should **NOT** be weighted to any tail bones in the mesh. Weighting should skip the first physics bone.

**Example weighting (female feline tail):**
- Tail root mesh → Weighted to NPC Pelvis [Pelv] or NPC Spine2 [Spn2]
- Mid-tail mesh → Weighted to TailBone02, TailBone03, etc.
- **NOT** → TailBone01 (first physics bone stays unweighted)

**Reason:** Prevents fighting between skeleton animation and physics simulation.

### Common Configurations

#### Hair Physics
```xml
<bone name="HairBone01">
    <mass>1</mass>
    <linearDamping>0.5</linearDamping>
    <angularDamping>0.5</angularDamping>
    <gravityFactor>0.8</gravityFactor>
    
    <capsule-shape>
        <margin>3</margin>
        <radius>1</radius>
        <length>10</length>
    </capsule-shape>
    
    <constraint>
        <stiffness>5</stiffness>
        <maxAngle>45</maxAngle>
    </constraint>
</bone>
```

**Key values:**
- Light mass (1)
- Moderate damping (0.5)
- Slightly reduced gravity (0.8)
- Flexible stiffness (5)

#### Tail Physics
```xml
<bone name="TailBone02">
    <mass>5</mass>
    <linearDamping>0.3</linearDamping>
    <angularDamping>0.3</angularDamping>
    <gravityFactor>1</gravityFactor>
    
    <capsule-shape>
        <margin>5</margin>
        <radius>3</radius>
        <length>20</length>
    </capsule-shape>
    
    <constraint>
        <stiffness>15</stiffness>
        <maxAngle>40</maxAngle>
    </constraint>
</bone>
```

**Key values:**
- Heavier mass (5)
- Lower damping for more swing (0.3)
- Normal gravity (1.0)
- Moderate stiffness (15)

#### Cape/Cloak Physics
```xml
<bone name="CapeBone01">
    <mass>3</mass>
    <linearDamping>0.6</linearDamping>
    <angularDamping>0.6</angularDamping>
    <gravityFactor>1</gravityFactor>
    
    <box-shape>
        <margin>5</margin>
        <halfExtents x="10" y="2" z="15"/>
    </box-shape>
    
    <constraint>
        <stiffness>20</stiffness>
        <maxAngle>35</maxAngle>
    </constraint>
</bone>
```

**Key values:**
- Moderate mass (3)
- Higher damping for cloth behavior (0.6)
- Box shape for flat panels
- Higher stiffness (20)

### NIF Requirements

For HDT-SMP to work, the NIF must have:

1. **NiStringExtraData "HDT"**
   - Attached to scene root or skeleton root
   - String value: Path to XML config (e.g., "hdtSkinnedMeshConfigs/MyTail.xml")

2. **Physics bones in skeleton**
   - Bones referenced in XML must exist as NiNode in NIF
   - Proper parent-child hierarchy

3. **Mesh skinned to physics bones**
   - Vertices weighted to physics bones
   - Max 4 bones per vertex

4. **Collision meshes (if used)**
   - VirtualGround: NiTriShape at ground level
   - BodyCollision: Simplified body mesh

### Debugging Physics Issues

**Symptoms:** Physics not working, clipping through ground, jittery movement

**Checklist:**
1. ✅ HDT-SMP.dll installed and enabled
2. ✅ XML config in correct location
3. ✅ NIF has NiStringExtraData "HDT" pointing to XML
4. ✅ Collision meshes defined **before** bones in XML
5. ✅ `<prenetration>` spelled correctly (not "penetration")
6. ✅ Bone names in XML match bone names in NIF exactly
7. ✅ VirtualGround mesh exists and is named correctly
8. ✅ VirtualGround weighted to NPC Root [Root]
9. ✅ Physics bones exist in skeleton hierarchy
10. ✅ Mesh vertices actually weighted to physics bones

**Common mistakes:**
- Defining collision meshes after bones → Move to top of XML
- Using `<penetration>` instead of `<prenetration>` → Fix tag name
- Misspelled bone names → Check exact capitalization and spacing
- VirtualGround not weighted → Paint weights to NPC Root [Root]
- FSMP MCM auto-reset causing crashes → Disable FSMP MCM

See [Physics Issues Debugging](../debugging/physics-issues.md) [TBD] for more troubleshooting.

## Tools

**NifSkope:** View/edit Havok collision blocks in NIFs

**PyNifly:** Export NIFs with collision from Blender
```python
from pyn import pynifly

nif = pynifly.NifFile('mesh.nif')
# Check for collision
for node in nif.nodes.values():
    if 'bhk' in node.blockname:
        print(f"Collision block: {node.blockname}")
```

**Creation Kit:** Generate Havok collision for objects (PhysX → Havok export)

**HDT-SMP Visualizer:** In-game debug mode (shows collision shapes, bone connections)

**SSEEdit/FO4Edit:** Check FormID references to physics-enabled meshes in plugins

## See Also

- [NIF Files](nif-files.md) - bhkCollisionObject and physics block structure
- [Mesh Workflows](../workflows/physics-collisions.md) [TBD] - Setting up physics in Blender
- [Physics Debugging](../debugging/physics-issues.md) [TBD] - Troubleshooting collision issues
