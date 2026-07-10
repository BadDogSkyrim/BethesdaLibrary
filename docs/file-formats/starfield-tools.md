# Starfield Modding Tools

A directory of the tools used to work with Starfield's file formats, grouped by task.
Because Starfield's formats are new (geometry-less NIF + external `.mesh`, layered `.mat`
materials, component-based plugins, in-house `.agx` animation), most of these are
community-built and evolve fast — **check each project for its current version/state.**
This is a landscape map; the format pages ([meshes](starfield-meshes.md),
[materials](starfield-materials.md), [chargen](starfield-chargen.md),
[plugins](starfield-plugins.md)) are where the details live.

Two ecosystem facts worth knowing up front:

- **`fo76utils/nifskope` is the de-facto Starfield NifSkope** — the official niftools NifSkope
  viewport is largely non-functional for Starfield assets.
- The main Blender mesh tool (**Starfield Geometry Bridge**) is **pinned to Blender 3.5/3.6** and
  breaks on 4.0+ — the biggest gap in the modern-Blender tooling story.

---

## Meshes & geometry (NIF / `.mesh`)

| Tool | What it does | Notes |
|---|---|---|
| **Starfield Geometry Bridge** / **StarfieldMeshConverter** (SesamePaste233) | Blender plugin: import/export `.nif`, external `.mesh`, `morph.dat`, and Havok cloth/physics | The de-facto Blender mesh pipeline. **Blender 3.5–3.6 only** (breaks on 4.0+). `src/MeshIO.cpp`/`MorphIO.cpp` are the byte-level format reference. Nexus 4360; GitHub `SesamePaste233/StarfieldMeshConverter`; docs `starfieldgeometrybridge.github.io` |
| **NifSkope (fo76utils fork)** | View/edit Starfield NIFs; read `.mesh` (internal + external), meshlet generation, `.cdb`/`.mat` materials, LOD v1↔v2, NiTriShape↔BSGeometry conversion | The **de-facto Starfield NifSkope**. GitHub `fo76utils/nifskope`; Nexus 10748 |
| **Outfit Studio / BodySlide** (ousnius) | Body/outfit editing: reads/writes SF `.mesh` (internal & external), builds `morph.dat`, previews `.mat`; loads a reference body | Built on `nifly`. Internal-geometry mode (BSGeometry flag `0x200`) yields self-contained NIFs. GitHub `ousnius/BodySlide-and-Outfit-Studio` (`dev`); SF-focused fork `DJLegends1011` |
| **nifly** (ousnius) | C++ NIF library — the engine under Outfit Studio; parses `BSGeometry`/`BSGeometryMeshData`, external-mesh stream I/O, meshlet regen | Library, not an app. GitHub `ousnius/nifly` |
| **PyNifly** (Bad Dog) | Blender NIF import/export addon (Skyrim/FO/FO76) — **Starfield support in development** | Targets modern Blender; the project adding SF `.mesh` support to fill the 3.5/3.6 gap. GitHub `BadDogSkyrim/PyNifly` |
| **Male/Female Body Blender Template** | Vanilla body reference meshes for Blender | Nexus 5455 / 13117 |
| **`.nif` Mesh Path Migration Tool** | Fixes mesh-path references after the SF 1.11.36 mesh-path reorganization | Nexus 9234 |

## Materials & textures

