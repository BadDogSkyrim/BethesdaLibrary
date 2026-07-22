# Starfield File Formats

Starfield (Creation Engine 2) keeps the broad shape of a Bethesda game — a NIF
scene graph, TES4-family plugins, BA2 archives, DDS textures — but rebuilt almost
every format underneath. If you know `[FO4]`/`[SSE]` modding, the concepts
transfer; the file layouts do not. This section documents the Starfield-specific
formats, with an eye toward character/body/armor work.

> **Scope note:** every page in this section is Starfield-only. Facts are tagged
> `[FO4]` / `[SSE]` / `[Skyrim]` only where they contrast with an older game.
> Details drawn from reverse-engineered community tooling (nifly, xEdit/SF1Edit,
> StarfieldMeshConverter, fo76utils NifSkope) are marked where confidence is
> partial; treat **Unverified** notes as "confirm against a shipped asset."

## The five headline changes

| Area | `[FO4]` / `[SSE]` | Starfield |
|---|---|---|
| **Geometry** | Vertices embedded in the NIF (`BSTriShape`) | NIF is a container; geometry lives in external **`.mesh`** files referenced by a `BSGeometry` block via a mesh-path string |
| **Materials** | Flat `BGSM`/`BGEM` text files | Layered, graph-based **`.mat`** (JSON) compiled into a material database (`.cdb`) |
| **Morphs** | `.tri` files | **`morph.dat`** delta files + a `MRPH` "Morphable Object" record |
| **Tints / skin** | Fixed RACE tint-mask layers | Stackable **AVM** system (`AVMD` records) + layered-material swaps (`LMSW`) |
| **Plugins** | Flat subrecord records | **Component system** (`BFCB`/`BFCE` base-form components); new medium master tier; BA2 v2/v3 |

Two more that matter for characters: **animation** moved to an in-house system
(`.agx`/`.af`, not Havok — no public behavior-graph authoring tool), and the
skeleton was renamed to a clean `C_`/`L_`/`R_` bone convention.

## How the pieces fit together

```
Plugin (.esm, component-based records)
  ├─ RACE ──▶ WNAM Skin (ARMO) ──▶ ARMA addons ──▶ .nif container
  │            │                                        └─▶ BSGeometry ──▶ geometries\hex1\hex2.mesh
  │            ├─ Skeleton Data ──▶ skeleton.nif
  │            ├─ Chargen & Skintones ──▶ face dials, morph phenotypes, AVM skin tones
  │            ├─ Head Parts ──▶ HDPT ──▶ MRPH ──▶ morph.dat
  │            └─ Bone Modifiers ──▶ BMOD (SpringBone / LookAtChain …)
  ├─ HDPT / ARMO / ARMA ──▶ .nif ──▶ BSGeometry ──▶ .mesh (+ BSSkin bone list)
  └─ TXST ──▶ .mat (layered material) ──▶ .dds (BC7/BC5/BC4 PBR set)
Assets packed in <Plugin> - Main.ba2 (meshes/geometries/materials) + Textures.ba2 (BTDX v2/v3)
```

## Pages in this section

- **[Meshes: NIF + external `.mesh`](meshes.md)** — the geometry-less NIF,
  the `BSGeometry` block, and the external `.mesh` binary format (int16-SNORM
  metric positions, UDEC3 normals, meshlets, `SkinAttach` skinning). The core of
  any importer/exporter.
- **[Materials & Textures](materials.md)** — the layered `.mat`/`.cdb`
  system, shader-model templates (incl. skin/hair), texture slots and DDS
  conventions, and how to map it to a Blender shader.
- **[Chargen, Race & Skeleton](chargen.md)** — RACE/HDPT/MRPH/BMOD/AVMD,
  morphs, the skeleton, adding a tail/ears, FaceGen, and a realistic assessment of
  what a **custom (e.g. anthropomorphic) playable race** actually requires.
- **[Plugins & Archives](plugins.md)** — the component record system,
  master tiers and FormID ranges, the records a body/armor/race mod edits, and the
  BA2 v2/v3 archive format.

## Tooling landscape

The de-facto community tools for Starfield's new formats: **NifSkope (fo76utils
fork)** for viewing/editing NIFs and materials; **StarfieldMeshConverter /
Starfield Geometry Bridge** (Blender 3.5–3.6) for `.mesh`/`morph.dat` I/O;
**Outfit Studio** (built on `ousnius/nifly`) for body/outfit `.mesh` + `morph.dat`;
**SF1Edit** (xEdit) for records; the **Creation Kit** for FaceGen/chargen; and
**CharGenMenu** (SFSE) for exposing custom character-creator sliders.

See the **[Tools](tools.md)** page for the full directory, grouped by task.

_Draft 2026-07-06 — not yet reviewed_
