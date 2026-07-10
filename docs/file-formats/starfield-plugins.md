# Starfield Plugins (ESM) & BA2 Archives

Starfield is still a TES4-family engine: a plugin is a `TES4` header record followed by `GRUP` groups of records, each record a stream of `[SIG:4][SIZE:2][data]` subrecords. The record header is the same 24 bytes as Skyrim/Fallout 4, groups behave the same, and the `XXXX` large-field trick still applies. What is genuinely new is a **component system** layered on top of records, a **new master-tier model** (full / medium / small), and a **new BA2 version** (v2/v3). Geometry also moved out of the `.nif` into external `.mesh` files.

This page assumes familiarity with the generic [plugin](plugins.md) and [archive](archives.md) pages and only documents Starfield deltas. Record-field breakdowns are taken from the xEdit / SF1Edit definition file `wbDefinitionsSF1.pas` (the authoritative community source), cross-checked against `Starfield.esm`. Header layouts are from direct byte dumps of the shipped archives.

- **Plugin header version (HEDR):** `0.96` (`[FO4]` was `0.95`; `[SSE]` `0.94`/Form 44).
- **xEdit game mode:** SF1Edit (`xSFEdit.exe`, or `xEdit.exe -sf1`), build 4.1.4+ for read, 4.1.5+ for most editing.

---

## 1. Plugin format evolution

### 1.1 The component system (Base Form Components)

`[FO4]` records were a flat, fixed sequence of subrecords. Starfield keeps that for most fields but inserts a **component block** near the top of most records — an ordered, self-describing list of "components" that attach reusable capabilities (a name, a model, a container, keywords, scripts, destruction data, etc.) to a form. This is the same idea Bethesda used internally in Fallout 76; in Starfield it is exposed in the plugin format.

**On-disk shape of the component block** (xEdit calls it *Base Form Components*):

```
<component count / marker>          ← xEdit surfaces this as the "____" known subrecord (ksrBaseFormComponents)
  BFCB  <string>   Component Type   e.g. "TESFullName_Component"
  ... component-specific subrecords ...
  BFCE  (empty)    End Marker
  BFCB  <string>   Component Type   e.g. "TESModel_Component"
  ... component-specific subrecords ...
  BFCE
  ...
```

- **`BFCB`** — null-terminated ASCII naming the component class (e.g. `BGSKeywordForm_Component`, `TESContainer_Component`, `BGSDestructibleObject_Component`, `BGSSkinForm_Component`). xEdit resolves the following data with a *decider* keyed on this string.
- **`BFCE`** — empty end-of-component marker.
- The component's payload uses ordinary subrecord signatures (`FULL`, `MODL`, `DEST`, `KWDA`, `PRPS`, …) — the *same* signatures used inline in older games, just relocated inside a component.

Over 70 component classes exist. The ones a body/armor/race mod touches:

| Component class (`BFCB`) | Carries | Key subrecords |
|---|---|---|
| `TESFullName_Component` | Display name | `FULL` |
| `TESModel_Component` | Model / mesh path | `MODL`, `MOLM`, `FLLD`, `MODC`, `XFLG` |
| `BGSKeywordForm_Component` | Keywords | `KSIZ`/`KWDA` |
| `TESContainer_Component` | Inventory contents | container item structs |
| `BGSDestructibleObject_Component` | Destruction data | `DEST`/`DSTD`… |
| `BGSSkinForm_Component` | Skin (armor worn as body) | skin form link |
| `BGSPropertySheet_Component` | Actor-value properties | `PRPS` |
| `BGSPapyrusScripts_Component` | Attached scripts | VMAD-style data |

**Practical consequence for modders:** in xEdit a Starfield ARMO/RACE/TXST shows a `Base Form Components` array with expandable `Component` nodes, *plus* the classic inline fields lower down. Copy-as-override brings the whole component block along; adding a capability (e.g. giving a form a name) means adding the right component, not just a subrecord. **Unverified:** xEdit still cannot fully edit component forms whose payload includes opaque `REFL` reflection blobs (`GBFM` generic base forms in particular) — treat those as read-only.

`GBFM` ("Generic Base Form") is the new pure-component record type — a form that is *nothing but* a component list. Ship parts use it heavily; a race mod generally does not create `GBFM` records but will encounter them.

### 1.2 ESM / ESP / master tiers, flags & FormID ranges

