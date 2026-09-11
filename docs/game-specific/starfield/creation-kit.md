# Starfield: The Creation Kit & FaceGen

Practical, hard-won notes on getting the Starfield Creation Kit (CK) to **bake a custom NPC/race
head** — the fragile last mile after the mesh, material, and morphs are correct. Most of this was
verified the painful way (custom "Lykaios" anthro head via PyNifly), and it fills in the gaps the
[chargen page](chargen.md) flagged as unverified — most importantly **where FaceGen actually writes
its output**.

If your head renders in NifSkope and in the CK's head-part preview but is **black, invisible, or
human-textured in the actor preview / in-game**, the cause is almost always on this page, not in the
asset.

---

## 1. CKPE is effectively required (and its version matters)

**[Creation Kit Platform Extended (CKPE)](https://www.nexusmods.com/starfield/mods/11802)** is not
just a QoL patch for FaceGen work — without it (or with a mismatched build) the CK's FaceGen path
tends to **silently do nothing or crash**. Observed failure signatures:

- **Silent no-op:** Ctrl+F4 shows the confirm dialog → "done" dialog, with **no per-NPC "processing"
  status line and no output files**. The routine ran over zero NPCs. Reproduces on *vanilla* NPCs too
  when the CK/CKPE FaceGen path is broken — so "vanilla also bakes nothing" is a strong signal the
  problem is the CK environment, not your mod.
- **Crash:** the character-dialog "generate" button access-violates. See §6.

**Version sensitivity is real:** a FaceGen bake that worked on one CKPE build stopped working after an
update (and vice-versa). If FaceGen breaks after a CKPE change, **roll CKPE back** and retest before
suspecting your data. Turn on CKPE's log (`ckpe.log` / `CreationKitPlatformExtended.log`) — but note
the CK holds it open with an exclusive lock while running, so read it **after** closing the CK.

### How CKPE loads (and how to run the CK without it)

CKPE injects via a **`winhttp.dll` DLL-search-order hijack**: a proxy `winhttp.dll` dropped next to
`CreationKit.exe` is loaded before the real `System32` copy (winhttp is imported by the CK and is not
a protected "KnownDLL"), and its `DllMain` boots CKPE. In current builds this proxy **also fronts the
Steam API** (the CK is a Steam-DRM'd app), so its export table is `SteamAPI_*` rather than WinHTTP
forwarders. Files: `winhttp.dll`, `ckpe_loader.exe`, `CKPE*.dll`, `CreationKitPlatformExtended.toml`.

To run a **vanilla CK for A/B testing**, close the CK and rename `winhttp.dll` → `winhttp.dll.bak`;
launch `CreationKit.exe` directly. The other `CKPE.*` files go inert without the proxy. Rename back to
restore. (`CKPE.Installer.exe` also has a proper install/uninstall.)

---

## 2. FaceGen output — what it bakes and **where** (verified)

The [chargen page](chargen.md#8-facegen-baking-npc-faces) noted the literal Starfield FaceGen output
path was unconfirmed ("same idea as FO4, path TBD"). **Confirmed:** the per-race **base head skin** is
baked to

```
Data\Textures\actors\Character\FaceCustomization\<Plugin>.esp\BaseHead<RaceEDID><Sex>_<map>.dds
```

e.g. `…\FaceCustomization\FSF.esp\BaseHeadFSFLykaiosRaceMale_Color.dds`. The map suffixes and formats
seen (1024×1024, DDS):

| File | Map | Format |
|---|---|---|
| `BaseHead<Race><Sex>_Color`  | albedo (skin tone + tint layers) | `R8G8B8A8_UNORM_SRGB`, 5 mips |
| `BaseHead<Race><Sex>_Normal` | normal | `BC5_SNORM`, 5 mips |
| `BaseHead<Race><Sex>_ao`     | ambient occlusion | `R8` uncompressed, 5 mips |
| `BaseHead<Race><Sex>_rough`  | roughness | `R8` uncompressed, 5 mips |

Note this is **not** FO4's `meshes\actors\...\facegendata\facegeom\<plugin>\<FormID>.nif` layout — the
Starfield base head is a **texture set under `FaceCustomization`**.

### Two output filenames: per-race vs per-NPC

The same four maps are written under **either** of two names in that folder:

| Filename | When |
|---|---|
| `BaseHead<RaceEDID><Sex>_<map>.dds` | the NPC has **no** tint layers (`EDCT` = 0) |
| `<NPC local FormID:08X>_<map>.dds`  | the NPC has **≥ 1** tint layer |

`BaseHead%s%s` is a literal format string in both `CreationKit.exe` and `Starfield.exe` (`%s%s` =
race EDID + `Male`/`Female`). Adding a single tint layer — vanilla NPCs use `TNAM='Dermaesthetic'` —
is what promotes the bake to a per-NPC file. If you expect `<FormID>_Color.dds` and get
`BaseHead…`, the NPC has no tints.

### What the bake actually composites (verified by pixel comparison)

The bake **does not read the head part's material.** Measured against a vanilla male head, with the
loose `male_default.mat` deliberately pointed at unrelated textures:

| Baked map | Compared to | Result |
|---|---|---|
| `_Color` | `male_default_sk0_color.dds` (the skin-tone source) | **identical** across the face; only the hair/scalp overlay and the NPC's tint layers are added |
| `_rough` | `male_default_rough.dds` | **byte-identical**, 1 048 576 bytes |
| `_ao`    | `male_default_ao.dds`    | **byte-identical**, 1 048 576 bytes |
| `_Normal`| `male_default_normal.dds`| identical within BC5 quantisation (mean \|Δ\| 0.58, median 0, p99 4, max 15 on a −127…127 scale) |

So all four channels are straight copies of the **base-layer source maps**, with tint layers
composited into colour only. The material's own texture paths are never consulted, and the
material's **upper layers are not baked in** — a vanilla head material carries five detail layers
(pore, stubble, lips, cheek, skin detail) whose normal/AO contributions are absent from the bake.

Those four maps correspond exactly to slots 0/1/3/5 of the material's base texture set. Slot 8
(transmissive) and the flat `TextureReplacement` entries at slots 2/4 are not baked.

!!! note "Inference, not measured"
    The natural reading is that the bake **replaces the base layer's four maps** and the material's
    remaining layers still composite at render time — otherwise vanilla faces would show none of
    their pore/stubble/lip/cheek detail, and the bake demonstrably does not carry it. This has not
    been directly confirmed. A clean test: enable `LayeredEmissivityComponent` on the material's
    root node; nothing in the FaceGen path touches emissive.

!!! warning "The base-head filename is keyed to the race EDID — rename the race and it orphans"
    `BaseHead<RaceEDID><Sex>_*` is located by **naming convention from the race's Editor ID**, with no
    reference stored in the plugin. If you **rename the race EDID**, the previously-baked textures keep
    the *old* name and are silently ignored, while the game now looks for the new name and finds
    nothing → **black / invisible / stale-human-textured head**. Delete the orphaned
    `BaseHead<OldRace>*` files and re-bake. (This is the same race-EDID naming convention as the
    FacialBoneRegions CSV — see §8.)

---

## 3. Where the bake gets its source textures — `FCTP` and the filename convention

The FaceGen bake sources its four base maps **by filename convention from a per-race directory**.
Neither the head part's material nor the plugin stores these paths.

### The directory

The race's **`FCTP`** ("Face Custom Textures Base Path") field, in the *male* Chargen-and-Skintones
block, supplies the directory, relative to `Data\Textures\`:

```
FCTP = actors\Felid\faces\chargen          (FelidRace)
FCTP = <absent>                            (vanilla HumanRace)
```

When `FCTP` is absent the engine falls back to the ini setting **`[Facegen] sSkinTexturePath`**,
whose built-in default is the literal `Actors\Human\Faces\Chargen` — which is exactly where the
vanilla human face textures live. **It does not fall back to the material's texture paths.**

### The filenames

Hard-coded format strings, present in both `CreationKit.exe` and `Starfield.exe`:

| Format string | Resolves to |
|---|---|
| `%s\%s_sk%u_color.dds` | `<FCTP>\<phenotype>_sk<N>_color.dds` |
| `%s\%s_normal.dds`     | `<FCTP>\<phenotype>_normal.dds` |
| `%s\%s_rough.dds`      | `<FCTP>\<phenotype>_rough.dds` |
| `%s\%s_ao.dds`         | `<FCTP>\<phenotype>_ao.dds` |
| `%s\FCT_%s_mask.dds`   | `<FCTP>\FCT_<region>_mask.dds` |
| `%s\FCT_null_mask.dds` | `<FCTP>\FCT_null_mask.dds` |

- **`<phenotype>`** is a chargen phenotype name. `male_default` and `female_default` are hard-coded
  literals in both exes and act as the fallback. Vanilla ships **22** phenotypes (11 per sex: the
  nine ethnicity×age combinations, plus `eu_md2`, plus `default`), and the names are exactly the
  child keys of `ComplexGroup_FaceSkinTones` (see [chargen §4](chargen.md#4-tints-complexions-overlays-the-avm-system-avmdavms)).
- **`<region>`** is a face region — the race's `MPGN` morph-group names:
  `Cheeks, Chin, Ears, Eyes, Forehead, Jaw, Mouth, Neck, Nose`.

The vanilla `Actors\Human\Faces\Chargen` folder holds exactly **274** files, which is this
convention exhaustively enumerated: 22 phenotypes × (9 sk-indexed colours + `_ao` + `_normal` +
`_rough`) = 264, plus the 9 region masks and `FCT_null_mask.dds`.

!!! warning "Colour is `_sk<N>_color`, never a plain `_color`"
    There is no `<phenotype>_color.dds` anywhere in vanilla. The albedo filename always carries the
    skin-tone index. A file named `male_default_color.dds` will be silently ignored.

### Albedo has a second route; the other three do not

The **colour** channel can also be supplied per skin-tone index through the `FSTT` → `AVMD` chain
(race `FSTT` → kind-2 ComplexGroup → per-phenotype SimpleGroup → nine `VNAM` texture paths, indexed
by the NPC's `STON`). Where that lookup resolves, its path wins over the computed
`_sk<N>_color.dds` name — a custom race can point it anywhere.

**`_normal`, `_rough` and `_ao` have no such route.** No `AVMD` record anywhere in `Starfield.esm`
supplies a *base* face normal/rough/AO; the 176 `_ao`-suffixed AVMD entries are all scar and
post-blend detail overlays. Those three maps come from the `FCTP` convention and nowhere else.

!!! tip "Minimum viable FCTP folder for a custom race"
    Set `FCTP` on the race, then place under `Data\Textures\<FCTP>\`:

    - `male_default_ao.dds`, `male_default_normal.dds`, `male_default_rough.dds`
    - `male_default_sk0_color.dds` (…`_sk8_` if you want a tone ramp), *or* leave colour to `FSTT`
    - the ten `FCT_*_mask.dds` region masks (copy the human or Felid set to start)
    - the `female_default_*` equivalents if the race has a female

    Setting `FCTP` is strongly preferable to overriding the vanilla
    `Actors\Human\Faces\Chargen` files, which recolours every human in the game.

---

## 4. A custom race needs a **body** before the head resolves

The single fix that made a custom-race head finally render with its **full texture** was **giving the
race a working body skin.** Symptom while the body was unresolved (from `EditorWarnings.txt`):

```
MODELS: Trying to apply skin [Skin_Naked] to reference [<NPC>] with empty model or
        with no model supporting reference race [<CustomRace>]
```

A custom race clones `HumanRace`, but its `WNAM` **Skin** `ARMO` and that armor's **addons** must have
**valid-races** covering your new race, or the actor has no body — and with no body skin resolved, the
head's skin/tint compositing fails and the head renders black/untextured even though the head *mesh*
is fine. **Add a body (a skin `ARMO` + `ARMA` addon whose race list includes your race) first**, then
the head bakes and shows its texture.

---

## 5. Chargen morphs must match the `.mesh`'s render-vertex count

FaceGen builds the head by applying the chargen morph to the head geometry. Starfield `.mesh` files
store **render (post-split) vertices** — verts are duplicated at UV/normal seams — and the
`chargen` `morph.dat` must be **1:1 with that post-split vertex set**. If it isn't:

```
MODELS: ApplyChargenMorph: Vertex count mismatch between geometry and morph data for <head> :
        Geometry Vertex Count[5558] ... Morph Data Vertex Count[5405]
```

The morph fails to apply, the head geometry doesn't assemble, and the FaceGen bake **crashes** (null
head geometry — see §6). A morph authored against the *pre-split* mesh (e.g. the raw Blender vertex
count) will mismatch any head with UV seams. **Any exporter must emit the morph at the same split
vertex count/order the `.mesh` uses** — duplicating each vertex's delta wherever the mesh splits it.
(The vanilla morph.dat vertex count equals the vanilla `.mesh` render-vertex count for the same head.)

---

## 6. The FaceGen crash (null head geometry)

The character-dialog "generate" button (and the head-build path generally) crashes with an
**`EXCEPTION_ACCESS_VIOLATION` reading address 0** while walking an NPC's head geometry. Decoding a CKPE
crash dump: the faulting frame dereferences a null where a **`BSGeometry`** should be, with `TESNPC*`,
`BSFadeNode*`, and `NiTObjectArray<NiPointer<NiAVObject>>*` on the stack — i.e. the CK is assembling
the head's scene graph and one head-part geometry is null.

Crucially, **the crash persists with CKPE fully disabled** (§1), so it is the *engine's* head-build,
not a CKPE bug. Root causes that null the head geometry: the **morph mismatch** (§5), a **missing body
skin** (§4), or a **missing/failed head part**. Fix those and the crash clears.

CKPE writes crash dumps to `…\Starfield\Logs\CKPE\Crashes\CreationKit.exe_<timestamp>.zip`
(containing `CreationKitPlatformExtendedCrash.log` with the decoded stack + a `.dmp`).

---

## 7. Diagnosing: `EditorWarnings.txt` is the key file

On plugin load / FaceGen the CK writes `…\Starfield\EditorWarnings.txt`. The `<CURRENT>` lines are your
active plugin. The most useful entries seen, and what they mean:

| Warning | Meaning / fix |
|---|---|
| `FACEGEN: … RACE '<Race>' Missing FacialBoneRegions file '…\<Race>FacialBoneRegionsMapping.csv'` | See §8. |
| `MODELS: ApplyChargenMorph: Vertex count mismatch …` | Morph ≠ `.mesh` render-vert count (§5). |
| `MODELS: Trying to apply skin [Skin_Naked] … no model supporting reference race […]` | No body for the race (§4). |
| `FACEGEN: TeethCustomizationNode failed for actor(…) because its scene graph does not have a HeadPartTeeth` | The race/NPC has no Teeth head part — add one (Type 9). |
| `SYSTEM: Can't load object res:… referenced by …\Foo.mat (#N)` | A loose `.mat`'s internal object references aren't resolving — usually non-fatal if the material still renders, but a sign of a malformed material graph (see [materials](materials.md)). |

---

## 8. The FacialBoneRegions files (schema verified)

A race needs **two** files, both hooked **purely by naming convention from the race EDID** — the
plugin stores **no** reference to either (verified: a custom race's plugin contains no path string for
them). Supplying the files under the right names is the entire hookup; there is no record edit.
(Same race-EDID gotcha as the base-head textures, §2.)

| File | Contents |
|---|---|
| `<RaceEDID>FacialBoneRegionsMapping.csv` | bone → face-region influence matrix |
| `<RaceEDID>FacialBoneRegions<Sex>.txt` | JSON: the actual bone-morph definitions |

### Where they live

Vanilla `HumanRace` ships them in `meshes\actors\human\characterassets\` (the male `.txt` and the
`.csv`), with the female `.txt` one level down in `…\characterassets\female\`. `HumanCrowdRace` keeps
its own set under `meshes\actors\human_crowd\characterassets\`.

A shipped custom race puts copies in **both** its own `meshes\actors\<race>\characterassets\` **and**
`meshes\actors\human\characterassets\` — the same two files, same race-EDID names, in both folders.
Since the lookup is name-based rather than record-based, shipping both locations is the low-cost way
to satisfy whichever path the CK and the runtime each use.

### `…Mapping.csv` schema

First column is unnamed and holds the bone name; the remaining nine columns are the face regions.
Values are 0–100 influence.

```
                        Cheeks Chin Ears Eyes Forehead Jaw Mouth Neck Nose
faceBone_L_CheekBone        80    0    0   20        0   0     0    0    0
faceBone_C_NoseRidge         0    0    0   30        0   0     0    0   70
faceBone_L_OutterJaw         0   10   20    0        0  70     0    0    0
faceBone_C_HeadBack          0    0    0    0        0   0     0    0    0
```

Vanilla human has **48 bone rows**. A bone may split across regions, and a bone may be all-zero
(present in the rig but not driven by any region slider). Rows do **not** have to sum to 100.

### `…FacialBoneRegions<Sex>.txt` schema

UTF-8 JSON with a BOM. Top level is `{"Constraints": null, "Regions": [...]}`.

```json
{ "ID": 26, "Name": "Ears", "SculptRegion": true,
  "SlidersA": [
    { "ID": 27, "Name": "down - up", "ZeroToOne": false,
      "BonesA": [
        { "Bone": "faceBone_L_EarMaster",
          "Maxima": { "Position": {"x":0,"y":0.683,"z":0},
                      "Rotation": {"x":0,"y":0,"z":0},
                      "Scale":    {"x":0,"y":0,"z":0} },
          "Minima": { "Position": {...}, "Rotation": {...}, "Scale": {...} } } ] } ] }
```

Each slider interpolates every listed bone between its `Minima` and `Maxima` transform.
`ZeroToOne` distinguishes a one-directional 0→1 blend from a bipolar min↔max slider.

Vanilla human male has **20 regions**, split by the `SculptRegion` flag:

- **9 phenotype regions** (`SculptRegion: false`) named `male_af_md1`, `male_as_ol1`, … — the same
  strings as the race's `FMRU` phenotype keys. Each drives all 48 bones.
- **11 sculpt regions** (`SculptRegion: true`) — the creator's face sliders:

| Region | Bone refs | Sliders |
|---|---|---|
| Head Shapes | 192 | Square, Narrow, Wide, Round *(all `ZeroToOne`)* |
| Eyes | 37 | down–up, narrow–wide, scale down–up, back–forward |
| Nose | 32 | down–up, back–forward, narrow–wide, tip down–up, short–long, nostrils up–down, nostrils in–out, ridge narrow–wide, ridge in–out |
| Jaw | 18 | back–forward, narrow–wide, down–up |
| Cheeks | 17 | narrow–wide, scale down–up, down–up |
| Neck | 16 | Wattle In–Out, narrow–wide |
| Mouth | 15 | down–up, Left–Right, scale down–up, underbite–overbite |
| Forehead | 14 | narrow–wide, back–forward |
| Ears | 12 | down–up, back–forward, narrow–wide |
| Eyebrows | 12 | down–up, back–forward, narrow–wide |
| Chin | 9 | down–up, back–forward, narrow–wide |

For a HumanRace clone on the human skeleton, a renamed copy of the vanilla pair is the correct
starting point — both files key on bone names, which are unchanged. The vanilla files **have real
content**; an extract that looks empty means a faulty BA2 extractor, not an empty source. Don't ship
an empty one.

**Still unverified:** whether the files are strictly *required* or merely advisory. The same
"missing" warning fires for vanilla `ChildRace`, so the CK warns even when a bake can proceed.

> **Note — "FCT" the CK button ≠ these files.** The character-dialog **"Bake FCT"** button bakes the
> **Face Customization Texture** (the per-NPC baked face texture set); it is unrelated to
> FacialBoneRegions. See §2 for the FaceGen texture output.

A region's `ID` is what the race record's `FMRI`/`FMSR` entries and an NPC's Face Morphs / Face
Dial Positions arrays point at — the plugin side is an index into these files. See the chargen
page, §3, for how these bone-driven regions relate to the vertex-morph (`morph.dat`) system,
which of the three NPC arrays drives which, and which one to reach for.

---

## Sources

- Direct investigation of a custom Starfield race/head via PyNifly (2026-07): CK behavior,
  `EditorWarnings.txt`, CKPE crash-dump decode, on-disk FaceGen output.
- [Creation Kit Platform Extended (CKPE)](https://www.nexusmods.com/starfield/mods/11802).
- Nexus — "Notes and pitfalls on creating a playable race" (article 431).
- Cross-refs: [chargen page](chargen.md) (race/HDPT/MRPH records, §8 FaceGen concept),
  [materials](materials.md) (loose `.mat` structure), [tools](tools.md) (CK, CKPE, BSArch).

_Draft 2026-07-24 — not yet reviewed_