| Tool | What it does | Notes |
|---|---|---|
| **Starfield Material Exporter (SFME)** (maximusmaxy) | Author/edit `.mat` materials; exports a **loose JSON `.mat`** (no `.cdb` compile needed). Also extracts `.mat` from the `.cdb` — **but its `.cdb` reader OOMs on the current v4 database** (see note below) | GitHub `maximusmaxy/SFME`; Nexus 7830 |
| **NifSkope (fo76utils fork)** | Also exports materials — "Material → Copy JSON / Clone / Save as New" writes a loose `.mat` | See Meshes section |
| **Material Editor Lite** | Lighter `.mat` editing | Nexus 14659 |
| **Gibbed.Starfield** | Reads/tools the compiled material database `materialsbeta.cdb` | GitHub `gibbed/Gibbed.Starfield` (read-focused). Verify against a current **v4** `.cdb` before relying on it (see note) |
| **PyNifly** (Bad Dog) — `pyn/sf_cdb.py` | Pure-Python **v4-aware `.cdb` reader**: dumps compiled materials → loose JSON `.mat`. `python -m pyn.sf_cdb <cdb> <mat-path\|list.txt> [outdir]` | Reads the 33-byte v4 `ObjectInfo` the older readers miss (48,755 materials in the shipped DB). GitHub `BadDogSkyrim/PyNifly` (SF support in development) |
| **AssetWatcher** | Converts source TIFF textures → DDS (PC + Xbox) | **Ships with the Creation Kit** |
| **fo76utils / ce2utils** | Material dump / `mat_names.txt` extraction; NifSkope's `sfmatexport` writes a loose `.mat` per material | GitHub `fo76utils/ce2utils`. `.cdb`-reader coverage of the v4 layout unverified — check against a current DB |

> No tool ships a `.cdb` *writer* — but none is needed: the game loads loose JSON `.mat` at runtime.