Starfield replaces the single ESL concept with a **three-tier master model**. Tier is set by TES4-header flags, not by extension; almost everything ships as `.esm`.

| Tier | TES4 flag | FormID form | Index range | Records each | Max in load order |
|---|---|---|---|---|---|
| **Full master** | `0x00000001` (ESM) | `xx000001`–`xxFFFFFF` | `xx` = `00`–`FC` | ~16.7 M | 253 |
| **Medium master** | `0x00000400` (bit 10, "Medium") | `FDxx0001`–`FDxxFFFF` | `xx` = `00`–`FF` | 65 535 | 256 |
| **Small master** (ESL / "light") | `0x00000100` (bit 8, "Small") | `FExxx001`–`FExxxFFF` | `xxx` = 12-bit | 4 095 | 4 096 |

(`[FO4]`/`[SSE]` had only Full + Light; the **Medium** tier is new to Starfield, added in game update 1.11. It fills the gap between a 4 K-record ESL and a full load-order slot.)

**Full Starfield TES4 header flag set** (from `wbDefinitionsSF1.pas`):

| Bit / value | Name | Meaning |
|---|---|---|
| `0x001` | Master | Full master (loads first) |
| `0x010` | Optimized | CK-optimized |
| `0x080` | Localized | strings externalized to `.STRINGS` (default on) |
| `0x100` | **Small** | small/light master (ESL-equivalent, `FE` FormIDs) |
| `0x200` | Update | "update" plugin (overrides only; no new forms) |
| `0x400` | **Medium** | medium master (`FD` FormIDs) |
| `0x800` | **Blueprint** | blueprint master |

Notes:
- **A plugin cannot be both Small and Medium.** Convert with LOOT / xEdit "compact FormIDs" only when record counts fit the tier.
- Local FormIDs for new records in a full master conventionally start at `0x000800` (CK reserves the low range), same as prior games.
- `.esm` vs `.esp` still only affects **load-order family** (`.esm` before `.esp`); the tier flags drive FormID resolution. In practice Starfield mods ship `.esm` (often small- or medium-flagged). An `.esp` with no flag is a plain full-load-order plugin.
- **Blueprint master** (`0x800`) is a Starfield-specific master used for ship blueprints; not relevant to a race mod.

**Worked FormID examples:**
- `0x0000347D` — `HumanRace` in `Starfield.esm` (master index `00`).
- `0xFExxx7A2` — a record in a small (light) master; middle 12 bits pick the light plugin.
- `0xFD030044` — record `0x0044` in the medium master at medium-index `03`.

---

## 2. Records a body / armor / race mod touches

Signatures and field order below are from `wbDefinitionsSF1.pas`; "component block" = the `Base Form Components` array described in §1.1. Field breakdowns list the load-bearing subrecords, not every optional one.

### 2.1 How a mesh path is stored in a record — `TESModel_Component` / `MODL`

Every visible form references its art through a **Model** structure, either inline (`wbGenericModel`) or as a `TESModel_Component`. The structure:

| Sub | Field | Type | Notes |
|---|---|---|---|
| `MODL` | Model FileName | zstring | Path to a **`.nif`**, e.g. `meshes\actors\human\characterassets\...nif`. Still `.nif`, still `meshes\`. |
| `MOLM` | Material Swaps | array of FormID → `LMSW` | Layered-material-swap forms applied to the nif's materials (index-matched, sortable). |
| `FLLD` | Light Layer | uint32 flags | Lighting layer bitfield (required). |
| `MODC` | Color Remapping Index | float | Palette remap. |
| `XFLG` | Flags | uint8 | Model flags. |

Older `MODT`/`MODS`/`MODF` still parse but **do not occur in `Starfield.esm`** — Starfield does material binding through `MOLM`→`LMSW` and the nif's own material references instead of the old alternate-texture arrays.

**The mesh path is only half the story.** The `.nif` named by `MODL` is a lightweight **container**: transforms, bone list, physics, and *asset references*. Actual geometry lives in external **`.mesh`** files (see §3.4 and §4). So a record → `MODL` (`.nif`) → `BSGeometry` mesh-path hash → `Data\geometries\<hex1>\<hex2>.mesh`. A record never names a `.mesh` directly.

### 2.2 `RACE` — Race

The central record for this project. It is large; the mod-relevant fields:

| Sub | Field | Type | Notes |
|---|---|---|---|
| `EDID` | Editor ID | zstring | e.g. `HumanRace` |
| *component block* | — | — | `TESFullName_Component`, keywords, property sheet, etc. |
| `FULL` / `DESC` | Name / Description | lstring | |
| `WNAM` | **Skin** | FormID → `ARMO` | The "naked body" armor worn when nothing is equipped. **Central to a custom body.** |
| `GNAM` | Body Part Data | FormID → `BPTD` | Dismemberment / hit regions. |
| `DAT2` | Data struct | struct | Heights (male/female), default weights (thin/muscular/fat), biped-object slot indices (Head/Hair/Body/Beard/Shield/Pipboy), movement, bleedout, etc. |
| Skeleton Data | `MNAM`/`FNAM` + `ANAM`,`NAM5`,`NAM6`,`DNAM` | strings | Male & female **skeletal model**, skeleton rig, animation root, animations (behavior graph). |
| `VTCK` | Voices | FormID[2] → `VTYP` | Male/female voice types. |
| `PNAM`/`UNAM` | FaceGen clamps | float | Main / face morph clamp. |
| Chargen & Skintones | `MNAM`/`FNAM` blocks | mixed | Race presets (`RPRM`/`RPRF` → `NPC_`), **Morph Groups**, **Face Morph Phenotypes**, body/hand/face skin-tone paths (`BSTT`/`HSTT`/`FSTT`), face custom-texture base path (`FCTP`). |
| `NAM8` | **Morph Race** | FormID → `RACE` | Race whose facegen morphs this race inherits. |
| `RNAM` | **Armor Race** | FormID → `RACE` | Race used to resolve wearable armor models — **set to `HumanRace` so your race can wear all human armor.** |
| `SRAC` | **Subgraph Template Race** | FormID → `RACE` | Animation subgraph template — **set to `HumanRace` to avoid broken animations.** |
| Head Parts & Bone Modifiers | `MNAM`/`FNAM` → `INDX`+`HEAD` (→`HDPT`), `BNAM`→`BMOD` | arrays | Per-gender list of head parts and bone modifiers. |
| Equip Slots | `QNAM`(→`EQUP`)+`ZNAM` node | array | Equip slot → skeleton node mapping (ordered, do not sort). |
| Biped Object Names | `NAME` ×64 | strings | Names of the 64 biped/armor slots. |

### 2.3 `ARMO` — Armor (and the "skin" body)

Both real armor and the race's naked body are `ARMO` records. Mod-relevant fields:

| Sub | Field | Type | Notes |
|---|---|---|---|
| Record flags | `0x04` Non-Playable, `0x40` Shield | flags | |
| *component block* | — | — | `TESFullName_Component`, keywords, destructible, etc. |
| `MOD2`/`MOD4` | Male/Female **World Model** | Model struct | Dropped/inventory model (+ `MOLM` material swaps). |
| `BO64` | Biped Object slots | uint64 | Which of the 64 biped slots this armor occupies. |
| `RNAM` | **Race** | FormID → `RACE` | Race the armor is built for. |
| `Models` | array of `INDX`(uint16)+`MODL`(→`ARMA`) | array | **The addon list** — maps an addon index to an `ARMA` record. This is how an ARMO delegates its actual worn mesh to per-race addons. |
| `DATA` | Value / Weight / Health | struct | |
| `FNAM` | Armor Rating / Base Addon Index / Stagger | struct | |
| `ETYP`/`ETYP` | Equip type | FormID → `EQUP` | |

The **race skin** is an ARMO (pointed to by `RACE.WNAM`) whose `Models` list references body/hands `ARMA` addons. A custom body means: a skin ARMO → body `ARMA` + hands `ARMA` → each pointing at your `.nif`s and skin `TXST`. Specifics confirmed by the "creating a playable race" guide:

- The skin ARMO **must have the `Non-Playable` record-header flag** (or you can accidentally equip/"skin" the player).
- **Split into two addons**: a **body** ARMA on biped slot **3 (BODY)** and a **hands** ARMA on slot **6 (Gloves)** — most apparel only substitutes the body addon, so hands need their own.
- The body ARMA needs the **`Is Skin`** flag ("Unknown 7" = *use skintone texture*); the hands ARMA needs **`Is Skin Hands`** ("Unknown 8" = *use gloves skintone texture*). Omitting the hands addon/flag is the classic **invisible-hands** bug.
- **Only the *first* model in a NIF receives the skin-tone texture swap** — keep the naked body a single whole piece, and in apparel that shows skin, order the naked-body model first (Starfield Geometry Bridge exports models in alphabetical name order). A face-type `HDPT` receives skin-tone swap automatically (no header edit needed); align the body and head UVs so they share one skin-tone texture.
- Shortcut: copying the vanilla human skin ARMO + its ARMAs and re-pointing them is far less error-prone than building from scratch.

### 2.4 `ARMA` — Armor Addon (the race↔model mapping)

The record that actually binds a worn mesh to a race and gender. **This is where anthropomorphic body/hand meshes get wired in.**

| Sub | Field | Type | Notes |
|---|---|---|---|
| Record flags | `0x40` No Underarmor Scaling, `0x80` **Is Skin**, `0x100` **Is Skin Hands**, `0x400` No Model | flags | "Is Skin"/"Is Skin Hands" mark this addon as body vs hands skin. |
| *component block* | — | — | |
| `BO64` | Biped Object slots | uint64 | Slots this addon fills. |
| `RNAM` | **Race** | FormID → `RACE` | Primary race. |
| `DNAM` | Data | struct | Weapon adjust, male/female priority, detection sound, health-bar offset. |
| Biped Model | `MOD2` (male) / `MOD3` (female) | Model structs | **The worn 3rd-person meshes** (+ `MOLM` material swaps). |
| 1st Person | `MOD4` (male) / `MOD5` (female) | Model structs | First-person meshes. |
| `MOD6`/`MOD7` | Male/Female Alt Skeleton | string | |
| `NAM0`/`NAM1` | Male/Female **Skin Texture** | FormID → `TXST` | Skin texture set for body/hands. |
| `NAM2`/`NAM3` | Male/Female Skin Texture Swap List | FormID → `FLST` | |
| `NAM4`–`NAM7` | Morphs | FormID → `MRPH` | World / 1st-person morph targets. |
| Additional Races | `MODL` ×N | FormID → `RACE` | **Extra races this addon also serves** — add your race here to reuse vanilla addons, or add `HumanRace` to your addon so humans can wear it. |
| `PNAM` | Body Part Data | FormID → `BPTD` | |

**Race-based addon selection (verified — same as `[FO4]`).** Starfield keeps FO4's per-race ARMA
mechanism intact. An `ARMO`'s addon list can hold multiple `ARMA`s; the engine picks the one whose
`RNAM` (or `Additional Races`) matches the wearer's **Armor Race**, falling back to `FNAM` Base Addon
Index. It's used pervasively: vanilla ships 586 HumanRace, 168 HumanCrowdRace, 15 ChildRace, and
per-creature ARMAs; **704 ARMAs populate `Additional Races`** (human apparel routinely serves
`HumanRace + HumanCorpseRace + MannequinRace` with one mesh — e.g. `AA_Naked_Body`). `ChildRace` gets
distinct-mesh ARMAs, the "different mesh per race" case.

**The redirect knob — `RACE.RNAM` (Armor Race) — decides your custom-race armor strategy:**

- **Armor Race = `HumanRace`** (the common custom-race default): armor resolves *as HumanRace*, so a
  custom race uses the **human** ARMAs (human meshes) on its body. All vanilla armor "just works" but is
  shaped for human proportions — fine if the custom body **conforms to human armor**; refit only the
  pieces you want. Zero per-armor edits for vanilla coverage.
- **Armor Race = your custom race**: the engine will auto-select **your** race-keyed ARMAs — but vanilla
  armor (whose ARMAs are `HumanRace`) then won't resolve unless you either add your race to each vanilla
  ARMA's `Additional Races` (reuse the human mesh) or add a custom ARMA to the ARMO's addon list (custom
  mesh). Full fit control, at per-armor override cost. No global "redirect all armor" switch exists.

### 2.5 `HDPT` — Head Part

Head/hair/eyes/ears/muzzle geometry entries referenced by `RACE` and `NPC_`.

| Sub | Field | Type | Notes |
|---|---|---|---|
| `EDID`, component block, `FULL` | | | |
| Model | `wbGenericModel` | Model struct | `MODL` → head-part `.nif`. |
| `DATA` | Flags | uint8 | `0x01` Playable, `0x02` Male, `0x04` Female, `0x10` Is Extra Part, `0x20` Use Solid Tint, `0x40` **Uses Body Texture**, `0x80` Hide with "HideEar" morph. |
| `PNAM` | **Type** | uint32 enum | 0 Misc, 1 Face, 2 Right Eye, 3 Hair, 4 Facial Hair, 5 Scar, 6 Eyebrows, 7 Jewelry, 8 Meatcaps, 9 Teeth, 10 Head Rear, 11 Extra Hair, 12 Left Eye, 13 Eyelashes, **14 Creature Head, 15 Creature Torso, 16 Creature Arms, 17 Creature Legs, 18 Creature Tail, 19 Creature Wings**. |
| `HNAM` | Extra Parts | FormID[] → `HDPT` | Chained sub-parts. |
| `NAM2`/`NAM3` | Color Mapping / Mask | string | |
| `TNAM` | Texture Set | FormID → `TXST` | |
| `RNAM` | Valid Races | FormID → `FLST` | Form-list of races that may use this part — **add your race's FLST here.** |
| `MNAM` | Morph | FormID → `MRPH` | |

The creature-part types (14–19, incl. **Tail** and **Wings**) are directly useful for an anthro race — a tail can be authored as an `HDPT` of type 18.

### 2.6 `TXST` — Texture Set

| Sub | Field | Type | Notes |
|---|---|---|---|
| `EDID`, component block | | | |
| Textures (RGB/A) | `TX00` Diffuse, `TX01` Normal/Gloss, `TX08` Metal, `TX09` Rough, `TX17` AO, `TX19` Opacity | strings | Paths under `textures\` (`.dds` / `.png`→converted). Starfield's PBR set differs from `[FO4]`'s TX00–TX07. |
| `DODT`/`DODT` | Decal data | struct | |
| `DNAM` | Flags | uint16 | `0x01` No Specular, `0x02` **Facegen Textures**, `0x04` Model-Space Normal, `0x10` Default To Box Decal. |
| `MNAM` | **Material** | string | Path to a material (`.mat`) — Starfield binds a TXST to a material file. |

### 2.7 `BPTD` — Body Part Data

Referenced by `RACE.GNAM` and `ARMA.PNAM`; defines dismemberment/hit regions. **Parts are defined by *bone*, not geometry** — each `Body Part` = `BPNN` "Part Node" (a skeleton bone) + health %, VATS-target bone, `NAM4` gore-target bone, `ENAM`/`FNAM` hit-reaction start/end bones, blood material (`MaterialActorSkin`). So Starfield dismemberment is entirely bone-driven and record-level (no mesh segments — unlike `[FO4]`'s `BSSubIndexTriShape`+`.ssf`). One `BPTD` per race (`HumanBodyPartData`, `ChildBodyPartData`, per-creature — 28 total); gore stumps come from the "Meatcaps" HDPT type. A furry race just **reuses `HumanRace`'s BPTD** via `GNAM` — bone-based severing works for free on the human skeleton; field-level edits are rarely needed for a cosmetic race.

### 2.8 Supporting records you will reference

- **`LMSW`** (Layered Material Swap) — targets of `MOLM`; retexture without editing the nif.
- **`FLST`** — form lists (valid-races lists on `HDPT`, skin texture swap lists on `ARMA`).
- **`MRPH`** — morph targets (facegen / body morphs).
- **`NPC_`** — the player and race presets (`RPRM`/`RPRF`).
- **`EQUP`** — equip slots referenced by `RACE`/`ARMO`.
- **`BMOD`** — bone modifiers referenced by `RACE`.
- There is **no `MATO` record** in Starfield's definitions; material objects were replaced by the external `.mat` material system + `LMSW`.

---

## 3. BA2 archive format

Starfield archives are still **`BTDX`** BA2 containers, split **GNRL** (general) vs **DX10** (texture), auto-loaded by matching the plugin name. What changed is the **version number** and a slightly larger header.

### 3.1 Versions observed in the shipped game

Byte 4 of the header is the version `uint32`. From direct dumps of `Data\*.ba2`:

| Version | Seen on | Type |
|---|---|---|
| **1** | `[FO4]` / FO76 archives | GNRL & DX10 |
| **2** | `Starfield - Materials/Interface/Misc/Meshes*.ba2` (GNRL); `Constellation/OldMars/ShatteredSpace/SFBGS* - Textures.ba2` (DX10) | GNRL **and** DX10 |
| **3** | `Starfield - Textures01–09.ba2` (base-game main textures) | DX10 only |

So **version is not simply "GNRL=2, DX10=3."** Reality (confirmed by dumps): **GNRL is always v2**; **DX10 is v2 or v3.** v3 is an optimized texture layout that streams to VRAM faster; base-game bulk textures ship v3 while most DLC/update texture archives ship v2. The community "BA2 Upgrader" tool converts v2 DX10 → v3.

### 3.2 Header layout (from byte dumps)

Common prefix (offsets in bytes):

| Off | Size | Field | Example (GNRL v2 `Meshes01`) |
|---|---|---|---|
| 0 | 4 | Magic `"BTDX"` | `42 54 44 58` |
| 4 | 4 | Version (uint32) | `02 00 00 00` |
| 8 | 4 | Type `"GNRL"`/`"DX10"` | `47 4E 52 4C` |
| 12 | 4 | File count (uint32) | `E3 E3 04 00` → 320 995 |
| 16 | 8 | Name-table offset (uint64) | `CF E3 D7 FE 00…` → `0xFED7E3CF` |
| 24 | 4 | *New in Starfield* — unknown A (uint32) | `01 00 00 00` |
| 28 | 4 | *New in Starfield* — unknown B (uint32) | `00 00 00 00` |
| 32 | … | File records begin (GNRL & v2 DX10) | |

For **v3 DX10** there is one additional `uint32` before the file records (observed value `03`), so v3 file records begin at offset **36**:

```
Textures01 (DX10 v3):
00: 42 54 44 58  03 00 00 00  44 58 31 30  C6 15 00 00   BTDX v3 DX10  count=0x15C6
10: 31 10 E5 FF  00 00 00 00  01 00 00 00  00 00 00 00   nameTblOff=0xFFE51031, A=1, B=0
20: 03 00 00 00  <first DX10 file record...>              v3 extra u32 = 3
```

`[FO4]` v1 had **no** bytes 24–31 — file records began right after the 24-byte prefix. **Unverified:** the exact meaning of unknown-A/B (A is consistently `1`, B `0` across sampled archives; A may be a "compression method present" flag, B reserved).

### 3.3 File records & chunks

**GNRL file entry — 36 bytes, unchanged from `[FO4]`** (verified against `Meshes01`):

| Off | Size | Field |
|---|---|---|
| 0 | 4 | Name hash (uint32) |
| 4 | 4 | File extension (char[4], e.g. `"nif\0"`) |
| 8 | 4 | Directory hash (uint32) |
| 12 | 4 | Flags (uint32) |
| 16 | 8 | Data offset (uint64) |
| 24 | 4 | Packed (compressed) size — 0 if stored |
| 28 | 4 | Unpacked size |
| 32 | 4 | Sentinel `0xBAADF00D` |

**DX10 (texture) entry** keeps the `[FO4]` shape: per-file header (name hash, `"dds\0"`, dir hash, then `numChunks`, `chunkHeaderSize=0x18`, height, width, `numMips`, DXGI `format`, `isCubemap`, `tileMode`), followed by `numChunks` **chunks**, each `[offset u64][packedSize u32][unpackedSize u32][startMip u16][endMip u16][sentinel 0xBAADF00D]`. The DDS header is **not** stored; it is reconstructed on load from these fields — which is why texture BA2s load fast. v3 tweaks the chunk/streaming layout for VRAM upload but keeps the same conceptual structure.

**Compression:** GNRL/DX10 chunks are **zlib** by default, as in `[FO4]`. Starfield additionally introduced **LZ4** for some data. Chunk headers carry packed vs unpacked sizes; packed==0 (or ==unpacked) means stored uncompressed. **Unverified:** which archives use LZ4 vs zlib and how the format flag is encoded — community tools (BSArch Pro, Bethesda Archive Manager) auto-detect.

### 3.4 What's inside — and the `.mesh` split

Starfield geometry is **not** in the `.nif`. Archive naming reflects the split:
- `... - Meshes*.ba2` — `.nif` **container** files under `meshes\`.
- `Starfield - Meshes01/02` also carry `geometries\<hex1>\<hex2>.mesh` — the actual vertex/UV/normal/weight/LOD/meshlet data.
- `... - Materials.ba2` — the `.mat` material database / files under `materials\`.
- `... - Textures*.ba2` (DX10) — `.dds` under `textures\`.

A `BSGeometry` node in a `.nif` stores a **mesh path** string (vanilla: 40 hex chars split `hex1/hex2`) resolving to `geometries\hex1\hex2.mesh` inside a meshes BA2 (or a loose file). The hex name *looks* like a digest but is **not a computed/enforced hash** — nifly/Outfit Studio write arbitrary (even human-readable) names and the game doesn't verify them (the only CRC32 in the pipeline is for *material* resource-ID lookup, not mesh filenames). One `BSGeometry` can reference up to **4** `.mesh` files (LODs). **Note:** game update **1.11.36** reorganized vanilla mesh paths; older mods needed a path-migration tool — author against current paths.

### 3.5 Loose files override archives

Same rule as every Bethesda title: **loose files in `Data\` beat archived files**, and later-loading archives beat earlier ones. Priority high→low:
1. Loose file at `Data\<path>`
2. Later plugin's BA2, then earlier plugins' BA2s (plugin load order)
3. Base-game `Starfield - *.ba2`

During development ship loose; for release pack into `<Plugin> - Main.ba2` (+ `<Plugin> - Textures.ba2`). A BA2 auto-loads when it shares the plugin's base name.

---

## 4. Workflow

### 4.1 Two authoring tools

- **SF1Edit / xEdit** — the record surgeon. Copy vanilla records as overrides/new records, wire FormID links (`WNAM`, `RNAM`, `SRAC`, addon lists), flag master tier, compact FormIDs, detect conflicts, clean ITMs. Fastest for a race mod's record plumbing. Component forms with `REFL` blobs are the one gap.
- **Creation Kit (Starfield)** — the WYSIWYG editor. Needed for facegen/chargen preview, morph setup, and anything with in-editor visualization. Heavier, slower, but authoritative for chargen.

Most race mods do the record work in SF1Edit and use the CK for facegen/preview.

### 4.2 Asset pipeline (mesh → material → texture)

1. Model the body/hands/head/tail in Blender; export to Starfield's **`.mesh`** + **`.nif` container** (community "Starfield Geometry Bridge" / updated NifSkope; PyNifly-style tooling handles the split).
2. Author materials as `.mat` (+ optional `LMSW` layered swaps referenced by `MOLM`).
3. Author PBR textures (`_color`, `_normal`, `_rough`, `_metal`, `_ao`, `_opacity` `.dds`) and bind them via a `TXST`.
4. Place files under `Data\meshes\`, `Data\geometries\`, `Data\materials\`, `Data\textures\` (loose while iterating).

### 4.3 Records a custom-race mod must create/edit

The concrete plumbing (see checklist at end). Load order: your race `.esm` (small- or medium-master flagged) after `Starfield.esm` and any masters whose assets you reuse. Keep new FormIDs in the correct tier range so the flag stays valid.

### 4.4 Packaging & shipping

1. Finalize the plugin; **compact FormIDs** to the small/medium range and set the tier flag (LOOT or xEdit).
2. Pack assets: `BSArch`/BSArch Pro or Bethesda Archive Manager → `<Plugin> - Main.ba2` (v2 GNRL: meshes, geometries, materials) and `<Plugin> - Textures.ba2` (v2 or v3 DX10: textures). **Note:** a `<Plugin> - Meshes.ba2` is **no longer recognized** by Starfield — meshes/geometries go in `- Main.ba2`.
3. Confirm archive base names match the plugin so they auto-load.
4. Ship plugin + BA2s (+ any loose overrides). Test with loose files first, then verify packed.

---

## Records a custom-race mod must create / edit — checklist

- [ ] **`RACE`** — copy `HumanRace` [`0000347D`] as a new record. Set `FULL`/`DESC`; point `WNAM`→your skin ARMO; set `RNAM` (Armor Race)=`HumanRace` and `SRAC` (Subgraph Template Race)=`HumanRace` to inherit armor fit + animations; set `NAM8` (Morph Race)=`HumanRace` to inherit facegen; populate Head Parts list, skeleton-data model paths, and chargen/skintone paths.
- [ ] **`ARMO` (skin)** — the naked-body armor referenced by `RACE.WNAM`. Set `RNAM`→your race; `Models` list maps addon indices to the body and hands `ARMA` records.
- [ ] **`ARMA` (body)** — flag **Is Skin**; `RNAM`→your race (+ add `HumanRace` under Additional Races if reusing human armor); set male/female Biped Model `.nif`s and `NAM0`/`NAM1` skin `TXST`; set `BO64` body slots.
- [ ] **`ARMA` (hands)** — flag **Is Skin Hands**; same wiring for the hands slot (fixes the classic "invisible hands/limbs" pitfall — every skin slot needs its own addon).
- [ ] **`TXST`** — skin texture set(s): diffuse/normal/rough/metal/AO/opacity + `MNAM` material; referenced by the `ARMA` `NAM0`/`NAM1`.
- [ ] **`HDPT`** — head/ears/muzzle/**tail**/**wings** parts (types 14–19 for creature parts). Set `TNAM`→TXST, `RNAM`→valid-races `FLST`, add to `RACE` head-part list.
- [ ] **`FLST`** — valid-races form list for your `HDPT` records (include your race, optionally `HumanRace`).
- [ ] **`MRPH`** — morph targets if the race uses body/face morphs (optional; some races skip head morphs).
- [ ] **`LMSW`** *(optional)* — layered material swaps for retexture variants via `MOLM`.
- [ ] **`NPC_`** *(optional)* — race presets (`RPRM`/`RPRF`) and any test actor.
- [ ] **`BPTD`** — reuse `HumanRace`'s unless adding severable limbs (e.g. a tail hit region).
- [ ] **Plugin/TES4** — set author/description, add masters (`Starfield.esm` + any asset donors), choose master tier (small if ≤4095 new records, else medium), keep FormIDs in range.
- [ ] **Assets** — `.nif` containers + `.mesh` geometry + `.mat` materials + `.dds` textures under the right `Data\` subfolders; pack to `<Plugin> - Main.ba2` / `<Plugin> - Textures.ba2`.

---

## Sources

- xEdit / SF1Edit record & header definitions — `wbDefinitionsSF1.pas` (TES5Edit-dev 4.1.6 Core), authoritative for RACE/ARMO/ARMA/HDPT/TXST/BPTD/TES4 fields, component list, and master flags. Repository: <https://github.com/TES5Edit/TES5Edit>
- Direct byte dumps of shipped `Data\*.ba2` archives (Starfield base game + DLC) for BA2 magic/version/type/header/file-record layout.
- Starfield Wiki — Archive2 / BA2 format (GNRL vs DX10, v1/v2/v3): <https://starfieldwiki.net/wiki/Starfield_Mod:Archive2>
- `ba2` Rust crate docs (FO4/Starfield BA2 structures, DX10Header/Chunk/CompressionFormat, zlib+lz4): <https://docs.rs/ba2/latest/ba2/fo4/index.html>
- BA2 Upgrader — Upgrade to BA2 Version 3 (Starfield Nexus, v2→v3 texture format): <https://www.nexusmods.com/starfield/mods/1192>
- Bethesda Archive Manager (create/extract Starfield BA2): <https://www.nexusmods.com/starfield/mods/14468>
- Ortham, "Load order in Starfield" (full/medium/small masters, FormID ranges, flags): <https://blog.ortham.net/posts/2024-06-28-load-order-in-starfield/>
- Modding.wiki — Converting ESMs to ESPs (master tiers & conversion): <https://modding.wiki/en/starfield/developers/tutorials/ESMtoESP>
- LOOT — Changing plugin types in Starfield: <https://loot.github.io/docs/help/Changing-Plugin-Types-In-Starfield.html>
- Nexus — "Notes and pitfalls on creating a playable race" (RACE/ARMO/ARMA workflow, skin body+hands split, RNAM/SRAC, invisible-limb fix): <https://www.nexusmods.com/starfield/articles/431>
- Nexus — "Organization of Starfield's Meshes and Related Assets" (.nif container vs external .mesh, BSGeometry hash path, up-to-4 meshes): <https://www.nexusmods.com/starfield/articles/268>
- Nexus — .nif Mesh Path Migration Tool for SF 1.11.36 (mesh-path hashing change): <https://www.nexusmods.com/starfield/mods/9234>
- NifSkope Starfield support PSA (BSGeometry / mesh references): <https://github.com/niftools/nifskope/issues/232>
- fre-sch, "Starfield guide for creating new ship parts" (GBFM / component / BFCB structure in xEdit): <https://gist.github.com/fre-sch/ea74bc201be01c8e656991baacfc9702>

_Draft 2026-07-06 — not yet reviewed_
