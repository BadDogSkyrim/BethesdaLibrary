# Fallout 4

Fallout 4 runs on the 64-bit Creation Engine. It keeps the Bethesda format
family — TES4-style plugins, NIF meshes, Havok animation/physics, Papyrus
scripts — but adds several things Skyrim doesn't have: external `.bgsm`/`.bgem`
material files, mesh **segments** (for runtime dismemberment and material
swaps), **connect points** for runtime attachment, **BA2** archives, and **ESL**
("light") plugins.

The `` `[FO4]` `` tags below mark what's specific to Fallout 4. Untagged pages
document the shared format — read them for the common structure, then note the
Fallout 4 differences.

## Formats

- **[Plugins (ESP/ESM/ESL)](../../file-formats/plugins.md)** — record structure, FormIDs, master resolution. `[FO4]` introduced the ESL "light" plugin tier.
- **[NIF Files](../../file-formats/nif-files.md)** — `[FO4]` `BSTriShape` geometry; `BSSubIndexTriShape` (SITS) carries the mesh **segments** used for dismemberment and material swaps.
- **[NIF Animations](../../file-formats/nif-animations.md)** — scene-graph object animations (doors, terminals, enchant/effect glow) embedded in the mesh.
- **[Animations (HKX)](../../file-formats/animations.md)** — Havok skeleton and animation files. `[FO4]` uses the 64-bit `hk_2014.1.0-r1` Havok format.
- **[Physics & Collision](../../file-formats/physics-collision.md)** — Havok rigid-body collision and cloth.
- **[Morphs & Shape Keys](../../file-formats/morphs-shapekeys.md)** — `.tri` morphs for FaceGen/chargen and BodySlide.
- **[Textures & Materials](../../file-formats/textures-materials.md)** — DDS textures. `[FO4]` moves material/shader settings out of the NIF into external **`.bgsm`** (lighting) / **`.bgem`** (effect) material files.
- **[Archives (BA2/BSA)](../../file-formats/archives.md)** — `[FO4]` packs assets in **BA2** archives, replacing Skyrim's BSA.
- **[Scripts (PEX)](../../file-formats/scripts.md)** — compiled Papyrus, attached to records via VMAD.

## Fallout 4-specific pages

- **[Connect Points](connect-points.md)** — named attachment points for snapping one mesh onto another at runtime (weapon mods, workshop objects).
- **[Dismemberment](dismemberment.md)** — runtime limb severing via `BSSubIndexTriShape` segments and the `.ssf` segment file.

_Draft 2026-07-10 — not yet reviewed_
