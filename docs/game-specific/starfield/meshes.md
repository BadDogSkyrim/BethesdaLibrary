# Starfield Geometry: NIF + External `.mesh` Files

Starfield keeps the classic NIF scene-graph but **moves the actual mesh geometry out of the NIF** into standalone `.mesh` files streamed from `geometries/` archives. A Starfield NIF is a tree of `NiNode`s whose shapes are `BSGeometry` blocks; each `BSGeometry` holds only bounds, refs, and up to four *pointers* (a hash path or embedded blob) to `.mesh` data. This page documents the NIF-side blocks and the external `.mesh` binary layout as currently reverse-engineered, with emphasis on bodypart/armor meshes, skinning, and Blender import/export.

Everything here is Starfield-only unless tagged `[FO4]` / `[SSE]` / `[Skyrim]` for contrast.

## Version identification

A Starfield NIF reports:

| Field | Value |
|---|---|
| NIF file version | `20.2.0.7` (`V20_2_0_7`) |
| User version | `12` |
| Stream (BS) version | `172`–`175` (real base-game assets = `173`) |

Upstream nifly detects Starfield as `file == V20_2_0_7 && stream >= 172 && stream <= 175` (`BasicTypes.hpp::NiVersion::IsSF()`), and its canonical writer version is `getSF() = {V20_2_0_7, user 12, stream 172}` — so tooling **reads 172–175, writes 172**. The *file* version string is shared with Fallout 4 / FO76, so the **stream version is what distinguishes Starfield**.

> **Stream version drift:** the two vanilla NIFs extracted for this page (skeleton + body) both report **stream 173**; newer game updates / current Outfit Studio builds go up to **175**, and the `.mesh` meshlet encoding was revised to "version 2" in game update **1.11.33** (with a mesh-path migration in 1.11.36). Treat the Starfield range as **172–175**. (An older nifly fork keyed only 172–173 — worth checking if using an out-of-date copy.)

---

## 1. The geometry-less NIF and the `BSGeometry` block

### What replaced `BSTriShape`

`[FO4]``[SSE]` geometry lived in `BSTriShape` / `BSSubIndexTriShape` blocks *inside* the NIF (vertices, tris, skin weights all embedded). Starfield replaces these with **`BSGeometry`**, which contains **no vertex/triangle arrays at all** — just a reference to external `.mesh` file(s).

`BSGeometry` derives from `NiShape` and (per nifly `Geometry.hpp`/`Geometry.cpp`) streams in this order:

```
BSGeometry (: NiAVObject : NiShape)
  BoundingSphere  bounds            // center(Vector3) + radius(float)  = 16 bytes
  float           boundMinMax[6]    // axis-aligned min/max extents     = 24 bytes
  Ref             skinInstanceRef   // -> NiSkinInstance / BSSkin::Instance (or -1)
  Ref             shaderPropertyRef // -> BSLightingShaderProperty       (or -1)
  Ref             alphaPropertyRef  // -> NiAlphaProperty                (or -1)
  // up to 4 mesh slots, each gated by a presence byte:
  repeat 4 times:
      uint8  present     // 1 = a BSGeometryMesh follows, 0 = skip
      if present: BSGeometryMesh mesh
```

The **4 mesh slots are the LOD levels** (slot 0 = LOD0/highest detail, slots 1–3 = successively coarser). NifSkope labels the array "Meshes". A shape may populate only slot 0.

**`bounds` / `boundMinMax` are load-bearing, and the convention differs by shape kind (verified
in-game 2026-07-11):**

- **Static (non-skinned) shapes**: `bounds` (sphere: centre + max-vertex-distance radius) **and**
  `boundMinMax` (**centre.xyz + half-extents.xyz**, *not* min/max corners — despite the name) must be
  real, non-zero, computed from the verts in metric (`.mesh`) space. A **zero bound makes a static
  invisible in-game AND in the Creation Kit** (the engine frustum/distance-culls it) even though the
  geometry is perfectly valid — Blender/NifSkope ignore bounds, so it still shows there.
- **Skinned shapes**: vanilla sets `bounds.radius = 0` and **`boundMinMax = all FLT_MAX`**
  ("infinite, never cull"). The mesh moves with the bones, so block-level culling is delegated to the
  per-bone bounds in `BSSkin::BoneData` (§3); a tight block AABB would cull the body the moment it
  animates. **Do not compute a real block AABB for a skinned shape — write the infinite sentinel.**

