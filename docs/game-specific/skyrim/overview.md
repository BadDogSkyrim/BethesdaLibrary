# Skyrim

Skyrim ships in two editions that share almost all formats but differ in a few
load-bearing ways:

- `` `[LE]` `` **Legendary Edition** ("Oldrim") — 32-bit. `NiTriShape` /
  `NiTriStrips` geometry, 32-bit Havok, BSA v104.
- `` `[SSE]` `` **Special Edition** — 64-bit. `BSTriShape` / `BSDynamicTriShape`
  geometry, 64-bit Havok (LE animations must be converted), BSA v105, and later
  gained `[SSE]` ESL "light" plugin support.

Most authoring (records, meshes, textures, morphs) is identical between the two;
the edition tags below flag where they diverge. Untagged pages document the
shared format, which Skyrim also has in common with Fallout 4.

## Formats

- **[Plugins (ESP/ESM)](../../file-formats/plugins.md)** — record structure, FormIDs, master resolution. `[SSE]` supports ESL "light" plugins; `[LE]` does not.
- **[NIF Files](../../file-formats/nif-files.md)** — `[LE]` `NiTriShape` / `NiTriStrips`; `[SSE]` `BSTriShape` and `BSDynamicTriShape` (morphable head/body with dynamic vertices). Body meshes use the **`SBP_*` partition** system to hide regions covered by armor — the partitions are defined on the [NIF Files](../../file-formats/nif-files.md) page, with the complete slot list in [Partition Names](../../reference/partition-names.md).
- **[NIF Animations](../../file-formats/nif-animations.md)** — scene-graph object animations (doors, banners, mill wheels, enchant glow) embedded in the mesh.
- **[Animations (HKX)](../../file-formats/animations.md)** — Havok skeleton and animation (`hk_2010.2.0-r1`). `[SSE]` uses 64-bit HKX; `[LE]` 32-bit files are not cross-loadable without conversion.
- **[Physics & Collision](../../file-formats/physics-collision.md)** — Havok collision, plus skinned-mesh physics via HDT-SMP (and `[LE]` HDT-PE).
- **[Morphs & Shape Keys](../../file-formats/morphs-shapekeys.md)** — `.tri` expression morphs, RaceMenu chargen sliders, BodySlide.
- **[Textures & Materials](../../file-formats/textures-materials.md)** — DDS textures. Skyrim keeps material/shader settings **inline** in the NIF's `BSLightingShaderProperty` — the external `.bgsm`/`.bgem` material files are `[FO4]`.
- **[Archives (BSA)](../../file-formats/archives.md)** — `[LE]` BSA v104, `[SSE]` BSA v105.
- **[Scripts (PEX)](../../file-formats/scripts.md)** — compiled Papyrus, attached to records via VMAD.

_Draft 2026-07-10 — not yet reviewed_
