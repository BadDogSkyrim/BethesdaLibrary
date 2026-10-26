# Starfield Cloth (`BSClothExtraData`)

Hair, tails, skirts, coat flaps, capes and banners move by Havok cloth. The simulation lives in a
nif's `BSClothExtraData` block. This page covers the block's format, how a cloth is put together,
what the game does with it, and what we learned building cloth from scratch and testing it in
game.

Measured on all 298 vanilla nifs with cloth (320 pieces of cloth), October 2026. In-game results
are from a fox tail, the vanilla ponytail and a vanilla skirt. PyNifly reads, edits and builds
cloth (30.1.0); its [user page](https://github.com/BadDogSkyrim/PyNifly/blob/main/docs/Starfield_Cloth.md)
covers the Blender side.

---

## 1. What cloth does

**Cloth only moves bones.** It simulates a small set of **particles**: a strip down a ponytail,
a few dozen across a skirt. Their triangles drive bones, and the render mesh is skinned to those
bones the ordinary way. Nothing in the blob refers to the render mesh.

- **Pinned particles** (mass 0) follow the skeleton. The **free** ones are simulated.
- Each **driven bone** follows one sim triangle.
- **Collision shapes** (capsules, tapered capsules, spheres) ride body bones and keep particles
  out of the body.
- **Constraints** hold the particles in shape: links, hinges, distance limits and bone planes.

---

## 2. The container: a Havok 2019 tagfile

The payload is a **Havok tagfile**: magic `TAG0`, SDK `20190200`. `[FO4]` used an older Havok
*packfile* with its type information stripped. The Starfield file **carries its own type
definitions**: every class, field name, offset and size. So a generic reader turns it into named
objects without any class definitions supplied.

Each section header is a big-endian `uint32` and a 4-character tag. The top two bits of the
`uint32` say whether the section holds other sections (0) or data (1); the low 30 bits give its
size, including the 8-byte header.

```
TAG0
  SDKV   "20190200"
  DATA   the object bytes
  TYPE
    TPTR   runtime pointer table (zeros in a file)
    TST1   type-name strings, NUL-separated
    TNA1   the types: name + template parameters
    FST1   field-name strings, NUL-separated
    TBDY   each type's parent, format, size/alignment and fields
    THSH   type hashes
    TPAD   padding
  INDX
    ITEM   the item table: {u32 type+kind, u32 offset into DATA, u32 count}; item 0 is null
    PTCH   where in DATA the references between items sit
```

**Reading the types:**

- **Integers** in `TNA1`/`TBDY` are Havok's variable-length form, big-endian. Below `0x80` is one
  byte; top bits `10` add a byte (14-bit value); `110` take three bytes, and so on.
- **`TNA1`:** a count (including type 0), then per type a name index into `TST1` and its
  template parameters. A parameter whose name starts with `t` holds a type; one starting with
  `v` holds an integer.
- **`TBDY`:** per type, its index, its parent, and an option mask saying what follows.
  `0x01` format, `0x02` element type, `0x04` version, `0x08` size and alignment, `0x10` flags,
  `0x20` fields, `0x40` interfaces, `0x80` attribute.
- **A field** is name (an `FST1` index), flags, offset and type. When the flags have bit `0x80`
  set, **one extra value comes before the offset**. In vanilla only `hkPackedVector3.values`
  and `hclCollidable.userData` do this; its meaning is unknown.
- **The format's low 5 bits** give the kind: 2 bool, 3 string, 4 int (bit `0x200` signed),
  5 float, 6 pointer, 7 class, 8 array. An **array with bit `0x20` set is inline**, its length in
  the bits above 8: `hkVector4` is `0x428` (four floats), `hkMatrix4` is `0x1028` (sixteen).
- **In `DATA`,** a pointer, a string or an ordinary array is a `uint32` item index.
- **`PTCH`** is grouped by the type of the reference field: `u32 type, u32 count`, then that many
  `DATA`-relative offsets. Null references aren't listed.
- Some blobs **name a type without defining it** (no `TBDY` body). An empty array of such a type
  needs no element size.

### Writing one: two traps

Each of these makes Starfield **drop the cloth silently**: the mesh renders, but it doesn't move.

1. **Every `PTCH` offset must lie inside an item.** A reference left in a gap of `DATA` kills
   the cloth.
2. **Every `TYPE` subsection must be padded to 4 bytes**: `TST1` and `FST1` with `0xFF`, the
   others with zeros. Zero padding at the end of `TBDY` reads as empty entries, so anything after
   it is never read.

Not required, all tested in game: item order, `THSH` order, body order, section alignment, and
unused gaps in `DATA`.

---

## 3. How a cloth is put together

Every vanilla cloth has the same structure. A blob holds a `hkRootLevelContainer` whose
variants are one `hclClothData` per piece of cloth (the pirate officer's lower half has six) and
one `hkaSkeleton`.

Per `hclClothData`:

| Part | Holds |
|---|---|
| `simClothDatas[1]` | the particles, sim triangles, constraint sets and collidables (`hclSimClothData`) |
| `bufferDefinitions[2]` | a scratch buffer and the sim buffer, one vertex per particle |
| `transformSetDefinitions[1]` | the skeleton's bones |
| operators | skin, move particles, simulate, bone deform (once or twice), copy |
| `clothStateDatas[2]` | `Simulate` = skin, move, simulate, deform; `Animate` = skin, copy, deform |

- **Skin** (`hclBoneSpaceSkinPNOperator` or `hclObjectSpaceSkinPNOperator`) places **every**
  particle from the skeleton. Pinned particles are then held there by **move particles**. Free ones
  use it as the anchor for local range, and the `Animate` state puts them there outright.
- **Bone deform** (`hclSimpleMeshBoneDeformOperator`) drives the bones.
- **Copy** (`hclCopyVerticesOperator` or `hclGatherAllVerticesOperator`) feeds `Animate`.

**Bone-space skinning** (vanilla hair uses it) stores particles in blocks:

| Bones per particle | Particles per block |
|---|---|
| 4 | 4 |
| 2 | 8 |
| 1 | 16 |

- Slot `k*n + j` holds bone `j` of the block's particle `k`, where `n` is the bones per particle.
- `localPosition` is (w · B⁻¹p, w): the weight times the particle in the bone's bind frame.
- Normals are packed `int16` (value / 32768, exponent word 12288).

**Each driven bone follows its nearest triangle**: the one whose centre is nearest the bone
(5,736 of 5,742 vanilla pairs). Its offset is `L = F⁻¹ · B_bind`, where:

- `B_bind` is the bone's bind matrix;
- `F` is the triangle's frame, with columns
  `[p0 − c, p1 − c, (p0 − c) × (p1 − c), c]` (`c` the centre; the cross product not
  normalised).

### The skeleton

The blob carries its own `hkaSkeleton`, and its reference pose is the bind the cloth uses. Vanilla
skeletons range from **2 bones to the whole authoring scene**: the ponytail carries 165,
including face bones; 27 cloths carry 5 and 11 carry 2. **A skeleton of just the bones the cloth
uses works.** We tested the used bones plus their ancestors up to `Root`.

**Bones are matched by name.** A cloth's own bones don't need to exist anywhere else:

- The ponytail's `C_Cloth_PonyTail_00`–`_04` are in no skeleton nif, and not among the hair
  nif's nodes. They exist only in the blob's skeleton (which gives their parent and rest pose)
  and by name in the mesh's skin.
- **You can make up cloth bone names.** A fox tail rebuilt with invented bones
  `C_Cloth_Tail_00`–`_08` worked in game. Give them sensible parents (the tail's first bone under
  `C_Hips`).

### Cloth bones in a skinned nif

A vanilla Starfield skin names its bones in `SkinAttach`, **one per slot**, and its
`BSSkin::Instance.boneRefs` are empty. A shape weighted to cloth bones can also point some
slots at `NiNode`s. Then:

- **The node names the slot.** `SkinAttach` holds the cloth bone's **parent** in that slot (the
  Collector coat's slots say `C_Chest` and `C_Hips`; the nodes say `R_Cloth_Jacket` and so on).
- The weights and binds still index **every** slot (37 for the Collector's upper body, 11 of them
  nodes). A reader that takes only the non-empty node refs gets the wrong bone for every
  weight.
- The nodes are **flattened under the root**, each holding the bone's transform **relative to
  its real parent, in metres**. They are no use as a pose; the bind is where the bone is.
- The Collector's upper body also has a non-identity `BSGeometry` transform: `C_Head`'s
  position, in metres. That's against the rule in [Meshes](meshes.md) that a skinned shape's
  transform is identity.

26 vanilla shapes use node slots, including the Collector outfit, a farmer outfit and a pirate
upper body. A shape weighted only to made-up cloth bones, with plain `SkinAttach` names and no
nodes, also works in game.

---

## 4. Constraints

Each `hclSimClothData` lists its constraint sets in `staticConstraintSets`. The simulate
operator's `constraintExecution` gives the order. **Vanilla always runs them in this order:**

1. local range
2. bone planes
3. standard links and compressible links
4. bend stiffness
5. stretch links
6. volume

| Set | Cloths (of 320) | What it does |
|---|---|---|
| Standard links (`hclStandardLinkConstraintSetMx`) | 277 | keep two particles at their rest distance |
| Stretch links (`hclStretchLinkConstraintSetMx`) | 263 | stop two particles getting further apart; one end is pinned |
| Local range (`hclLocalRangeConstraintSet`) | 233 | limit how far a particle strays from its skinned position |
| Bend stiffness (`hclBendStiffnessConstraintSetMx`) | 128 | a hinge spring at each edge two triangles share |
| Bone planes (`hclBonePlanesConstraintSet`) | 57 | keep a particle on one side of a plane riding a bone |
| Compressible links | 43 | |
| Volume | 7 | |

Records come as `singles` and as `batches` of four in parallel arrays.

**Standard links.** Vanilla gives every link in a set one stiffness `s`, split by inverse mass:
`stiffnessA = s·wA/(wA+wB)`, `stiffnessB = −s·wB/(wA+wB)`. A link between two pinned particles
does nothing.

**Stretch links.** `restLength` is the distance times a slack factor: 1.0 in most cloths, up to
1.43. Vanilla runs them from the pinned root to the tip, so the whole length can't stretch.

**Bend stiffness** (worked out from vanilla's 3,256 records). Each record names the two "wing"
particles A and B (the triangles' far corners) and the edge's C and D:

- **Weights:** A and B get `dB/(dA+dB)` and `dA/(dA+dB)`, where `dA` and `dB` are the wings'
  distances from the edge line. C and D get `−(1−t)` and `−t`, where `t` is where the wings'
  weighted point meets C–D.
- **`h`** = the sum of weight × position. It is zero when the two triangles lie flat.
- **`restCurvature`** = `−(h·n) / (dA·dB)`, with `n` the unit normal of triangle A-C-D.
- **`bendStiffness`** = `−k / Σ(weight² · invMass)`, with `k` from 0 to 1.
- The set's `maxRestPoseHeightSq` = 64 × the largest `h²`.

Vanilla paints `k` per hinge (106 of 128 cloths vary it), commonly 0.5 to 0.8. A hinge works on
the four particles of its two triangles, so it doesn't matter whether its edge is also a link.

**Local range.** Up to four sets per cloth, each with its own stiffness, shape and normal
handling. Each record gives a maximum distance, and optionally maximum and minimum normal
distances and a per-particle stiffness. Long garments rely on it to stay near the body: the
Khan skirt at 0.1 m, the trench coat 0.5 m, the Varuun ambassador up to 1 m.

**Bone planes.** Each record is a plane `(nx, ny, nz, d)` in **the bone's frame**, so it moves
with the bone, plus a particle, the bone and a stiffness.

- The particle is kept where **`n·x + d ≥ 0`**. All 5,421 vanilla records sit on that side at
  rest.
- Vanilla uses them for:
  - hair: 2–9 planes on the head, to keep it out of the face
  - the ponytail: planes on the neck
  - skirts and coats: planes under the hips, to stop flaps flipping up
  - the Starborn cape: two hip planes per particle, a wedge that turns with the pelvis
- **No vanilla cloth uses a plane as a floor.**

---

## 5. Collision shapes

`perInstanceCollidables` holds the shapes. `collidableTransformMap` gives the bone each one follows
and its offset. Per particle, `staticCollisionMasks` says which shapes it collides with: bit k
for the cloth's k-th shape.

| Shape | Use |
|---|---|
| `hclCapsuleShape` | most body parts |
| `hclTaperedCapsuleShape` | skirts: a radius at each end |
| `hclSphereShape` | the Aceles only |

A mod's fox tail had leg capsules of 0.45 m on one side and 0.30–0.35 m on the other.
Replacing one side with mirrored copies of the other worked fine in game.

---

## 6. Settings

The most common vanilla values:

| Setting | Field | Vanilla |
|---|---|---|
| Gravity | `simulationInfo.gravity` | (0, 0, −9.81) in 268 of 320 |
| Damping | `simulationInfo.globalDampingPerSecond` | 0.85–0.98 |
| Iterations | simulate `Config.numberOfSolveIterations` | **1 in all 320** |
| Sub-steps | `Config.subSteps` | 1 in 306 |
| Link stiffness | standard and stretch | 1.0 and 1.0 in 210 |
| Particle mass / radius / friction | `particleDatas` | 0.08 / 0.02 m / 0.5 most common |
| Motion transfer | `transferMotionData` | translation 0.6–0.6 over 0–10; rotation 0–0.6 over 30–90°/s |
| Transfer bone | `transferMotionData.transformIndex` | `C_Head` 80, `C_Chest` 69, `C_Hips` 63 |
| Landscape collision | `landscapeCollisionEnabled` | off in all 320 |

---

## 7. In-game behaviour

What we learned testing tails, a ponytail and a skirt:

- **Landscape collision does nothing.** Turning on `landscapeCollisionEnabled`, at two radii,
  gave no ground contact on flat ground or stairs.
- **A floor is a bone plane on `Root`.** `Root` stays at the feet when the actor crouches or
  lies down. A plane facing up about 3 cm above it, holding every free particle at stiffness 1,
  keeps a tail out of the ground. It's flat at the feet, so it's wrong on slopes and stairs, and
  it holds particle centres, not the mesh around them.
- **Stiffness is applied once per iteration** (position-based dynamics). With one iteration even
  0.999 barely holds; a fox tail looked right at 4 iterations and hinge stiffness 0.9.
- **Hinges alone don't hold a long strip up against gravity.** Pinning more particles at the base
  does; so does local range, graded from small near the root to large at the tip.
- **On a strip, the rung hinges control bending and the diagonal ones control twist.** To free a
  stretch of strip, zero them all.
- **An anchor particle off the strip's plane must use standard links.** With stretch links (and
  the root rung unpinned) a tail hung straight down.
- **Keep the sim mesh simple.** A closed triangular tube twitches and twists at any setting.
  Its hinges share triangles and fight each other, so stiffer hinges or more iterations make it
  worse. With its hinges at 0 it's calm but kinked near the body and stiff. A flat strip works
  well.
- **Shipping a re-exported vanilla piece needs its `.mesh` in `Data\geometries`.** A skirt
  looked distorted until it was deployed.

---

## Sources

- Vanilla Starfield meshes (unpacked), 298 nifs with cloth. Census scripts in PyNifly's
  development work, October 2026.
- PyNifly: `pyn/havok_tagfile.py`, `havok_graph.py` (read and write tagfiles), `sf_cloth.py`
  (read a cloth), `sf_cloth_build.py` (build one):
  https://github.com/BadDogSkyrim/PyNifly
- nifly `NifFile::GetShapeBoneList` (bone slots): https://github.com/BadDogSkyrim/nifly
