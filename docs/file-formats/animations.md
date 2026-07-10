# Animations (HKX Files)

HKX files contain skeleton hierarchies and compressed animation data for Bethesda games. They use Havok's proprietary binary format.
- [Animations (HKX Files)](#animations-hkx-files)
  - [Overview](#overview)
  - [File Types](#file-types)
    - [Skeleton Files](#skeleton-files)
    - [Animation Files](#animation-files)
    - [Behavior Files](#behavior-files)
  - [Skeleton Structure](#skeleton-structure)
    - [Wire format](#wire-format)
    - [Object inventory](#object-inventory)
    - [Object graph](#object-graph)
    - [Animation skeleton (`hkaSkeleton`)](#animation-skeleton-hkaskeleton)
    - [How variable-length data is stored on disk](#how-variable-length-data-is-stored-on-disk)
    - [Bone Naming Convention](#bone-naming-convention)
    - [Required Bones (Skyrim)](#required-bones-skyrim)
    - [Bone Transform Data](#bone-transform-data)
    - [Ragdoll Data](#ragdoll-data)
  - [XML Representation](#xml-representation)
    - [Section folding (reversible)](#section-folding-reversible)
    - [Float precision (irreversible)](#float-precision-irreversible)
    - [When XML is and isn't appropriate](#when-xml-is-and-isnt-appropriate)
  - [Animation Data](#animation-data)
    - [Keyframe Structure](#keyframe-structure)
    - [Compression](#compression)
      - [Track structure per bone](#track-structure-per-bone)
      - [Time blocking](#time-blocking)
      - [How spline fitting loses information](#how-spline-fitting-loses-information)
      - [Bit quantization (additional loss)](#bit-quantization-additional-loss)
      - [Continuous sampling at runtime](#continuous-sampling-at-runtime)
      - [Worked example](#worked-example)
      - [Tunable tolerance](#tunable-tolerance)
      - [Re-export compounding](#re-export-compounding)
      - [Best practice](#best-practice)
    - [Annotation Tracks](#annotation-tracks)
    - [Animation Blending](#animation-blending)
  - [`FO4` Fallout 4 Differences](#fo4-fallout-4-differences)
    - [64-bit Havok](#64-bit-havok)
    - [FaceBones System](#facebones-system)
    - [Skin Bones](#skin-bones)
  - [Tools](#tools)
    - [PyNifly (Blender Addon)](#pynifly-blender-addon)
    - [Havok Content Tools (HCT)](#havok-content-tools-hct)
    - [hkxpack / hkxcmd](#hkxpack--hkxcmd)
    - [NifSkope](#nifskope)
    - [Creation Kit](#creation-kit)
  - [Workflow Tips](#workflow-tips)
    - [Creating Custom Skeletons](#creating-custom-skeletons)
    - [Creating Animations](#creating-animations)
    - [Converting LE → SE](#converting-le--se)
    - [Converting LE/SE → FO4](#converting-lese--fo4)
  - [Common Issues](#common-issues)
    - [Animation Not Playing](#animation-not-playing)
    - [Animation Jittery/Broken](#animation-jitterybroken)
    - [Skeleton Causes CTD](#skeleton-causes-ctd)
    - [Mesh Not Following Skeleton](#mesh-not-following-skeleton)
  - [See Also](#see-also)

## Overview

**Extension:** `.hkx`  
**Format:** Havok binary (proprietary, version-specific)  
**Contains:** Skeletons, animations, ragdolls, behavior data

**Havok versions:**
- **Skyrim LE/SE:** hk_2010.2.0-r1 (32-bit for LE, 64-bit for SE)
- **Fallout 4:** hk_2014.1.0-r1 (64-bit)

**Compatibility:** HKX files are **NOT** cross-compatible between Havok versions. SE/FO4 require conversion from LE formats.

## File Types

### Skeleton Files

Define an actor's bone hierarchy, bind pose, and (in Skyrim) the bundled ragdoll. **Filename pattern:** `skeleton.hkx`, `skeleton_female.hkx`, `skeleton_beast.hkx` under `meshes/actors/<race>/character assets/`. Bone names correspond to NiNode names in the paired `skeleton.nif`. See [Skeleton Structure](#skeleton-structure) for the binary-format walkthrough and bone-level details.

### Animation Files

Define bone motion for one animation. Each animated bone is stored as up to three B-spline-compressed tracks (position, rotation, scale) with bit-quantized control points; a parallel annotation track carries event markers (`hitFrame`, `footstep`, etc.) that the behavior graph routes to sounds and scripted callbacks. **Filename pattern:** `<animname>.hkx` (e.g. `1hm_attackright.hkx`) under `meshes/actors/<race>/animations/`. See [Animation Data](#animation-data) for the format details.

### Behavior Files

Behavior graphs are the state machines that decide which animation plays at any moment for a given actor. Game code feeds runtime parameters (movement speed, equipped weapon type, attack stage, ragdoll state, etc.); the graph picks the active state, blends animations from blend trees, and handles transitions between states. Annotation events embedded in animation HKXs (`hitFrame`, `footstep`, etc.) are routed back through the graph to trigger sounds, scripted callbacks, or further state changes.

**Location:** `meshes/actors/<race>/behaviors/`

**Vanilla files:** `defaultmale.hkx` / `defaultfemale.hkx` (plus per-creature equivalents).

**Format:** Binary Havok packfile — same `.hkx` wrapper as skeletons and animations, different content type (`hkbBehaviorGraph` and related blocks). `hkxpack` / `hkxcmd` extract to readable XML for editing; Havok Content Tools is the official editor (license required).

**Modding:** Adding a new animation usually means adding a new state or transition to the behavior graph. **FNIS** and **Nemesis** are the community tools that automate this — they read each mod's animation list and patch the behavior HKX so manual XML editing isn't needed.

## Skeleton Structure

`skeleton.hkx` is a Havok packfile bundling an animation skeleton, a simplified ragdoll skeleton, and the physics bodies and constraints that wire them together. The vanilla Skyrim SE human skeleton (`meshes/actors/character/character assets/skeleton.hkx`, 85408 bytes) is used below as a worked example. The wire-format details apply to all HKX files; the object inventory and bone-level details are skeleton-specific.

### Wire format

The packfile starts with an 80-byte file header (magic, classversion, pointer size, version string `hk_2010.2.0-r1`, layout flags), followed by a section table. The file has three sections:

| # | Name | Size | Purpose |
| --- | --- | --- | --- |
| 0 | `__classnames__` | 480 bytes | Table of `(signature, name)` pairs, one per class used in the file |
| 1 | `__types__` | 0 bytes | Empty for `hk_2010.2.0-r1`; type info is identified by class name + signature against a known type registry |
| 2 | `__data__` | 84720 bytes | Object payload + fixup tables |

Each section's data is laid out as `payload | local_fixups | global_fixups | virtual_fixups | exports | imports`, with byte offsets stored in the section header. `__classnames__` and `__types__` have no fixups (classnames are literal strings; types is empty), so for those sections only the payload region has any size.

The `__data__` section's payload is 70448 bytes of object data, followed by ~3 KB of fixup tables: 567 local fixups (8 bytes each), 486 global fixups (12 bytes each), and 324 virtual fixups (12 bytes each). Each virtual fixup marks the start of one top-level object in the payload and identifies its class by pointing at a name string in `__classnames__`. So the file contains exactly **324 top-level objects** in the data section.

### Object inventory

| Class | Count | Role |
| --- | --- | --- |
| `hkRootLevelContainer` | 1 | Top-level entry point, holds 6 named variants |
| `hkaAnimationContainer` | 1 | Wraps the two skeletons |
| `hkaSkeleton` | 2 | Animation skeleton (99 bones) + ragdoll skeleton (18 bones) |
| `hkaSkeletonMapper` | 2 | Map poses between the two skeletons (one per direction) |
| `hkaRagdollInstance` | 1 | Binds the ragdoll skeleton to its physics bodies |
| `hkpPhysicsData` / `hkpPhysicsSystem` | 1 each | Physics-world wrapper |
| `hkpRigidBody` | 19 | One per ragdoll body (plus one extra for whole-actor world collision) |
| `hkpCapsuleShape` | 19 | Collision geometry, one per rigid body |
| `hkpShapeInfo` | 19 | Shape metadata, one per rigid body |
| `hkpConstraintInstance` | 34 | Wrappers around the constraint datas |
| `hkpRagdollConstraintData` | 18 | 6-DOF ragdoll joints |
| `hkpLimitedHingeConstraintData` | 16 | Single-axis hinges (elbows, knees) |
| `hkpPositionConstraintMotor` | 1 | Referenced from inside one of the constraints |
| `hkMemoryResourceContainer` | 151 | Per-bone / per-attachment resource bookkeeping |
| `hkMemoryResourceHandle` | 38 | Resource handles |

### Object graph

The 324 objects form a graph rooted at `hkRootLevelContainer`. Its `namedVariants[6]` array points at the six top-level subsystems:

```
hkRootLevelContainer
├─ "Merged Animation Container"  → hkaAnimationContainer
│                                  └─ skeletons[2] → hkaSkeleton (animation, 99 bones)
│                                                    hkaSkeleton (ragdoll,    18 bones)
├─ "Resource Data"               → hkMemoryResourceContainer (root of a tree of 151 containers)
├─ "Physics Data"                → hkpPhysicsData
│                                  └─ systems[1]    → hkpPhysicsSystem
│                                                     ├─ rigidBodies[19]    (each → hkpCapsuleShape)
│                                                     └─ constraints[17]    → hkpConstraintInstance
├─ "RagdollInstance"             → hkaRagdollInstance
│                                  ├─ rigidBodies[18]    (subset of the 19 in PhysicsSystem)
│                                  ├─ constraints[17]    (subset of the 34 instances)
│                                  └─ skeleton            → the ragdoll hkaSkeleton
├─ "SkeletonMapper"              → hkaSkeletonMapper      (one direction)
└─ "SkeletonMapper"              → hkaSkeletonMapper      (the other direction)
```

Both skeleton mappers carry the literal string `"SkeletonMapper"` as their name in `namedVariants[]` — they're distinguished only by their mapping direction (animation→ragdoll vs. ragdoll→animation), not by name.

### Animation skeleton (`hkaSkeleton`)

The animation `hkaSkeleton` object is 9600 bytes in the `__data__` section. Its fields:

- **`name = "NPC Root [Root]"`** — the skeleton's overall label
- **`parentIndices[99]`** — `int16` per bone. `-1` marks a top-level bone. The human skeleton has exactly **two top-level bones**: `NPC Root [Root]` (index 0) and `Camera3rd [Cam3]` (index 97). `Camera3rd` is the player's third-person camera anchor; on creature skeletons, only `NPC Root` is top-level. All other bones are descendants of one of these two.
- **`bones[99]`** — flat list, children always after their parent. Each entry is just `(char* name, bool lockTranslation)` — the hierarchy is encoded in `parentIndices`, not in the bone struct.
- **`referencePose[99]`** — bind-pose `hkQsTransform` per bone (translation + quaternion + scale, vec4-padded to 48 bytes for SIMD).
- **`referenceFloats[8]`** — parallel to `floatSlots`, all `0.0` in vanilla.
- **`floatSlots[8]`** — named float channels the animation system can drive. The human skeleton carries: `hkFade:AnimObjectA/B/L/R`, `hkVis:Shield`, `hkVis:NPC L MagicNode [LMag]`, `hkVis:NPC R MagicNode [RMag]`, `hkVis:Weapon`. Used to hide or fade attached props during animation. Creature skeletons typically have zero `floatSlots` — these channels exist because humanoids carry equipment that the animation system needs to show or hide.
- **`localFrames[]`** — empty (unused in vanilla).

`lockTranslation` is set on 94 of 99 bones, telling the runtime to ignore translation tracks for those bones and pin them to the rest position. Only five bones translate freely: `NPC Root`, `x_NPC LookNode`, `x_NPC Translate`, `x_NPC Rotate`, `NPC COM`. Note the `x_NPC` prefix on three of them — the engine drives those nodes directly (look-target IK, root motion) rather than through skinned-mesh rigging.

### How variable-length data is stored on disk

Pick the `hkMemoryResourceContainer` named `"NPC Spine2 [Spn2]"` (one of the 151). It's 144 bytes and lays out as:

```
+0x00..+0x10  base-class fields (vtable space, refcount)
+0x10..+0x18  char*                       name         ← stored as zero on disk
+0x18..+0x20  hkRefPtr<...>               parent       (SERIALIZE_IGNORED, zero on disk)
+0x20..+0x30  hkArray<hkRefPtr<Handle>>   resourceHandles  (16 bytes: ptr + size + cap_and_flags)
+0x30..+0x40  hkArray<hkRefPtr<Container>> children         (16 bytes: ptr + size + cap_and_flags)
+0x40..+0x60  inline "NPC Spine2 [Spn2]\0" + padding
+0x60..+0x90  children[6]   six pointers, each stored as zero on disk
```

The `name` and `children.data` pointer fields, and every slot of the children array, are stored as zero bytes on disk. They're filled in at load time using the file's fixup tables:

- A **local fixup** records `(src=+0x10, dst=+0x40)`. At load time the loader writes `(in-memory address of object) + 0x40` into the pointer field at `+0x10`, so `name` ends up pointing at the embedded ASCII string at `+0x40`.
- A **local fixup** records `(src=+0x30, dst=+0x60)`. Same mechanism patches `children.data` to point at the array start at `+0x60`.
- For each element of the array, a **global fixup** records `(src=+0x60..+0x88, target_section=__data__, target_offset=...)`. At load time each child pointer is patched to point at another `hkMemoryResourceContainer` somewhere in `__data__`.

This is why a Havok packfile can be loaded almost in-place: read the bytes into memory, walk the fixup tables, rewrite a few pointer fields per object, and the on-disk struct becomes a live in-memory struct. It's also why object sizes vary even within a single class — `hkMemoryResourceContainer` is 96, 112, or 144 bytes depending on its inline string length and inline array length, since the variable-length data is embedded right after the fixed struct header in the same allocation.

The same mechanism explains how `hkaSkeleton` packs all 99 bone-name strings, the `parentIndices` array, the `bones` array, and the `referencePose` array into a single 9600-byte allocation. The internal pointers (each `hkaBone.name`, the array bases) are zero on disk and patched at load time using local fixups.

The `dump_hkx.py` utility at the project root parses this structure and prints a per-object listing with the resolved fixups inline, including field-name labels for the well-known classes (`hkRootLevelContainer`, `hkaSkeleton`, `hkpPhysicsSystem`, `hkMemoryResourceContainer`, etc.) — so a fixup can be reported as `[bones[12].name]` or `[namedVariants[3].variant]` rather than just an offset. The offsets in this section were derived from that output.

**Notes:**
- `[FO4]` Hair with physics can have their own facebones HKX file, e.g. `FemaleHair06_faceBones.hkx`. See [FaceBones System](#facebones-system) below. Skyrim has no equivalent.
- Skirt physics bones (`SkirtRBone01-03`, `SkirtLBone01-03`, `SkirtBBone01-03`, `SkirtFBone01-03`) and pauldron bones (`NPC L Pauldron`, `NPC R Pauldron`) are part of the vanilla SE skeleton — not mod additions. XPMSSE-style skeleton replacers add other bones (chest physics for HDT, butt, wings, etc.) by extending `bones[]` and `parentIndices[]`, interspersing new bones without changing the vanilla parenting structure.

### Bone Naming Convention

The naming convention varies by actor type.

**Humanoid skeletons** (human, child, elf, orc — all share a single skeleton structure) use:

**Format:** `NPC <Side> <Part> [<Short>]`

**Examples:**
- `NPC Root [Root]` — Root bone
- `NPC L Hand [LHnd]` — Left hand
- `NPC R UpperArm [RUar]` — Right upper arm
- `NPC Pelvis [Pelv]` — Pelvis (center, no side)

**Short codes (in brackets):**
- 4-character shorthand included as part of the full bone name string
- Convention only — animations, behavior graphs, NiSkinInstance, and script `GetNodeName` all reference the full name (e.g. `"NPC Spine [Spn0]"`), not the short code independently
- Likely a holdover from Gamebryo-era tooling; useful for modders eyeballing skeletons but not parsed out by the engine

**Utility-node prefix:** A small set of bones uses `x_NPC` instead of `NPC`: `x_NPC LookNode [Look]`, `x_NPC Translate [Pos ]`, `x_NPC Rotate [Rot ]`. These are children of `NPC Root` that the engine drives directly (look-target IK, root motion) rather than being shaped by skinned-mesh rigging.

**Creature skeletons** use a simpler convention with no shortcodes and no L/R prefix as a separate token:

**Format:** `<Race>_<Part>` (`Canine_*`, `Bear_*`, `Dragon_*`, etc., capitalized to match the asset)

**Examples** (from a canine skeleton):
- `NPC Root [Root]` — the root bone keeps the humanoid form even on creature skeletons
- `Canine_COM`, `Canine_Pelvis`, `Canine_Spine1`, `Canine_Spine2`, `Canine_Spine3`
- `Canine_LFrontLeg1`, `Canine_RBackLeg1`, `Canine_Tail1`, `Canine_JawBone`, `Canine_LEar01`

The corresponding ragdoll skeleton uses a `Ragdoll_<Race>_<Part>` prefix (e.g. `Ragdoll_Canine_LBackLeg1`). The same `Ragdoll_` convention is used for the humanoid ragdoll bones — they're named `Ragdoll_NPC <Part> [<Short>]` (e.g. `Ragdoll_NPC L Thigh [LThg]`).

### Required Bones (Skyrim)

Minimum bones for character skeleton:
- `NPC Root [Root]` - World space root
- `NPC COM [COM]` - Center of mass
- `NPC Pelvis [Pelv]` - Hips
- `NPC Spine [Spn0]`, `Spine1 [Spn1]`, `Spine2 [Spn2]` - Torso
- `NPC L/R Clavicle [L/RClv]` - Shoulders
- `NPC L/R UpperArm [L/RUar]` - Upper arms
- `NPC L/R Forearm [L/RLar]` - Forearms
- `NPC L/R Hand [L/RHnd]` - Hands
- `NPC L/R Thigh [L/RThg]` - Thighs
- `NPC L/R Calf [L/RClf]` - Shins
- `NPC L/R Foot [L/RFt ]` - Feet
- `NPC L/R Toe0 [L/RToe]` - Toes
- `NPC Neck [Neck]` - Neck
- `NPC Head [Head]` - Head

**Weapons:**
- `WeaponBack` - Sheathed weapon on back
- `WeaponSword` - Sheathed sword on hip
- `WeaponAxe` - Sheathed axe
- `WeaponDagger` - Sheathed dagger
- `WEAPON` - Equipped weapon in hand

**Custom bones:**
- Can add bones for tails, wings, capes, etc.
- Must be in hierarchy (connected to existing bone)
- Must export to HKX skeleton

### Bone Transform Data

Each bone stores:

**Translation:** 3D offset from parent (X, Y, Z)

**Rotation:** Quaternion (X, Y, Z, W) 

**Scale:** 3D scale factors (X, Y, Z)
- Usually (1, 1, 1)
- Non-uniform scale can cause issues

### Ragdoll Data

The Havok format combines skeleton and ragdoll in one HKX (`hkpPhysicsData` + `hkaRagdollInstance` alongside the `hkaSkeleton`), and **Skyrim's actor `skeleton.hkx` files use that path** — including the human ones.

`[Skyrim]` `skeleton.hkx` and `skeleton_female.hkx` are byte-identical in structure: 324 objects in the `__data__` section, organized as the canonical Havok dual-skeleton ragdoll bundle:

- 1× `hkRootLevelContainer`, 1× `hkaAnimationContainer`
- **2× `hkaSkeleton`** — one for animation (`NPC Root [Root]`, 99 bones), one for the ragdoll (`Ragdoll_NPC COM [COM ]`, 18 bones)
- 2× `hkaSkeletonMapper` — translate poses between the two skeletons in either direction
- `hkpPhysicsData` → `hkpPhysicsSystem` → 19× `hkpRigidBody` (each with an `hkpCapsuleShape`), tied together by an `hkaRagdollInstance`
- 34× `hkpConstraintInstance` wrapping 18× `hkpRagdollConstraintData` (6-DOF) + 16× `hkpLimitedHingeConstraintData` (single-axis, elbows/knees). One `hkpPositionConstraintMotor` is referenced from inside one of the constraints, not as an instance of its own.
- Bookkeeping: `hkMemoryResourceContainer`, `hkMemoryResourceHandle`

A binary class-name scan of all 38 vanilla Skyrim `skeleton*.hkx` files under `meshes\actors\` (human, every creature, dragons, dwarven constructs, atronachs, etc.) finds the ragdoll classes (`hkaRagdollInstance`, `hkpPhysicsData`, `hkpRigidBody`, `hkpRagdollConstraint`) in every one. Bundled ragdoll is the rule for actor skeletons in Skyrim, not an exception for creatures.

Creature skeletons use the same wire format and the same base ragdoll classes, but quadrupeds typically have more bones in both skeletons (the tail, separate front/back legs, separately animated ears/jaw/tongue) and a higher fraction of those bones participate in the ragdoll than for humans. Some creatures also include `hkpConvexVerticesShape` and `hkpConvexVerticesConnectivity` objects for collision bodies whose shape doesn't fit a capsule (e.g. a head).

The paired `skeleton.nif` *also* carries ragdoll data — `bhkRigidBody`, `bhkRagdollConstraint`, `bhkLimitedHingeConstraint`, and `bhkBlendCollisionObject` blocks attached to bone NiNodes via `bhkCollisionObject`. Each rigid body carries its own collision shape, mass, friction, and restitution; the constraints define the joint limits between parent/child bodies. The role split between the HKX ragdoll and the NIF ragdoll isn't documented here.

`[FO4]` FO4's `skeleton.hkx` ragdoll structure hasn't been verified for this library.

## XML Representation

Community tools (`hkxpack`, `hkxcmd`, `hkxc`) convert HKX files to and from a human-readable XML representation. **The XML is a logical view of the object graph, not a faithful image of the binary**, and a round trip through XML is lossy in two distinct ways.

### Section folding (reversible)

The binary packfile has three sections (`__classnames__`, `__types__`, `__data__`); the XML shows only one `<hksection name="__data__">` root. The two folded sections are essentially metadata:

- `__classnames__` is a lookup table mapping class signatures (32-bit hashes) to class-name strings. The XML embeds both directly on each `<hkobject class="..." signature="...">`, so the table is regenerable from the XML on re-serialization.
- `__types__` carries embedded type-layout metadata for forward-compat. In `hk_2010.2.0-r1` this section is empty — the format identifies types by class name + signature against a known type registry. Newer Havok versions (FO4's `hk_2014.1.0-r1`) use this section more.

This folding is fully reversible. Round-tripping XML → HKX regenerates the header, classnames, and types sections byte-identically.

### Float precision (irreversible)

XML formats floating-point values with `%f`-style notation (six decimal places). Anything below ~1e-6 prints as `0.000000`, and parsing `0.000000` yields exact zero — sub-precision noise is silently stripped. A round trip through XML therefore quantizes every float in the file to ~6 decimal digits.

For a vanilla SE `skeleton.hkx`, a round trip produces a file of the exact same size (85408 bytes — layout is deterministic) but with ~8.5% of bytes different from the original. The header, `__classnames__`, and (empty) `__types__` sections round-trip byte-identically; the entire diff is float values within `__data__`. Verified by checking that the byte-level diff begins past the section table and exclusively touches IEEE-754 fields like quaternion components and reference-pose offsets.

For skeletons this loss is harmless (the affected values are subnormal noise on identity quaternions and zero offsets) but for animations it compounds with the precision losses inherent to spline-compressed animation tracks — see [Compression](#compression). The decode-spline → format-floats → re-fit-spline → re-quantize path through XML adds float-format loss on top of the existing decode/refit/requantize cycle.

The implication: **the XML pipeline is not a transparent inspection or patching layer**. It's good for reading and structural editing. It's not byte-faithful — re-saving a file through XML is a lossy export pass even if no field values were touched.

### When XML is and isn't appropriate

| Use case | XML | Direct binary |
| --- | --- | --- |
| Reading or auditing structure | ✓ | adequate via `dump_hkx.py` |
| Adding/renaming bones in skeletons | ✓ | hard |
| Behavior graph editing | ✓ | hard |
| Verifying a file is unchanged byte-for-byte | ✗ (re-export changes bytes) | ✓ |
| Round-tripping animations without data loss | ✗ | ✓ if you avoid the conversion entirely |
| Patching a single field without rewriting | ✗ | ✓ |

For inspection without precision loss, the `dump_hkx.py` utility at the project root parses the binary structure and prints a human-readable report — header fields, section table, classnames, and per-object byte ranges with outgoing references resolved by class name — without converting any field values to text. Object payloads are summarized by class and size, not field-by-field; for that, the XML view is the practical choice (with the precision caveat above).

## Animation Data

### Keyframe Structure

**Frame:** Single snapshot of skeleton pose at specific time

**Transform per bone:**
- Translation (X, Y, Z)
- Rotation (quaternion)
- Scale (X, Y, Z) - often omitted if always 1

**Timeline:**
- Start time: 0.0
- End time: Duration (seconds)
- Source authoring rate: Typically 30 fps (animator's keyframe spacing before export). This is **not** a runtime cap — see [Continuous sampling](#continuous-sampling-at-runtime) below.
- Stored data: A fitted B-spline, not the source keyframes (see [Compression](#compression))

### Compression

Skyrim and Fallout 4 store per-bone animation data as `hkaSplineCompressedAnimation`. The format is **structurally lossy** — the original animator's keyframes don't survive export. What's in the file is a fitted B-spline approximation plus bit-quantized control points.

#### Track structure per bone

Each bone (Havok calls one a "track") gets up to three independent B-splines:

- **Position** — one B-spline whose control points are 3D vectors. Each axis (X / Y / Z) is independently classified, so a bone moving only on X stores a full spline for X but a single constant for Y and Z.
- **Rotation** — one B-spline whose control points are quaternions. **All-or-nothing**: the whole quaternion is one of the three classifications below; you can't decompose it per-axis without breaking unit-length normalization.
- **Scale** — same per-axis structure as position. Most bones leave all three axes as `identity` since scale rarely animates.

The per-component classifications:

| Class       | What's stored                                    |
|-------------|--------------------------------------------------|
| `spline`    | Knot vector + sequence of quantized control points |
| `static`    | One quantized constant value                       |
| `identity`  | Nothing — translation = 0, scale = 1, rotation = identity quat |

A typical idle bone might be `pos=identity, rot=spline, scale=identity`. A finger that only rotates would be `pos=identity, rot=spline, scale=identity` too. The COM bone with root motion is more like `pos=spline (all axes), rot=spline, scale=identity`.

#### Time blocking

Long animations are chunked into time blocks of `max_frames_per_block` (256 in Skyrim). Each block carries its own set of splines for every track. So a 600-frame animation becomes ~3 blocks, with each animated bone getting up to three sets of splines (one per block) for each of position / rotation / scale.

This keeps each spline fit local — fitting a single B-spline through hundreds of frames is computationally hard and produces poor approximations. Short animations (under 256 frames) just have one block.

#### How spline fitting loses information

The Havok Content Tools exporter fits a B-spline through the source animation curve within a configurable error tolerance, then stores the resulting knot vector and control points. The control points are **not** the source keyframes:

- **Their parameter positions are wherever the fitter chose to place them**, dictated by the knot vector. A region with rapid change gets denser knots; a flat region gets sparse ones. Nothing forces alignment with the animator's keyframe times.
- **Their values are off-curve weights, not samples.** A B-spline `C(t) = Σᵢ Nᵢ(t) · Pᵢ` doesn't pass through its control points except at the endpoints (and only when the knot vector is clamped there with multiplicity = degree+1).

Original keyframes are not preserved anywhere in the file. High-frequency wiggle that doesn't fit the spline is smoothed away.

(Other Havok formats, like `hkaInterleavedUncompressedAnimation`, *can* preserve frame-aligned data. Skyrim and Fallout 4 don't use them — every animation HKX in those games is `hkaSplineCompressedAnimation`.)

#### Bit quantization (additional loss)

Every stored value — spline control points and static-track constants alike — is bit-quantized:

- **Positions / scales:** 8-bit or 16-bit integer per axis, mapped back to a per-axis `[min, max]` range stored alongside the spline data
- **Rotation quaternions:** 32-bit or 40-bit total (3 of 4 components packed; ~12 bits/component for the 40-bit form, which is the most common)

This loss compounds with the spline-fitting loss above and is independent of it.

#### Continuous sampling at runtime

B-splines are continuous functions of a real-valued parameter `t` — you can evaluate them at any `t`, not just integer frames. Skyrim's playback isn't locked to 30 Hz: the engine samples the splines at whatever timestep the animation update produces, giving smooth playback on a 60+ Hz display. The "source authoring rate" (typically 30 fps when the animator placed keyframes before export) and the "runtime sample rate" (engine frame time) are independent.

To play an animation at altered speed, the behavior graph just samples at `t' = playback_rate · wall_clock_time`. The encoded duration and knot spacing are fixed at export time, but the engine retimes by adjusting `t`.

#### Worked example

A real spline pulled out of `meshes/actors/character/animations/1hm_equip.hkx` (87 frames, 1.433 s, 99 bone tracks). Picking one bone's rotation track:

- Spline degree: **3** (cubic B-spline)
- Knot vector (**15** entries; values are frame-space):
  ```
  [0.0, 0.0, 0.0, 0.0, 4.0, 10.0, 18.0, 18.0, 28.0, 38.0, 38.0, 86.0, 86.0, 86.0, 86.0]
  ```
- **11** quaternion control points `[x, y, z, w]`:
  ```
  CP[ 0]  [+0.998466, -0.015545, +0.005527, +0.052852]
  CP[ 1]  [+0.998366, -0.019690, +0.006909, +0.053197]
  CP[ 2]  [+0.998138, -0.033507, +0.013817, +0.049052]
  CP[ 3]  [+0.997595, -0.022108, +0.002763, +0.065633]
  CP[ 4]  [+0.999516, -0.015890, -0.023490, +0.012781]
  CP[ 5]  [+0.999201, -0.017963, -0.034889, -0.007600]
  CP[ 6]  [+0.998549, -0.045943, -0.026944, -0.007945]
  CP[ 7]  [+0.998524, -0.038343, -0.036616, +0.011745]
  CP[ 8]  [+0.997635, -0.044907, -0.051815, +0.004836]
  CP[ 9]  [+0.997890, -0.036616, -0.042143, +0.033162]
  CP[10]  [+0.998322, -0.036271, -0.039725, +0.021417]
  ```

Things to notice:

- **Knots are not at frame positions.** Frame indices run 0–86. The knots cluster at {0, 4, 10, 18, 28, 38, 86} — dense at the start (where the equip motion ramps up) and sparse later (when the bone settles).
- **Repeated knots reduce continuity locally.** The duplicate `18.0, 18.0` and `38.0, 38.0` drop the curve from C² to C¹ at those parameter values; the source animation had a kink there.
- **Only the endpoint control points sit on the curve.** Because of the knot-multiplicity-of-4 clamping at start (`0, 0, 0, 0`) and end (`86, 86, 86, 86`), CP[0] equals the spline's value at frame 0 and CP[10] equals its value at frame 86. Verified: CP[0] = `[+0.998466, -0.015545, +0.005527, +0.052852]`, and the spline evaluated at frame 0 = the same.
- **Interior control points do not correspond to any frame.** CP[5] = `[+0.999201, -0.017963, -0.034889, -0.007600]`. There is no frame at which the bone's rotation equals this quaternion. It's an off-curve weight that pulls the spline through its arc. The actual frame-50 value is `[+0.998068, -0.041318, -0.044963, +0.011491]` — nothing like CP[5].
- **Compression ratio:** 11 quaternions × ~4 bytes (32-bit packed) + 15 knot bytes + 4-byte mask ≈ 63 bytes. Versus 87 frames × 16 bytes (full float32 quaternion) = 1392 bytes uncompressed. **~22× compression** on this single rotation track.

#### Tunable tolerance

The exporter exposes position and rotation tolerance parameters. Defaults produce visible error on dense or high-frequency curves; setting tolerance near zero minimizes loss but defeats the size advantage. Modders have reported visible artifacts ("the protagonist shivers like someone infected by malaria") at default tolerance, fixed by tightening it.[^havok-fidelity-thread]

#### Re-export compounding

Each export pass — decode spline → re-fit new spline to decoded samples → re-quantize — accumulates error. The compounding follows mathematically from the format; how visible it is in practice depends on tolerance settings and curve content.

#### Best practice

Keep original source files (FBX, Blender) and treat HKX as a build artifact, not a master format.

[^havok-fidelity-thread]: [How to avoid visible animation fidelity loss when exporting with Havok content tools? — Nexus Mods forums](https://forums.nexusmods.com/topic/13478686-how-to-avoid-visible-animation-fidelity-loss-when-exporting-with-havok-content-tools/)

### Annotation Tracks

Annotations mark specific events in animations.

**Common annotations:**
- `preHitFrame` - Just before weapon contacts
- `HitFrame` - Weapon impact point
- `KillMove` - Special kill move timing
- `FootLeft` / `FootRight` - Footstep sounds
- `SwapWeapon` - Switch weapon in hand
- `TriggerActivate` - Activate event fires

**Usage:** Behavior graphs trigger events, sounds, effects at annotation points.

### Animation Blending

Game blends multiple animations at runtime.

**Blend types:**
- Additive (add on top of base)
- Override (replace base)
- Partial (specific bones only, e.g., upper body aim)

**Blend weight:** 0.0-1.0 (how much each animation contributes)

**Transition:** Smooth blend from one animation to another over time.

## `FO4` Fallout 4 Differences

### 64-bit Havok

**hk_2014.1.0-r1:** Updated Havok version

**Changes:**
- 64-bit pointers (incompatible with LE/SE)
- Updated compression
- Slightly different binary structure

**Conversion:** Use Havok Content Tools or community converters (hkxpack).

### FaceBones System

Fallout 4 has dual armature system for faces.

**FaceBones skeleton:** `meshes/actors/character/character assets/facebone.hkx`

**Special bones:**
- Facial expression bones (brow, cheek, jaw, etc.)
- Separate from body skeleton
- Merged at runtime

**Head mesh requirements:**
- Weighted to **both** body skeleton and FaceBones
- Complex rigging workflow

**Export challenge:** Blender doesn't natively support dual armatures - requires special export scripts.

### Skin Bones

Fallout 4 has special `_skin` suffix bones.

**Example:** `LArm_Skin`

**Purpose:**
- Twist/deformation helpers
- Special parenting behavior
- Auto-generated from base bones in some cases

**Constraint:** Not fully documented, trial-and-error required.

## Tools

### PyNifly (Blender Addon)

**Import/export HKX skeletons and animations.**

**Skeleton import:**
```python
import bpy
from io_scene_nifly import pynifly

pynifly.import_hkx_skeleton('skeleton.hkx')
```

**Animation export:**
- Blender action → HKX animation
- Supports bone animation only (no morph/shape keys)
- Applies Havok compression on export

See [PyNifly Animation Workflow](../tools/pynifly/animations.md).

### Havok Content Tools (HCT)

**Official Havok toolset** (requires license).

**Features:**
- Convert between formats (FBX ↔ HKX)
- Preview animations
- Adjust compression settings
- Batch processing

**Filter Manager:** Configure export settings (compression level, sample rate, etc.)

**Availability:** Expensive commercial license. Bethesda has custom version. Community reverse-engineered alternatives exist.

### hkxpack / hkxcmd

**Community tools** for HKX conversion.

**hkxcmd (older):**
- Convert HKX ↔ XML
- Edit in XML, convert back
- Fragile, version-specific

**hkxpack (newer):**
- Python-based HKX packer/unpacker
- More reliable than hkxcmd
- Supports LE/SE/FO4 formats

**Usage:**
```powershell
# Unpack HKX to XML
hkxpack unpack animation.hkx

# Edit animation_unpacked.xml

# Repack XML to HKX
hkxpack pack animation_unpacked.xml animation_new.hkx
```

### NifSkope

**View skeleton references** in NIF files.

**Check:**
- Which skeleton NIF references (NiStringExtraData "HKX")
- Bone names in NiSkinInstance
- Bone order

### Creation Kit

**View animations** in preview window.

**Limitations:**
- Preview only, no editing
- Doesn't show annotation tracks

## Workflow Tips

### Creating Custom Skeletons

1. **Start from existing:** Modify Skyrim/FO4 skeleton, don't build from scratch
2. **Maintain required bones:** Keep all vanilla bones, add custom bones as children
3. **Name consistently:** Follow `NPC <Part> [Code]` convention
4. **Export to HKX:** Use PyNifly or HCT
5. **Test in-game:** Load with simple NPC to verify

### Creating Animations

1. **Rig character in Blender** with matching skeleton
2. **Animate bones** (keyframes on timeline)
3. **Export to HKX** via PyNifly
4. **Test in-game:**
   - Place in `Data/meshes/actors/<race>/animations/`
   - Add to behavior graph (or use animation replacer mod)
5. **Iterate:** Adjust timing, transitions

### Converting LE → SE

**Skeleton:** Usually compatible (same hk_2010.2.0-r1)

**Animations:** Usually compatible

**If issues:** Re-export from source (FBX/Blender) with SE settings.

### Converting LE/SE → FO4

**Required:** Convert with hkxpack or HCT (different Havok version).

**Process:**
```powershell
# Unpack LE/SE animation
hkxpack unpack skyrim_anim.hkx

# Repack for FO4
hkxpack pack skyrim_anim_unpacked.xml fo4_anim.hkx --fallout4
```

**Limitations:**
- Some features not cross-compatible
- Ragdoll data may need adjustment
- Test thoroughly

## Common Issues

### Animation Not Playing
- **Wrong skeleton:** Animation bones don't match skeleton
- **Missing behavior graph entry:** Animation not referenced
- **Filename mismatch:** Animation name doesn't match behavior graph reference
- **Fix:** Check bone names, verify behavior graph, check file paths

### Animation Jittery/Broken
- **Bone mismatch:** Bone names don't match exactly
- **Scale issues:** Non-uniform bone scales
- **Quaternion corruption:** Rotation data invalid
- **Fix:** Re-export from clean source, verify bone names

### Skeleton Causes CTD
- **Corrupted HKX:** Binary corruption
- **Wrong Havok version:** LE HKX in SE game
- **Missing required bones:** Essential bones removed
- **Fix:** Re-export skeleton, verify version, restore missing bones

### Mesh Not Following Skeleton
- **Bone name mismatch:** NIF bone names ≠ HKX bone names
- **Wrong skeleton reference:** NIF points to different skeleton
- **Fix:** Check NiStringExtraData "HKX" in NIF, verify bone names match

## See Also

- [PyNifly Animations](../tools/pynifly/animations.md) - Blender animation workflow
- [NIF Files](nif-files.md) - NiSkinInstance and bone references
- [Bone Names Reference](../reference/bone-names.md) - Standard bone names
- [Animation Workflows](../workflows/animations.md) - Step-by-step guides
- [Animation Debugging](../debugging/animation-issues.md) - Troubleshooting