> **Extracting editable `.mat` from the `.cdb`.** The compiled database is read-only, so to edit a
> vanilla material you *dump* it to loose `.mat`. Two current gotchas:
> 1. **It's packed and compressed.** The DB lives inside `Data\Starfield - Materials.ba2` at
>    `materials\materialsbeta.cdb` (~17 MB compressed → ~105 MB) — extract with **BSArch** first. A
>    0-byte output means a botched extract.
> 2. **The format bumped to version 4** (game build ≥ 1.16.244). Its internal `ObjectInfo` record grew
>    **21 → 33 bytes** (v4 now stores the parent's full 12-byte `BSResource::ID`). Readers built for the
>    old 21-byte layout — **SFME and the whole `MaxieStarfieldScripts` lineage** — misalign on the
>    *first* object, read a garbage list length, and **run away allocating memory until they OOM**. This
>    is the "cdb version mismatch" people hit. A **v4-aware reader is required**: PyNifly's
>    `pyn/sf_cdb.py` is a known-working one; older `.cdb` readers (fo76utils, Gibbed) may predate v4 —
>    verify against a current database.

## Plugins & records

| Tool | What it does | Notes |
|---|---|---|
| **SF1Edit / xEdit** (TES5Edit team) | The record editor — copy/override records, wire FormID links, compact FormIDs, conflict detection | Run as `xSFEdit.exe` or `xEdit.exe -sf1`. Record definitions in `Core/wbDefinitionsSF1.pas` |
| **SF1Dump / xDump** | Headless record dumper (part of the xEdit suite) — dumps decoded records to text; `-dg:<SIG>` limits to one top-level group | Great for scripted record enumeration/inspection without the GUI |
| **Creation Kit (Starfield)** | Bethesda's official SDK — FaceGen baking (Ctrl+F4), chargen/preview, record editing | Steam app 2722710 (free). Launched June 2024 |
| **Creation Kit Platform Extended (CKPE)** | Community stability/QoL patch for the CK (e.g. `TintMaskResolution` tunable) | Nexus 11802 |

## Archives (BA2)

| Tool | What it does | Notes |
|---|---|---|
| **BSArch** (zilav / ElminsterAU / Sheson) | Pack/unpack BA2 — native `-sf1` (GNRL) and `-sf1dds` (DX10) support; **runs headless** | Ships with the xEdit suite. CLI: `BSArch unpack <archive> [folder]`, `BSArch pack ... -sf1` |
| **Bethesda Archive Extractor (BAE)** | Extract BA2 contents | Added Starfield in v0.13 |
| **Bethesda Archive Manager** | Create/extract Starfield BA2 | Nexus 14468 |
| **BA2 Upgrader** | Converts v2 DX10 texture archives → v3 (optimized VRAM streaming) | Nexus 1192 |

> Starfield BA2 = `BTDX`; **GNRL is always v2**, DX10 is **v2 or v3** (base-game `Textures01–09` are v3).

## Character creation / chargen

| Tool | What it does | Notes |
|---|---|---|
| **CharGenMenu** (expired6978) | SFSE plugin — adds custom chargen sliders/morph targets via JSON, numeric sliders, preset save/load. The "RaceMenu for Starfield" (same author as Skyrim RaceMenu / FO4 LooksMenu) | Requires SFSE. Nexus 6850. Slider JSON `Key` must match a `morph.dat` morph name |
| **CharGen Resources** + **RTFP** | Modder's resource + a config-driven runtime FormID patcher (`[AVMData]`/`[FormList]` `add_entr`) for adding chargen options (AVM groups, headpart form-lists) without hand-editing in xEdit | Nexus 8736; tutorial article 481 |
| **Body Morph Console** | Drive 100+ body morphs at runtime via console (incl. on NPCs) — only morphs already in the model | Nexus 9427 |
| **Extended Facial Sculpting** | Adds face-bone sliders (successor to the FO4 mod) | Nexus 6595 |

## Skeleton, animation & physics

| Tool | What it does | Notes |
|---|---|---|
| **SF Extended Skeleton** (Allnarta) | Adds ~37–38 bones to the human skeleton (tail, ears, breast, belly, genitals…) for cloth/physics appendages | Nexus 16905. Added bones move via cloth/NAF, **not** the native animation graph |
| **NAF (Native Animation Framework)** / **SAF (Deputy NAF)** | Custom animation via glTF played on top of the game's animation system (override, not replace); SAF adds bone-name aliasing | Nexus 7360 / 16124. The working custom-animation path |
| **Starfield Behavior Editor** (Monitor221hz) / **CALUMI Motion** | View/research vanilla `.agx` behavior graphs | GitHub `Monitor221hz/Starfield-Behavior-Editor`; Nexus 16181. **Alpha — view/research only; full `.agx` authoring does not yet exist** |
| **Havok Content Tools 2014** (`hctStandaloneFilterManager`) | Bake Havok cloth (`BSClothExtraData`) for bone-deforming cloth (hair/tails) | Starfield keeps Havok for physics/cloth only, not animation |

## Reverse-engineering / development

| Tool | What it does | Notes |
|---|---|---|
| **SFSE (Starfield Script Extender)** | The script extender that runtime plugins (CharGenMenu, NAF, …) build on | Required by most framework mods |
| **CommonLibSF** (Starfield-Reverse-Engineering) | Reverse-engineered C++ headers for the game's runtime structures — the reference for SFSE-plugin authors | GitHub `Starfield-Reverse-Engineering/CommonLibSF` |

## Asset optimization & packaging

| Tool | What it does | Notes |
|---|---|---|
| **Cathedral Asset Optimizer** | Optimize/compact assets; package into BA2 | Common in facegen/asset-shipping workflows |
| **"NPCs Face Data" (Synthesis patcher)** | Injects the correct masters so the CK can resolve an NPC's face data before FaceGen baking | Fixes the "CK won't load the face" problem |

---

## Where PyNifly fits

The dominant Blender mesh tool (Starfield Geometry Bridge) is pinned to Blender 3.5/3.6, so there's
no maintained path for authoring Starfield geometry in modern Blender. [PyNifly](../tools/pynifly/overview.md)
— which already targets current Blender for Skyrim/Fallout — is adding Starfield `.mesh` import/export
to fill that gap. It builds on `nifly` (which carries the SF `BSGeometry`/`.mesh` support), so the new
work is the Blender-side representation plus loose-file `.mesh` resolution, not a from-scratch parser.

## Sources

Tool references were gathered across this Library's Starfield format research; Nexus mod IDs and
GitHub repository names are given inline. Verify current versions and compatibility at each project,
as the Starfield tooling ecosystem changes quickly.

_Draft 2026-07-08; `.cdb` extraction / v4-format tooling added 2026-07-10 — not yet reviewed_