(Note: a widely-used NIF ctypes/wrapper layer may report these block bounds as zero even when the
file has real values — validate against raw bytes, not a parsed shape buffer.)

### `BSGeometryMesh` — the pointer to a `.mesh`

```
BSGeometryMesh
  uint32  triSize     // triangle-index count hint (== nTriIndices in the .mesh)
  uint32  numVerts    // vertex-count hint
  uint32  flags       // observed value: 64 (0x40)
  NiString meshName   // length-prefixed (4-byte length) path string
  // [when the mesh is EMBEDDED rather than external:] BSGeometryMeshData follows
```

`meshName` is the path to the external `.mesh` (see below). In modern NifSkope forks the field shows as **"Mesh Path"**. Some Starfield NIFs instead embed the mesh data inline as a **"Mesh Data"** sub-record (a `BSGeometryMeshData`, same binary body as the external file) — NifSkope and nifly handle both. The choice is controlled by **`BSGeometry.flags` bit `0x200` (512)** — nifly's `HasInternalGeomData()`: when set, each present mesh slot carries an inline `BSGeometryMeshData`; when clear, it carries an external `meshName` string. External is normal for shipped assets (better streaming from BA2); **internal geometry yields a single self-contained NIF with no `geometries/` dependency** — a useful option for a tool's first-pass export (Outfit Studio supports both).

### Hash-path scheme (`geometries/…`)

