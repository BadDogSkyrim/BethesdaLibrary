# External Resources

A directory of useful external references — wikis, tool repositories, format
specs, tutorials, and articles — for Bethesda modding. This page is **seeded from
the links already cited across this library**; for the full context of any entry,
see the `Sources` / `See Also` section of the page that cites it.

> Auto-seeded and lightly annotated — expect some rough labels; prune and annotate
> as the library matures. Nexus mod IDs are given where the exact name wasn't
> recorded inline.

## Wikis & community references

- [Starfield Wiki (starfieldwiki.net)](https://starfieldwiki.net/wiki/Starfield_Mod:Archive2) — modding wiki; cited here for the Archive2 / BA2 format
- [Starfield Wiki (Fextralife)](https://starfield.wiki.fextralife.com/Character_Creation) — general Starfield wiki (character creation)
- [modding.wiki — Starfield tutorials](https://modding.wiki/en/starfield/developers/tutorials/ESMtoESP) — e.g. converting ESM → ESP
- [StarfieldDB](https://www.starfielddb.com/character-creation/) — Starfield database (character creation)
- [PCGamesN — Starfield character creation](https://www.pcgamesn.com/starfield/character-creation) — general character-creation guide

## NIF format, meshes & core tools

- [NifSkope (niftools)](https://github.com/niftools/nifskope) — the classic NIF viewer/editor
- [NifTools nif.xml](https://github.com/niftools/nifxml) — the NIF format definition ([nif.xml spec](https://github.com/niftools/nifxml/tree/develop/nif.xml))
- [nifly (ousnius)](https://github.com/ousnius/nifly) — C++ NIF library (the engine under Outfit Studio and PyNifly)
- [Outfit Studio / BodySlide (ousnius)](https://github.com/ousnius/BodySlide-and-Outfit-Studio) — body/outfit editing

## PyNifly (this library's companion addon)

- [PyNifly (GitHub)](https://github.com/BadDogSkyrim/PyNifly) — Blender NIF import/export addon
- [PyNifly Wiki](https://github.com/BadDogSkyrim/PyNifly/wiki) — usage & format docs (incl. [Skyrim Partitions](https://github.com/BadDogSkyrim/PyNifly/wiki/Skyrim-Partitions))
- [Releases](https://github.com/BadDogSkyrim/PyNifly/releases) · [Issues](https://github.com/BadDogSkyrim/PyNifly/issues)
- [Blender](https://www.blender.org/download/) — the host application

## Plugins, load order & xEdit

- [xEdit / TES5Edit](https://github.com/TES5Edit/TES5Edit) — the record editor (SF1Edit for Starfield)
- [LOOT — Changing Plugin Types in Starfield](https://loot.github.io/docs/help/Changing-Plugin-Types-In-Starfield.html)
- [Ortham blog — Load order in Starfield](https://blog.ortham.net/posts/2024-06-28-load-order-in-starfield/)
- [`ba2` Rust crate docs](https://docs.rs/ba2/latest/ba2/fo4/index.html) — FO4/Starfield BA2 structures
- [Starfield plugin-header gist (fre-sch)](https://gist.github.com/fre-sch/ea74bc201be01c8e656991baacfc9702)

## Animation & Havok

- [Nexus forums — Havok Content Tools fidelity](https://forums.nexusmods.com/topic/13478686-how-to-avoid-visible-animation-fidelity-loss-when-exporting-with-havok-content-tools/)

## Starfield — meshes & materials tooling

- [NifSkope (fo76utils fork)](https://github.com/fo76utils/nifskope) — the de-facto Starfield NifSkope. Source refs cited here: [CHANGELOG](https://github.com/fo76utils/nifskope/blob/develop/CHANGELOG.md) · [material.hpp](https://github.com/fo76utils/nifskope/blob/develop/lib/libfo76utils/src/material.hpp) · [meshlet.cpp](https://github.com/fo76utils/nifskope/blob/develop/lib/meshlet.cpp) · [MeshFile.cpp](https://github.com/fo76utils/nifskope/blob/develop/src/io/MeshFile.cpp)
- [fo76utils / ce2utils](https://github.com/fo76utils/ce2utils) — material dump / `mat_names.txt`
- [Gibbed.Starfield](https://github.com/gibbed/Gibbed.Starfield) — `.cdb` material-database tooling
- [Starfield Material Exporter (SFME)](https://github.com/maximusmaxy/SFME) (maximusmaxy) · [Nexus 7830](https://www.nexusmods.com/starfield/mods/7830)
- [StarfieldMeshConverter (SesamePaste233)](https://github.com/SesamePaste233/StarfieldMeshConverter) — the Starfield Geometry Bridge engine
- [Starfield Geometry Bridge docs](https://starfieldgeometrybridge.github.io/) — format tips: [material](https://starfieldgeometrybridge.github.io/docs/tips/material/) · [mesh](https://starfieldgeometrybridge.github.io/docs/tips/mesh/) · [nif](https://starfieldgeometrybridge.github.io/docs/tips/nif/)
- [Step Mods — Starfield Texture Formats](https://stepmodifications.org/forum/topic/19037-starfield-texture-formats/) — BC7/BC5/BC4 conventions
- [Allmods — Organization of Starfield's meshes & assets](https://allmods.net/starfield-mods/starfield-miscellaneous/organization-of-starfields-meshes-and-related-assets/)
- [HTG Regenesys Character](https://github.com/HelixTechGroup/HTG-Regenesys-Character) — a real shipped `.mat` example
- [Material Editor Lite (Nexus 14659)](https://www.nexusmods.com/starfield/mods/14659)

## Starfield — chargen, race & character

Guides & tutorials:

- Nexus articles — [268](https://www.nexusmods.com/starfield/articles/268) · [411 — creating a custom material](https://www.nexusmods.com/starfield/articles/411) · [431 — custom race](https://www.nexusmods.com/starfield/articles/431) · [481 — chargen / RTFP](https://www.nexusmods.com/starfield/articles/481)
- Nexus forums — [Generating FaceGen data](https://forums.nexusmods.com/topic/13526765-generating-facegen-data/) · [Starfield's `.cdb` material database](https://forums.nexusmods.com/topic/13361451-starfields-cdb-material-database/)
- [The-Animonculory / Modding-Resources](https://github.com/The-Animonculory/Modding-Resources)
- [Allmods — SFF body replacer](https://allmods.net/starfield-mods/starfield-characters/sff-body-replacer-v1-0/)

Mods & resources (Nexus):

- [4360 — Starfield Geometry Bridge](https://www.nexusmods.com/starfield/mods/4360)
- [10748 — NifSkope (fo76utils fork)](https://www.nexusmods.com/starfield/mods/10748)
- [16905 — SF Extended Skeleton](https://www.nexusmods.com/starfield/mods/16905)
- [17160 — Felid (playable cat race)](https://www.nexusmods.com/starfield/mods/17160)
- [6850 — CharGenMenu](https://www.nexusmods.com/starfield/mods/6850)
- [7360 — NAF (Native Animation Framework)](https://www.nexusmods.com/starfield/mods/7360)
- [9234 — `.nif` Mesh Path Migration Tool](https://www.nexusmods.com/starfield/mods/9234)
- [1192 — BA2 Upgrader](https://www.nexusmods.com/starfield/mods/1192)
- [14468 — Bethesda Archive Manager](https://www.nexusmods.com/starfield/mods/14468)
- [7783 — Starfield chargen resource](https://www.nexusmods.com/starfield/mods/7783)

_Draft 2026-07-11 — not yet reviewed_