- In shipped assets `meshName` is **40 hex chars**, split into a 20-char subdirectory + 20-char filename → resolving to `Data/geometries/<20hex>/<20hex>.mesh` (a real example: `geometries/00000042477f47c194db/3cd02fb771e05b4ac1be.mesh`). The 40-hex name *appears* to be a digest.
- **But the name is NOT a computed/enforced hash** (corrected against nifly + Outfit Studio source). The game does not verify it, and the tooling does **not** hash the mesh bytes to form the filename — nifly writes the `meshName` string verbatim, and Outfit Studio derives human-readable names like `NifName\ShapeName_Index`. The only hashing in the pipeline is a **CRC32** (`SFResourceHash`) used for *material/archive resource-ID lookup*, not for `.mesh` filenames. → **Mod meshes can use arbitrary, human-readable paths.**
- The engine resolves the path inside `Starfield - Meshes01/02.ba2` (or as loose files under `Data/geometries/…`). The BA2 name table stores paths with **forward slashes**.
- **Gotcha (from the "creating a playable race" guide):** the mesh-path string stored in `BSGeometry → Meshes` **must be ≤ 46 characters** or the shape renders invisible in-game. Starfield Geometry Bridge defaults to `[object name]\[mesh name].mesh`, so keep object/mesh names short. This is another reason to use short human-readable names rather than long hex ones.
- **`geometries/` is one shared, flat namespace** — across the whole game *and every mod* (like `meshes/` / `textures/`; there's no per-plugin geometry folder for authored assets, unlike FaceGen which nests under `<Plugin>\`). Two mods that ship the same relative path (`geometries/head/head.mesh`) **collide**, resolved by normal override rules (loose beats archived; later archive beats earlier). Vanilla's 40-hex names make this *collision-resistant* (a 160-bit space → clashes are astronomically unlikely at modding scale) but **not collision-proof** — and only if the hash is over mesh *content*; if it's derived from a source path/name (unconfirmed — the tooling doesn't compute it, modders pick the string) even hashes wouldn't prevent two modders colliding on the same source name. The practical protection is the same as `meshes/`/`textures/`: **namespace every mesh under a short, unique mod-specific subfolder** (e.g. `geometries\MyModTag\canid_head.mesh`), within the 46-char budget — though that too is convention, not enforced (two mods can pick the same tag). Bottom line: collision-avoidance here is probability + discipline either way; readable-under-a-unique-folder just keeps it manageable. The exporter's "generate geometry hash" option leans on the hash odds but makes meshes unmanageable (can't tell them apart).
- **`.morph` (facegen) data lives separately** under `Data/meshes/morphs/…/morph.dat`, referenced from records rather than by hash. (See §5.)

### What nifly does and does NOT do

**Important for a NIF library / PyNifly** (verified against nifly `main` + Outfit Studio `dev` source): nifly parses the full `.mesh` binary via `BSGeometryMeshData::Sync()` and exposes **stream-based hooks** — `NifFile::LoadExternalShapeData(shape, std::istream&, meshIndex)` and `SaveExternalShapeData(shape, std::ostream&, meshIndex)`, plus `GetExternalGeometryPathRefs(shape)` to read the `meshName` strings — but nifly has **no file/archive I/O**: it never opens `geometries/` files or BA2s. The **caller** does path resolution + loose-file/BA2 lookup and hands nifly a stream (Outfit Studio does exactly this in `OutfitProject::GetExternalGeometryStream`). So a tool built on nifly gets the entire `.mesh` reader/writer *and meshlet generator* for free; the only new code is **(a)** resolve the mesh path against loose files / BA2, **(b)** open a stream, **(c)** loop over each shape × its up-to-4 mesh slots calling Load/Save. That resolve-and-open layer (especially BA2 extraction) is the single biggest addition versus the FO4/SSE importer.

---

## 2. The external `.mesh` binary format

Little-endian throughout. Layout below is cross-verified against **three independent readers**: nifly `BSGeometryMeshData::Sync` (`src/Geometry.cpp`), fo76utils NifSkope `src/io/MeshFile.cpp`, and SesamePaste233's StarfieldMeshConverter (`include/MeshIO.h`). They agree on field order and encodings.

### Top-level layout

| Offset (relative) | Type | Field | Notes |
|---|---|---|---|
| 0 | `uint32` | **version / magic** | 0, 1, or 2. Readers reject `> 2`. Controls presence of LOD section (see note). |
| +4 | `uint32` | `indicesSize` | total triangle **index** count (= 3 × numTriangles) |
| +8 | `Triangle[indicesSize/3]` | triangles | each `Triangle` = 3 × `uint16` vertex indices |
| … | `float` | **`scale`** | per-mesh position dequant scale (bounding extent). **If `scale <= 0`, readers abort** — a real "empty geometry" sentinel. |
| … | `uint32` | `weightsPerVertex` | bone influences per vertex (see §3) |
| … | `uint32` | `numVertices` | full 32-bit count (but see 65 535 limit below) |
| … | position[numVertices] | **vertex positions** | 3 × `int16`, 6 bytes/vertex — see quantization |
| … | `uint32` | `numUV1` | |
| … | UV1[numUV1] | UV set 0 | 2 × `float16` (half), 4 bytes each |
| … | `uint32` | `numUV2` | usually 0 |
| … | UV2[numUV2] | UV set 1 | 2 × `float16` |
| … | `uint32` | `numColors` | 0 if no vertex colors |
| … | color[numColors] | vertex colors | `BGRA` uint8 ×4, 4 bytes each |
| … | `uint32` | `numNormals` | |
| … | normal[numNormals] | normals | **UDEC3** packed, 4 bytes (uint32) each |
| … | `uint32` | `numTangents` | |
| … | tangent[numTangents] | tangents | **UDEC3** packed uint32; the 2-bit `w` = bitangent sign |
| … | `uint32` | `numWeights` | total weight entries = numVertices × weightsPerVertex |
| … | boneWeight[numWeights] | skin weights | `{uint16 boneIndex, uint16 weight}`, 4 bytes each |
| … | `uint32` | `numLODs` | *(only when version/magic ≥ 1; see note)* |
| … | per-LOD | LOD index buffers | each: `uint32 indicesSize2` then `Triangle[indicesSize2/3]` |
| … | `uint32` | `numMeshlets` | *(nifly reads; fo76utils stops before this)* |
| … | Meshlet[numMeshlets] | meshlets | 4 × `uint32` (see §meshlets) |
| … | `uint32` | `numCullData` | |
| … | CullData[numCullData] | cull bounds | see §meshlets |

**Version/LOD note:** fo76utils only reads the LOD section when `magic != 0` (`if (magic) { read LODs }`). nifly reads LODs unconditionally after weights. In practice shipped meshes are version 1–2. **Unverified:** exact behavioral difference for version-0 meshes; treat the LOD block as present for v1+.

**Vertex-count limit:** a `.mesh` can address at most **65 536** vertices because triangle indices are `uint16`. nifly stores `numVertices` in a 32-bit field but casts to `uint16` internally; the tri-index ceiling is the real constraint. Split meshes exceeding this, exactly as `[SSE]``[FO4]`.

### Position quantization (the metric-scale gotcha)

Positions are **signed-normalized int16 × a single per-mesh `Scale` float** (verified against fo76utils `MeshFile.cpp` and real vanilla `.mesh` bytes):

```
read:  pos = (int16 / 32767.0) * Scale          // uniform 32767 divisor, all 3 components
write: int16 = round((pos / Scale) * 32767.0)
```

> **⚠ Scale MUST carry margin — never set it to the exact largest coordinate (verified in-game
> 2026-07-11).** The encode/decode is symmetric (`×32767` / `÷32767`), so the *usable* `int16` range
> is **±32767** — yet `int16` actually reaches **−32768**. If `Scale` equals the mesh's exact max
> extent, the deepest verts encode right at the edge and float rounding pushes some to **−32768**, one
> step past the symmetric range. Such a vertex **decodes to the correct position** (so it looks right
> statically and in most viewers — this makes the bug nearly invisible to offline validation), but the
> **engine's *skinned* vertex path mishandles the SNORM extreme and flings those verts across the map
> when the skeleton poses them.** Observed: a body authored with `Scale = exact max` had its deepest
> foot verts fly to ~2× body height, dragged by their foot bone. Vanilla avoids this by design — the
> sampled body's `Scale = 2.0` sits well above its true max of ~1.63 (≈22% headroom). **Writers:
> multiply the computed max-extent scale by a safety margin (~10% is ample) so no vertex encodes near
> ±32767.** This is why vanilla scales look "rounded up," not tight.

There is **one `Scale` field, not a separate `max_border`** — `Scale` is the world value that `int16 = 32767` maps to (effectively the mesh's largest absolute coordinate / half-extent). Readers **abort if `Scale <= 0`** (empty-geometry sentinel). An earlier signed-asymmetric variant (`raw < 0 ? 32768 : 32767`) exists only in dead `#if 0` code — do not use it. Two sampled vanilla meshes (a static and the human body) both had `Scale = 2.0`, and positions decode into **metric-scale metres** (~±2 for a body), the departure from prior games' game-unit vertices. nifly multiplies by `havokScale = 69.969` on top to reach legacy game-unit sizes (see below).

- **fo76utils** renders these metric values directly.
- **nifly** multiplies each axis by an extra constant **`havokScale = 69.969`** (`Geometry.cpp`) so the numbers "closely match the older games" (SSE-sized). A comment notes `69.9866` was experimentally even closer (measured against `markerxheading.nif`). So **1 metre ≈ 69.97 Bethesda units** is the Starfield→legacy conversion factor.

> **PyNifly implication:** decide one convention. If you import raw metric and let Blender treat 1 unit = 1 m, armor will be ~1/70th the size of an SSE import. To match PyNifly's existing SSE/FO4 pipeline (game-unit space) multiply positions by ~69.97 on import and divide on export. Cross-check the constant against a known asset before committing (nifly itself is unsure between 69.969 and 69.9866).

### UDEC3 normals/tangents (10-10-10-2)

Normals and tangents are each one **`uint32` in DirectX `DXGI_FORMAT_R10G10B10A2` style**: three 10-bit unsigned channels + a 2-bit `w`.

```
decode: x = (( bits        & 1023) / 511.5) - 1.0     // range -1 .. +1
        y = (((bits >> 10) & 1023) / 511.5) - 1.0
        z = (((bits >> 20) & 1023) / 511.5) - 1.0
        w =  (bits >> 30)                              // 2-bit, tangent sign basis (0..3)
```

For **tangents**, the 2-bit `w` encodes the **bitangent handedness/sign**. The bitangent is reconstructed:

```
bitangent = cross(normal, tangent.xyz) * tangent.w
```

**Caveat / known bug:** nifly's `SyncUDEC3` *write* path uses `&=` instead of `|=` when packing the three channels (`BasicTypes.hpp` ~L360), so **nifly's normal/tangent *encoder* is broken** (reads are fine). An exporter must pack UDEC3 correctly itself. The nifly header also flags that bitangent reconstruction from the 2-bit sign is still a `FIXME`.

### UVs, colors

- **UVs:** `float16` per channel (half-precision), two per vertex, per set. Up to 2 sets; set 1 (`numUV2`) is almost always 0 in shipped assets.
- **Vertex colors:** stored **BGRA** as four `uint8`. Readers shuffle to RGBA on load (fo76utils `shuffleValues(0xC6)` = channels 2,1,0,3). nifly stores as `ByteColor4`.

### Meshlets & cull data

Starfield uses GPU **mesh shaders**, so each `.mesh` carries DirectXMesh-style **meshlet** partitions and per-meshlet **culling bounds**:

```
Meshlet  (nifly + DirectX::Meshlet):   16 bytes
    uint32 vertCount     // vertices in this meshlet
    uint32 vertOffset    // start into the meshlet vertex-index list
    uint32 primCount     // primitives (triangles) in this meshlet
    uint32 primOffset    // start into the meshlet primitive list
```

The **cull-data layout is version-dependent** (resolved from fo76utils `nif.xml` `BSCullData`, `arg="Version"`); there is one cull entry per meshlet (`Num Cull Data == Num Meshlets`):

```
version >= 2 (what shipped meshes use, and all the writer emits):  24 bytes
    float center[3]      // AABB center
    float dimensions[3]  // AABB half-extents from center

version < 2 (legacy DirectXMesh-style):  24 bytes = 6 words (NOT 8 floats)
    NiBound  boundingSphere   // Vector3 center + float radius   (16 B)
    ByteVector4  normalCone    // packed cone axis + spread        (4 B)
    float    apexOffset                                            // (4 B)
```

This resolves the earlier "AABB vs sphere+cone" ambiguity — **the file version selects between them**, and the writer only ever emits the version-2 AABB (`center=(min+max)/2`, `dims=(max−min)/2`). Note: *Bethesda reorders the global triangle array during meshlet generation*, so meshlet `Triangle Offset`/`Count` index into the re-ordered triangle list, not the mesh's authoring order.

> **PyNifly implication:** meshlets + cull data are **derived/rendering acceleration data** — ignore on import, **regenerate on export** (the game renders via mesh shaders and needs valid meshlets). The good news: **nifly already regenerates them** — `BSGeometryMeshData::GenerateMeshlets()` is a hand-rolled greedy grouper (max **128 verts / 128 prims** per meshlet) that also stamps `version = 2` and computes the per-meshlet AABB cull data. So on a `git merge upstream` PyNifly gets meshlet generation for free; no need to bind DirectXMesh/meshoptimizer. (fo76utils independently uses meshoptimizer/DirectXMesh at 96/128 — different generator, both produce game-valid meshlets, so exact meshlet partitioning need not match vanilla.)

---

## 3. Skinning & dismemberment

### Bone weights/indices (in the `.mesh`)

Per §2, skin data is a flat array of `numVertices × weightsPerVertex` entries, each `{uint16 boneIndex, uint16 weight}`:

- **`weightsPerVertex`** is a free `uint32` in the file with **no hard cap** (unlike `[SSE]`/`[FO4]`'s fixed 4). Verified against real assets: a **static mesh had 0** (unweighted) and the **vanilla human body had 6** weights per vertex. An importer must handle a variable count, not assume 4.
- **`weight`** is a normalized `uint16` (divide by 65535 for 0..1). fo76utils packs the pair as `(boneIndex << 16) | weight`.
- **`boneIndex`** indexes into the **bone-name list carried by the NIF** (see below) — the geometry-less `.mesh` has no bone *names*, only indices.

### Bone names & bind data (in the NIF)

The `.mesh` carries indices only; the **skeleton binding lives in the NIF**. Verified against a real vanilla body NIF (`naked_f.nif`), a skinned Starfield shape carries **three** skin-related blocks:

- **`SkinAttach`** — holds the **bone-name list as strings**: `uint32 nameStringIdx` (e.g. "SkinBMP"), `uint32 numBones`, then `numBones` length-prefixed (`uint32`) bone-name strings. The `.mesh`'s `boneIndex` values index into **this** ordered list. (A geometry-less body NIF contains no `NiNode` blocks for the skeleton's bones — those live in `skeleton.nif` — so the names must be carried here as strings.) The sampled body listed **38** skin bones.
- **`BSSkin::Instance`** — the skin-instance block (skeleton-root ref + skin-instance data), the Starfield analog of the FO4 `BSSkin::Instance`.
- **`BSSkin::BoneData`** — per-bone bind data: `{BoundingSphere bounds, MatTransform skinToBone}` per bone (plus scales). Bounding spheres are culling data recomputed on export.

**There is no `BoneTranslations` block** (an earlier guess) — the per-bone transforms are in `BSSkin::BoneData`.

#### Authoring requirements for a valid skinned body (all verified in-game 2026-07-11)

Reading a skinned SF body is forgiving; **writing** one that the engine and Creation Kit accept has
several non-obvious hard requirements. Each of these, when wrong, produced a distinct failure on an
otherwise byte-correct authored body:

- **`SkinAttach` extra-data NAME must be `"SkinBMP"`** (Skin **B**one **M**a**P**). It is a
  `NiExtraData` on the shape; its name is how the engine locates the shape's bone map. An **unnamed**
  `SkinAttach` leaves the engine unable to resolve the `.mesh`'s bone indices → the body falls back
  toward bind space (lies on its side) with garbage bone transforms (spazzes).
- **`BSSkin::Instance.boneRefs` must have exactly `numBones` entries, each an EMPTY ref** (`-1` /
  `NIF_NPOS`). SF bodies have no `NiNode` skeleton bones in the file (they're in `skeleton.nif`), so
  every ref is empty — but the **array length must still equal the bone count**. The engine/CK walk
  `boneRefs` in lockstep with the bone data; a length-0 array runs the iterator off the end →
  **`EXCEPTION_ACCESS_VIOLATION` (null deref) when the CK opens an actor using the mesh.** (nifly
  preserves the empty refs on write via `SetKeepEmptyRefs` for SF.)
- **`BSSkin::BoneData` per-bone bounding spheres must be non-zero.** Each bone entry is
  `{BoundingSphere bounds, MatTransform skinToBone}`. The sphere bounds that bone's weighted verts in
  bone-local space (`skinToBone · vert`). Leaving it at the default zero radius **crashes the CK** on
  actor load (it reads these as skin culling data). Recompute per bone on export.
- **A skinned shape's own `BSGeometry` transform must be IDENTITY** (translation 0, identity rotation,
  scale 1). The `skinToBone` binds already place every vertex; writing the object/placement transform
  onto the shape too **double-applies it and the mesh explodes under animation.** (Only *static*,
  non-skinned shapes carry a placement transform — see §1.)
- **`BSXFlags` (name `"BSX"`) on the root node = `0x10000` (65536)** on skinned bodies. Add it if
  absent.
- **Vertex `Scale` must carry margin** (see §2 "Position quantization") — a zero-margin scale flings
  the extreme (foot) verts to ~2× body height in-game.

**Phase-2 note (resolved):** the engine resolves `boneIndex` → bone via the **`SkinAttach` string
names**, not `boneRefs` (which are all empty for SF bodies). `SkinAttach`, `BSSkin::BoneData`, and the
`.mesh` weight indices must all share one consistent bone order; the *order itself* is free (need not
match vanilla), but the three must agree.

**PyNifly implication:** import resolves `boneIndex` → bone name through the NIF's `BSSkin::Instance` bone list, then builds a Blender armature exactly like the SSE/FO4 path. Export must (a) emit `{boneIndex, uint16 weight}` in the `.mesh`, and (b) build the matching bone list + bone-data (bind transforms, bounding spheres) in the NIF.

### The `.mesh` verts are in a per-shape *skin bind space*, not a shared space

A crucial and easily-missed consequence of the above: **the raw `.mesh` vertex positions are in each shape's own skin bind space and are meaningless in isolation** — the actual placement onto the skeleton comes *entirely* from the per-bone `skinToBone` transforms in `BSSkin::BoneData`. Different shapes that skin to the same skeleton can be stored in wildly different raw spaces. Measured against real vanilla `.mesh` bytes (positions ×`havokScale`):

| Shape | Long axis | Raw extent | Reads as |
|---|---|---|---|
| `naked_f` body | **X** | X −114…−8 (span ~106), Z ±27 | body lying roughly **horizontal along −X**, centered ≈ X −61 |
| `outfit_ajun` torso | **Z** | Z −50…−3 | standing, shoulders/neck ≈ origin |
| `outfit_ajun` pants | **Z** | Z −110…−37 | standing, waist→ankle |
| `outfit_ajun` shoes | **Z** | Z −114…−107 | standing, at the feet |

The naked body and the clothing weight to the **same** Starfield human skeleton, yet the body is stored horizontal along X while the clothes are stored vertical. Their `BSSkin::BoneData` bind transforms reconcile both onto the standing character.

> **Tool implication:** an importer that plots raw `.mesh` positions **without applying the bind transforms** will show the body lying on its side along X and the clothing hanging below the origin — *not* a bug in the reader, and *not* a quantization/recenter artifact (positions are int16-SNORM×`Scale` spanning the full body extent, **not** an FO4-style half-precision recenter). To place shapes correctly (and to align a body with its clothing), read `BSSkin::BoneData`'s per-bone `skinToBone` and build the armature at those bind positions, then bind the mesh — exactly the SSE/FO4 skin-bind step. In Starfield the bone binding is **indexed by position** (the `.mesh` carries only indices), so resolve bind transforms by bone index, not by a node-name lookup.

### Dismemberment — bone-driven, no mesh-side data (resolved)

`[FO4]` did dismemberment in the geometry: `BSSubIndexTriShape` segments/subsegments + an external
`.ssf`. **Starfield dropped that entirely.** Verified two ways:

- The real vanilla body NIF (`naked_f.nif`) has **no `BSDismemberSkinInstance` and no segment array** —
  just `BSGeometry` + `SkinAttach` + `BSSkin::*`. (nifly still *defines* the old `BSGeometrySegmentData` /
  `BSSubIndexTriShape` classes, but `BSGeometry` has no segment array and shipped bodies use none.)
- Dismemberment moved to the **record level, defined entirely by bone**: `RACE.GNAM` → a **`BPTD`
  (Body Part Data)** record whose parts are skeleton nodes — each `Body Part` = `BPNN` "Part Node" (a
  bone) + health %, VATS target bone, `NAM4` gore target bone, `ENAM/FNAM` hit-reaction start/end bones,
  and blood material (`MaterialActorSkin`). There's one `BPTD` per race (`HumanBodyPartData`,
  `ChildBodyPartData`, one per creature — 28 total). Gore stumps are supplied by the **"Meatcaps" HDPT**
  type, not by cutting geometry.

**Implications:** there is **nothing dismemberment-related for a mesh importer/exporter to round-trip** —
the `.mesh`/NIF carry no segment data. A custom (e.g. anthro) race inherits `HumanBodyPartData` via
`GNAM` and gets bone-based gore/severing for free on the human skeleton; the only optional work is
race-appropriate **Meatcaps** if you want severed stumps to look right.

---

## 4. Bodypart vs. armor NIFs

Structurally a Starfield bodypart NIF and an armor NIF are the same kind of tree — `NiNode` root → `BSGeometry` shape(s) → external `.mesh` + `BSLightingShaderProperty` (referencing an external material) + `BSSkin::Instance`. Differences are in **which skeleton bones are weighted and how the body is partitioned into slots**, driven by the game's slot/biped system rather than by NIF structure.

- **Body** is split into parts (torso, arms, hands, legs, feet, head/neck) as separate `BSGeometry` shapes so armor can hide/replace individual pieces — analogous to Skyrim partitions but expressed as separate shapes + slots.
- **Layout in the raw `.mesh` differs by asset class** (see §3 "skin bind space"): sampled vanilla **clothing** (`outfit_ajun_*`) is authored **vertical along Z with the neck/top at the origin and the body hanging into −Z** (a full outfit spans Z ≈ 0 down to ≈ −1.6 m), while the sampled **naked body** is stored **horizontal along −X**. Don't read either raw layout as the in-game pose — both are just bind spaces resolved by `BSSkin::BoneData`. (The clothing "head-at-origin" convention is handy to know when eyeballing an un-bound import.)
- **Slots** are defined in the ESM records (ARMO/ARMA "biped object" flags), not in the NIF geometry. **Unverified:** the exact Starfield slot table and how it maps to bodypart shapes — a sibling investigation (chargen) and the CK docs cover the record side.
- **Skeleton:** Starfield's human skeleton and bone naming differ from Skyrim/FO4; a furry/anthro race must weight to Starfield's actual bone names. Extract these from a vanilla body `.mesh` + NIF skin instance.

**Open:** whether a custom anthro race needs new body `.mesh` files per slot, or can reuse vanilla partition boundaries with re-weighted geometry. Likely the former for non-human proportions.

---

## 5. `morph.dat` files (chargen reshape + expression morphs)

Overview here; the [chargen page](chargen.md) covers morphs and the authoritative binary layout in depth. Starfield stores per-vertex morph/blendshape deltas in **`morph.dat`** files (under `Data/meshes/morphs/…`), parallel to the `.mesh` they morph. The **same format serves two distinct roles** (split by folder — `chargen/` vs `performance/`):

- **Chargen morphs** — *reshape facial features*: the character-creator sliders and phenotype presets (chin/forehead/nose/…).
- **Performance morphs** — *expressions + lip-sync*: FACS-style action units driven at runtime in dialogue/emotes.

Layout per StarfieldMeshConverter (`include/MorphIO.h`, `MorphIO.py`) — see the chargen page for the byte-verified `MDAT` layout:

- A JSON-ish header (`num_axis`, `num_shape_keys`, `num_vertices`, `morph_names[]`) plus packed per-vertex delta records.
- **Per-vertex, per-morph delta record (`morph_data`, packed form):**
  ```
  uint16 offset[3]        // position delta, half-float (x,y,z)
  uint16 target_vert_color
  uint32 x, y             // packed delta normal + delta tangent (DEC3N)
  ```
- **Expanded/high-fidelity form (`morph_data_hf`, 16 bytes):** `float offset[3]` (position delta), `float target_vert_color`, `float nx,ny,nz` (delta normal, DEC3N), `float tx,ty,tz` (delta tangent, DEC3N).
- Morphs are **sparse**: only vertices touched by a given morph key store a record, with a per-vertex bitmask selecting which morph keys affect it (the byte-verified layout uses a 4×`uint32` marker → **up to 128 morph keys** — see the chargen page).

**PyNifly relevance:** morphs matter for heads/facegen, not static armor — but for an **anthro race a muzzle/head needs both kinds, and neither is optional for a good result**: the **performance** set so the face emotes and lip-syncs in dialogue (without it the face is frozen), and the **chargen** set so the player can customize the face in the creator. Deltas are in the same metric/DEC3N encoding family as the base `.mesh` (positions ÷ havokScale), so the same scale + UDEC3/DEC3N handling applies.

---

## Quick reference: encodings

| Data | Encoding | Bytes |
|---|---|---|
| Triangle index | `uint16` | 2 |
| Vertex position | `int16` signed-norm × `scale` (metric metres) | 6 (×3) |
| UV | `float16` × 2 | 4 |
| Vertex color | `uint8` BGRA | 4 |
| Normal / tangent | UDEC3 = R10G10B10A2 uint32 | 4 |
| Bone weight entry | `uint16 boneIdx` + `uint16 weight` | 4 |
| Meshlet | 4 × `uint32` | 16 |
| Cull data (AABB) | 6 × `float32` | 24 |
| Legacy→Starfield scale | `1 m ≈ 69.969 Bethesda units` (nifly) | — |

---

## Sources

- nifly (local, authoritative for the blocks PyNifly links against): `include/Geometry.hpp`, `src/Geometry.cpp` (`BSGeometry`, `BSGeometryMesh`, `BSGeometryMeshData`, `Meshlet`, `CullData`, `BSGeometrySegmentData`, `havokScale`), `include/BasicTypes.hpp` (`NiVersion::IsSF`, `getSF`, `SyncUDEC3`, `SyncHalf`). Upstream: https://github.com/ousnius/nifly
- fo76utils NifSkope fork, `.mesh` reader: https://github.com/fo76utils/nifskope/blob/develop/src/io/MeshFile.cpp ; meshlet code: https://github.com/fo76utils/nifskope/blob/develop/lib/meshlet.cpp
- SesamePaste233 StarfieldMeshConverter (Starfield Geometry Bridge): https://github.com/SesamePaste233/StarfieldMeshConverter — `include/MeshIO.h`, `include/MorphIO.h`, `scripts/tool_export_mesh/MeshIO.py`, `SFGBDocs/`
- Starfield Geometry Bridge (Nexus): https://www.nexusmods.com/starfield/mods/4360
- "Organization of Starfield's Meshes and Related Assets" (article 268): https://www.nexusmods.com/starfield/articles/268 (mirror: https://allmods.net/starfield-mods/starfield-miscellaneous/organization-of-starfields-meshes-and-related-assets/)
- NifSkope Starfield support tracking issue (partial 010 template, format discussion): https://github.com/niftools/nifskope/issues/232
- NifSkope for Starfield (Nexus): https://www.nexusmods.com/starfield/mods/10748

_Draft 2026-07-06 — not yet reviewed_
