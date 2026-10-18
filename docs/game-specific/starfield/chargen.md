# Starfield: Character Generation, Race, Skeleton & Body

Everything the Starfield engine needs to build, morph, tint, skin, and bake a
playable character — with an eye toward what a **custom anthropomorphic (furry)
playable race** would require. Starfield's chargen is a direct descendant of the
Fallout 4 / Skyrim system, but nearly every piece has been rebuilt: geometry
lives in external `.mesh` files, morphs are `.morph`/`.dat` deltas, tints are a
layered "AVM" material system, and animated appendages can be driven by **Bone
Modifiers (BMOD)** attached at the race level instead of a hand-authored Havok
behavior graph.

Record field names below come from the SF1Edit (xEdit) Starfield record
definitions (`wbDefinitionsSF1.pas`), cross-checked against `Starfield.esm`.
Mesh/skeleton details come from nifly's `BSGeometry` implementation and community
tooling (Starfield Geometry Bridge / StarfieldMeshConverter). Community-folklore
claims are marked **Unverified**.

---

## 1. The RACE record

### How races are used (verified against `Starfield.esm`)

`Starfield.esm` contains just **31 `RACE` records**, and **essentially every human
person in the game is the single `HumanRace [0000347D]`**. Starfield dropped the
many-races model — there is no race choice in chargen; all human variety is
appearance/morphs on that one race. The only other humanoid races are
`HumanCorpseRace [00034FB1]` (bodies), `ChildRace [002AABCD]`,
`HumanCrowdRace [002BBC09]` (ambient background crowds), and
`MannequinRace [001EE4DA]`; the remaining ~26 are creatures/fauna
(`QuadrupedA/B/C`, `BipedA`, `FloaterA`, `Terrormorph`…) and machines
(`AutopilotRace`, `*TurretRace`, `SecurityCameraRace`…).

When generating a custom race, you generally want to start by cloning HumanRace — you
inherit everything the game's race checks rely on. Two possible design paths:

- **Clone HumanRace → a new race**, assigned to the player and chosen NPCs. Selective,
  toggleable, mod-compatible (the article-431 route documented below), can share the world
  with humans.
- **Override `HumanRace` itself** (swap its skin ARMO / default head parts) →
  *everyone* changes, with no per-NPC editing, but it's total, not toggleable, and
  conflicts with other appearance/body mods. Ambient crowds are `HumanCrowdRace`
  (override that too for full coverage); kids are `ChildRace`.

**Where race boundaries should fall**: When you have multiple closely-related races (wolf,
jackal, fox) you might make each its own race or you might make one "Canid" race with
these being customizations (using Starfield's ethnicity mechanism, perhaps). HOWEVER,
texture layers are not race-specific -- there's one texture stack for the entire game. So
you won't be able to cleanly separate textures for the different species, and you'll have
to create extra textures just to fill in all the slots. It's likely more convenient to put
each species in its own race -- possibly sharing a single head with morphs for the
different head shapes.

**What actually "notices" a race swap**: conditions testing a **keyword**
(`ActorTypeNPC`/`ActorTypeHuman`, etc.) **pass** — a clone inherits HumanRace's keywords,
covering most generic AI/quest/dialogue checks. Conditions testing the **specific race
form** (`GetIsRace HumanRace`) or a **race form-list** **fail** until you add your race —
which is exactly what the finishing-fix form-lists patch (e.g.
`HumanRaceORChildRaceORHumanCorpseRace [CNDF:0003D8C1]`; see §9). Changing the race of
named NPCs also means re-baking **FaceGen** for each NPC.

**Selecting the player's race is done by plugin, not in the creator** (same as `[FO4]`):
Starfield has no in-chargen race picker, so a mod sets the player's race by **overriding
the player NPC record (form `7`) + its 12 copies** (article 431). 

### Ambient crowds (`HumanCrowdRace`) — generated on the fly

Background city crowds are **not** hand-authored NPCs with baked FaceGen — they use a
separate, deliberately lightweight race (`HumanCrowdRace [002BBC09]`) and a
**data-driven spawn system**:

- The crowd race has its own crowd body skin (`Skin_Crowd_Base_Body_NOTPLAYABLE`) and
  its own skeleton (`actors\human_crowd\…\skeleton.nif`) but shares human animations/
  rig. Crucially it carries **almost no chargen data** — no race presets, no morph
  groups, **no race-level head-part list** (just a "default" phenotype + a skin index).
- Crowds draw on **per-location leveled lists**: `LCharCrowdKeywords_DEFAULT`
  (+ `_Akila` / `_NewAtlantisWell` / `_NeonUnderbelly`) is a list of ~58 template NPCs
  named by **mood × prop** (`CrowdActor_KEYWORDS_Angry_Briefcase`, `_Angry_Coffee`…),
  fed into the actors' **Keywords** template slot; `LCharCrowdVoices_Male/Female` list
  voice templates. (The engine also LOD-renders distant ambient walkers on top.)
- **The crowd actor records carry no face** — but the face is **not** engine-generated
  from scratch; it's a **randomly-equipped head ARMO**. Verified across the 181
  `CrowdActor_*` NPC records: each has `RNAM`=HumanCrowdRace, `WNAM`=crowd body skin, a
  skin-tone index, a **randomized height range** (e.g. 0.98–1.02), an outfit and a voice
  — but **no `PNAM` head parts, no face morphs, `EDCT` (tint count) = 0**. Most (95 of 138)
  inherit only Factions and Keywords, but **24 also inherit Traits** from the voice lists,
  and Traits carries race ([crowds §2](crowds.md#2-the-crowd-actors)). The head instead
  comes from the **outfit**: each `Outfit_Crowds_*` equips
  clothing **plus a leveled list `LL_Crowd_Heads [000F4E92]`** (variants
  `_Overweight` / `_Thin`) that draws one of **8 authored `CrowdHead_<phenotype>` ARMOs**
  (`CrowdHead_af_md1`, `_eu_yo1`, … ethnicity×age). A `CrowdHead` ARMO sits on **biped
  slot 2 (Hide Head)** and shows its head mesh via an `AA_CrowdHead_*` addon. So a crowd
  face = a random head ARMO from a finite pool + random height. No per-NPC FaceGen, and
  no skin tone on the head: each crowd head is one mesh (head, eyes and arms) with its own
  baked textures ([crowds §3](crowds.md#3-the-crowd-head)).

**Full crowd appearance pipeline:**
```
CrowdActor NPC → DOFT: Outfit_Crowds_<location>
                    ├─ clothing items
                    └─ LL_Crowd_Heads (leveled list, 8 CrowdHead_* ARMOs)
                          └─ random CrowdHead_<phenotype>  → ARMO on slot 2 (Hide Head)
                                └─ AA_CrowdHead_* addon → head mesh
  body: WNAM = Skin_Crowd_Base_Body   ·   skin tone: STON   ·   height: randomized
```

**Modding implication (appearance):** the head is an **equippable ARMO chosen by a
leveled list**, so a crowd of another species is a data job, not per-NPC FaceGen. What
worked in game for a fox crowd (October 2026): its own crowd race, new NPCs copied from
crowd actors (with inherited Traits turned off), and fox head armors on a new head list in
those NPCs' outfits, leaving every vanilla record alone. Because the head carries the arms
and hands, the head is the only part that needs to show species; a crowd outfit is one
full-body garment, a head and a hair-or-hat. The details, including the `_facebones` copy,
the `BoneTrn` eye positions and the open question of tails, are on the
[crowds page](crowds.md#5-a-crowd-of-another-species).

### Record fields

Signature `RACE`. Far larger than its predecessors. The parts that matter for a
new race:

### Core data (`DAT2` "Data" struct)
| Field | Meaning |
|---|---|
| Male Height / Female Height | scale multipliers |
| Male/Female Default Weight | three floats each: **Thin / Muscular / Fat** — the body-triangle anchors |
| Head Biped Object | biped slot index that counts as "head" |
| Hair Biped Object | slot index for hair |
| Beard Biped Object | slot index for beard |
| Body Biped Object | slot index for body |
| Shield Biped Object / Pipboy Biped Object | slot indices |
| Flags (u64), Intelligence Level | AI/behavior |
| OnCripple / Bleedout / Electromagnetic Shocked | combat-dismemberment reactions |

`WNAM` **Skin** → `ARMO` (the default skin armor — the body/hands mesh set).
`GNAM` **Body Part Data** → `BPTD` (dismemberment regions; see the
`dismemberment.md` page for the FO4/Skyrim ancestor).

### Skeleton Data (per gender)
```
Skeleton Data
├─ Male Data   (MNAM marker)
│   ├─ ANAM  Skeletal Model     — path to the skeleton .nif
│   ├─ NAM5  Skeleton Rig
│   ├─ NAM6  Animation Root
│   └─ DNAM  Animations
└─ Female Data (FNAM marker)    — same fields
```
This is where a custom-skeleton race points at its own `skeleton.nif`,
rig, and animation root. Contrast `[Skyrim]`/`[FO4]` which used a single
`ANAM Skeletal Model` string per gender with far less structure.

### FaceGen clamps
- `PNAM` **FaceGen – Main clamp**
- `UNAM` **FaceGen – Face clamp**

These bound how far the chargen morphs may push the face.

### Biped Object Names / Conditions
- `NAME` × **64** — human-readable names for the 64 biped slots.
- `RBPC` × 64 — a per-slot condition (`AVIF`) gating whether the slot shows.

Compare `[FO4]` 32 biped slots / `[Skyrim]` 32 body-part flags — Starfield
doubles it to 64 and splits armor vs. **spacesuit ("SS")** variants (see §7).

### Chargen and Skintones (per gender) — the character-creator payload

**Phenotypes**: Much of character customization depends on "phenotypes", a new concept in
Starfield. A phenotype describes a basic look for a head. Starfield phenotype names follow
the form `<sex>_<ethnicity>_<age>`, where "sex" = male/female, "ethnicity" = af
(african)/as (asian)/eu (european), and "age" = md (middle aged)/ol (old)/yo (young).
That's 18 variants jut to cover the ground; variation *within* phenotype is in addition to
that. Phenotypes can control both facial morphs and textures.

```
Chargen and Skintones
└─ Male / Female
   ├─ Chargen (NAM0 marker)
   │   ├─ Race Presets      RPRM/RPRF → NPC_  (preset faces in the creator)
   │   ├─ Morph Groups      MPGN name + MPGM morph-name list
   │   ├─ Face Morph Phenotypes  FMRI index + FMRN name  (named face presets)
   │   ├─ Skin Tone AVMS Subtype (FDDS string)
   │   └─ Face Dials        FDSI Skin Index + FDSL Label  (individual sliders)
   ├─ Body Skin Tones   (BSTT string path)
   ├─ Hand Skin Tones   (HSTT string path)
   ├─ Face Custom Textures Base Path  (FCTP)
   └─ Face Skin Tones   (FSTT string path)
```
So the creator UI is **data-driven from the RACE record**: the list of
sliders ("Face Dials"), the named presets ("Face Morph Phenotypes"), the
grouped morphs ("Morph Groups"), and the skin-tone palettes are all here.
There is no separate "genes" record type — what players call the "genes"
system is this combination of **face dials + morph phenotypes + shape-blend
morphs + skin-tone AVM subtypes**.

#### Field reference (what SF1Edit shows under "Chargen and Skintones")

| Record | Label | Meaning |
|---|---|---|
| `MNAM` / `FNAM` | Male Data / Female Data | per-gender marker (the whole block repeats for each sex) |
| `NAM0` | Chargen | start of the chargen block |
| `RPRM` / `RPRF` | Race Presets (male/female) → `NPC_` | the preset faces scrolled in the creator; each points to an `NPC_` defining a full face |
| `MPGN` + `MPGM` | **Morph Groups** | `MPGN` = group name = a **face region** (`Cheeks, Chin, Ears, Eyes, Forehead, Jaw, Mouth, Neck, Nose`); `MPGM` = the list of morph-key names in that region — **one per phenotype** (e.g. `male_af_md1_Cheeks`, `male_eu_md2_Cheeks`, …). These are the creator's per-region sliders; the names are the keys in the chargen `morph.dat` (§3). |
| `FMRI` + `FMRU`/`FMRN`/`FMRS` | **Face Morph Phenotypes** | the named **base faces**: ethnicity (`af`/`as`/`eu`) × age (`yo`/`md`/`ol`) = **9** (`male_af_md1`, `male_eu_md2`, `female_as_yo1`, …). `FMRU` and `FMRS` are the raw name; `FMRN` is the localized display name (a string ID in `Starfield.esm`, literal text in an unlocalized plugin). **`FMRI` is not a positional index — it is the `ID` of a region in the race's `FacialBoneRegions<Sex>.txt`**, so the values are sparse (male: 1, 9, 12, 14, 16, 40, 42, 44, 46). |
| `FMSR` + `FMRU`/`FMRN` | **sculpt regions** | interleaved into the *same* numbered table as `FMRI`, these are the 11 `SculptRegion: true` regions — `Head Shapes`, `Cheeks`, `Chin`, `Ears`, `Eyebrows`, `Eyes`, `Forehead`, `Jaw`, `Mouth`, `Neck`, `Nose` (male IDs 22, 26, 30, 34, 38, 50, 56, 62, 66, 72, 82). Both kinds of row are entries in one flat table whose IDs run in increasing order. NOTE, As of this writing, xEdit shows these nested under FMRI -- it's clearer to think of them as at the same level, interleaved. |
| `FDDS` | Skin Tone AVMS Subtype | presumably names the AVM schema (§4) the skin tones conform to — but **neither `HumanRace` nor any shipped custom race sets it**, so the purpose is unconfirmed. |
| `FDSI` + `FDSL` | **Face Dials** | the individual named **sliders** in the creator. ⚠ xEdit labels `FDSI` "Skin Index" and it is **nothing to do with skin tones** — it is a **sculpt-slider ID**, the same space the NPC's `FMSI` indexes. `HumanRace` carries **40 dials per sex**, sparse (24, 25, 27, 28, 29, 31, … 85), and 24/25/76/77 are exactly the sliders the Mouth region (ID 22) owns — see §3. `FDSL` is the translatable label (`'down - up'`, `'narrow - wide'`). |
| `BSTT` / `HSTT` / `FSTT` | Body / Hand / **Face** Skin Tones | the AVM skin-tone group names the race draws its skin from (§4); a custom race points these at its own groups (guide 431, §"Adding skin tones") |
| `FCTP` | Face Custom Textures Base Path | the directory (under `Data\Textures\`) the **FaceGen bake** reads its base face maps from, by filename convention — `<phenotype>_sk<N>_color/_normal/_rough/_ao.dds` plus the per-region blend masks `FCT_<region>_mask.dds` ([§4.5](#how-the-phenotype-maps-are-chosen-and-blended)). Vanilla `HumanRace` omits it and falls back to `[Facegen] sSkinTexturePath` (default `Actors\Human\Faces\Chargen`); `FelidRace` sets `actors\Felid\faces\chargen`. **A custom race should set this** — see [Creation Kit §3](creation-kit.md#3-where-the-bake-gets-its-source-textures-fctp-and-the-filename-convention). |

**How it composes:** **9 regions × 18 phenotypes = 162 chargen morphs** (§3), named
`<phenotype>_<region>` — `male_as_md1_Cheeks`, `female_eu_yo1_Nose`. Morph Groups list
those names per region; Face Morph Phenotypes name the base faces the sliders blend
between; Face Dials are extra individual sliders. **The same phenotype vocabulary
addresses two different deformation systems** — the vertex morphs here, and the bone
morphs in the race's `FacialBoneRegions` file, which uses the identical names. §3 covers
how an NPC drives both.

A custom race authors its own `MPGN`/`MPGM` + `FMRI`/`FMRU` and its own skin-tone AVM groups
(`BSTT`/`HSTT`/`FSTT`). Keep the two halves consistent: a phenotype named `X` implies morph keys
`X_Cheeks`, `X_Nose` and so on, and a region `ID` that exists in the `FacialBoneRegions` file.

### Head Parts and Bone Modifiers (per gender)
```
Head Parts and Bone Modifiers
└─ Male Data / Female Data
   ├─ Head Parts    INDX index + HEAD → HDPT   (the default head-part set)
   └─ Bone Modifiers  BNAM → BMOD               (runtime bone behaviors — §6)
```

### Other race links
- `NAM8` **Morph Race** → RACE (which race's morphs to borrow)
- `RNAM` **Armor Race** → RACE (which race's armor addons fit)
- `SRAC` **Subgraph Template Race** + **Subgraph Data** (`SGNM` Behaviour Graph
  path, `SAPT` Animation Paths, role/perspective flags) — the Havok behavior
  wiring, normally inherited from `HumanRace`.
- `VTCK` Voices, `MTNM` Movement Type Names, `WKMV/SWMV/FLMV/SNMV` movement
  defaults, `UNWP` Unarmed Weapon.

### What the RACE record does *not* reach {#records-the-engine-finds-directly}

**A custom race is not self-contained.** Some of what the engine needs it finds by a
**hardcoded FormID** or by a **naming convention**, never by following a link out of your
RACE record. Nothing in your plugin points at these, so nothing warns you when they are
wrong — the failure is always silent, and usually looks like "works in the Creation Kit,
broken in game".

Consolidated, with the symptom when each is missed:

| What | Reached how | Miss it and… |
|---|---|---|
| `HeadPartsChargenOptionsMale [FLST:0003D9AF]` / `…Female [0003D9B0]` | hardcoded FormID | your head parts never appear as creator choices; the creator fits the *human* part to your skull |
| `CharGenPresets [FLST:0003F551]` | hardcoded FormID | the creator's preset row still offers human faces (each preset's head comes from that NPC's **own** race) |
| **The player records** (`Player [NPC_:00000007]` + its copies) | hardcoded FormID | you stay human where it matters — see [§9](#9-building-a-custom-race) for the full list |
| `HumanRaceORChildRaceORHumanCorpseRace [CNDF:0003D8C1]` | hardcoded FormID | spacesuit does not show |
| `DC_Race_Human [CPTH:000C1056]` | hardcoded FormID | dialogue camera sits too close |
| `Clothes_GenWare_01 "Space Undersuit" [ARMO:00165722]` | hardcoded FormID | invisible limbs in new-game chargen |
| `SimpleGroup_EyebrowOpacity [AVMD:0000EF9F]` | by **name** | eyebrows render fully transparent |
| Every `AVMD` tint slot (`Dermaesthetic`, `EyeColor`, …) | by **name** (§4.4) | a group you invented under a new name is simply never read; you must override the vanilla name or extend it with `AVMP` (§4.11) |
| `Chargen_*` twin tint groups | by **name** | the Creation Kit looks right and the in-game creator does not — CK reads the runtime group, the creator reads the `Chargen_` twin |
| `…FacialBoneRegions<Sex>.txt` + `…Mapping.csv` | **race EDID** filename | face morph regions do not resolve |
| `BaseHead<RaceEDID><Sex>_<map>.dds` | **race EDID** filename | rename the race and the old bake orphans silently → black/stale head (§8) |
| The four `FCTP` face maps | **filename convention** in the race's `FCTP` directory | a missing normal renders the face black (§1 `FCTP`) |

⚠ **Renaming your race EDID breaks the last three at once**, and none of them will tell you.

---

## 2. Head Parts (`HDPT`)

Signature `HDPT`. **This is the single most important record for a furry race** —
Starfield added dedicated **Creature** head-part types.

### Type enum (`PNAM`)
| # | Type | | # | Type |
|---|---|---|---|---|
| 0 | Misc | | 10 | Head Rear |
| 1 | Face | | 11 | Extra Hair |
| 2 | Right Eye | | 12 | Left Eye |
| 3 | Hair | | 13 | Eyelashes |
| 4 | Facial Hair | | 14 | **Creature Head** |
| 5 | Scar | | 15 | **Creature Torso** |
| 6 | Eyebrows | | 16 | **Creature Arms** |
| 7 | Jewelry | | 17 | **Creature Legs** |
| 8 | Meatcaps | | 18 | **Creature Tail** |
| 9 | Teeth | | 19 | **Creature Wings** |

Types 14–19 are Bethesda's built-in hooks for non-human morphology. A muzzle/
snout would most naturally be a **Creature Head** (or a Face + extra part), a
tail a **Creature Tail**, ears a Head-Rear/Extra part or a Creature part.
Note the split of eyes into **Right Eye / Left Eye** (vs `[Skyrim]`/`[FO4]`
single "Eyes"), plus new **Meatcaps** (gore stumps), **Head Rear**, **Eyelashes**.

### HDPT fields
| Field | Meaning |
|---|---|
| DATA Flags | `Playable`, `Male`, `Female`, `Is Extra Part`, `Use Solid Tint`, `Uses Body Texture`, `Hide with "HideEar" Morph` |
| Model | `.nif` path (which points at an external `.mesh` — §5) |
| HNAM Extra Parts | list of sub-HDPTs pulled in together (e.g. a head that also spawns eyes) |
| NAM2 Color Mapping | AVMS/AVMD color-group name |
| NAM3 Mask | tint mask name |
| TNAM Texture Set | → `TXST` |
| RNAM **Valid Races** | → `FLST` (a FormID list of races the part is offered to) |
| MNAM **Morph** | → `MRPH` (the morphable-object record; **replaces the TRI reference**) |

`RNAM Valid Races` is the mechanism by which a new head part is offered in the
creator only to your race. The `Hide with "HideEar" Morph` flag ties a whole
head part's **visibility** to the **Hide Ear** toggle (biped slot 19), which
helmets/headgear occupy — so the part vanishes when headgear is worn. Handy for a
separate horn or ear part that should disappear under a helmet. (Ears *integrated
into the head mesh* instead use the head's own `HideEar` **morph** to collapse the
ear region — see §3 Expressions.)

**The `.nif` and the morph.dat are siblings under `HDPT`, not linked to each
other.** A head part points at its mesh through **Model** (`meshes/…/*.nif` → an
external `.mesh`) and at its morphs through **`MNAM` → `MRPH` → `TMPP`/`TCMP`**
(`meshes/morphs/…/morph.dat`). Nothing inside the NIF references the morph file:
the two live in different trees (`meshes/` vs `meshes/morphs/`), their names don't
correspond, and the only thing that binds them is the shared `HDPT` record. So a
tool importing a head NIF **cannot auto-discover its morphs** — the association has
to come from the record (or be supplied by the user). The Creation Kit's **"tri"
field** on a head part is this `MNAM` → `MRPH` reference (the label is a Skyrim/FO4
legacy — Starfield morphs are `morph.dat`, not `.tri`); it **is** used, and every
vanilla Face / Eyebrows / Teeth / Eyelashes head part sets it.

---

## 3. Morphs — `MRPH` record and `morph.dat` geometry

`[Skyrim]`/`[FO4]` used `.tri` files referenced by a `BODYTRI`/`FaceGen`
`NiStringExtraData`. **Starfield replaces `.tri` with a `MRPH` "Morphable
Object" record plus external morph-delta files.**

### `MRPH` record fields
| Field | Meaning |
|---|---|
| `TMPP` Target Morph Path | expression/animation morph file |
| `TCMP` Target Chargen Morph Path | the chargen-slider morph file |
| `BMPP` Bone Morph Definition File | drives **bones** from morph values (skeletal morphs) |
| `MOBC` Base Vertex Color | base color for the morphed mesh |

Key insight: a `MRPH` separates the **performance morphs** (expressions,
visemes) from the **chargen morphs** (creator sliders). `BMPP` can additionally
map morph sliders onto **bone transforms** — but note that vanilla head/body
`MRPH` records and shipped custom races leave `BMPP` empty; the bone-driven face
shaping actually in use is the FacialBoneRegions system described below, which
is wired by file-naming convention rather than through `MRPH`.

### Expressions (performance morphs) — verified from vanilla assets

Facial **expressions and lip-sync are blendshape morphs**, stored in a
**separate `performance/` `morph.dat`** from the creator sliders. The morph tree
splits every head part three ways:

```
meshes/morphs/human/<sex>/performance/head/morph.dat   ← runtime expressions
meshes/morphs/human/<sex>/chargen/head/morph.dat        ← creator sliders
meshes/morphs/.../chargen/facefx/morph.dat              ← chargen-time face-FX preview
```

The extracted human female **`performance/head/morph.dat`** has **96 shape keys**
(15370 verts) — textbook **FACS action units**: `jawOpen`, `jawClench`,
`jawLeft/Right/Thrust`, `browLowererL/R`, `innerBrowRaiseL/R`, `outerBrowRaiseL/R`,
`eyeClosedL/R`, `eyeOpenL/R`, `squintL/R`, `lidTightenerL/R`, `cheekPuffL/R`,
`cheekRaiseL/R`, `dimplerL/R`, `lipCornerPullL/R`, `lipCornerDepressL/R`,
`lipStretchL/R`, `lipPucker`, `lipPress`, `upperLipRaiseL/R`, `lowerLipDepressL/R`,
`noseWrinkleL/R`, `nostrilDilator`, `chinRaise`, `neckFlexL/R`, `swallow`,
`HideEar`, plus `c_`-prefixed **combination/corrective** morphs (e.g.
`c_eyeLeft_eyeClosedL`, `c_squintL_cheekRaiserL`) that fire when two action units
co-activate. These action units double as **visemes** for lip-sync.

By contrast the **`chargen/head/morph.dat`** (84 keys) holds the *creator*
morphs. Its structure is exactly **3 body-shape keys + 9 phenotype presets × 9
face regions** (verified on the vanilla male & female head morph.dat):

- **Body shape (3):** `Overweight`, `Thin`, `Strong` (the same three keys as the
  `chargen/body/morph.dat`).
- **Face presets (81):** `<sex>_<ethnicity>_<age>_<Region>`.
  - **9 phenotype presets** = ethnicity `af`/`as`/`eu` × age `yo`/`md`/`ol`
    (young/mid/old), i.e. `af_md1`, `af_ol1`, `af_yo1`, `as_md1`, `as_ol1`,
    `as_yo1`, `eu_md2`, `eu_ol1`, `eu_yo1`. (Note `eu` uses `md2` where `af`/`as` use `md1` -- it's not clear why.)
  - **9 regions** = `Cheeks`, `Chin`, `Ears`, `Eyes`, `Forehead`, `Jaw`, `Mouth`,
    `Neck`, `Nose`.

So `male_eu_md2_Cheeks`, `female_af_yo1_Jaw`, etc. — each region exposes 9 sliders
(one per preset), and the creator blends them per region. The two channels are
entirely distinct sets, referenced by `MRPH.TMPP` (performance) vs `MRPH.TCMP`
(chargen). A specific NPC's face is then built from these: the `NPC_` record's
**Face Morphs** array holds `FMRI` face-morph indices (into this preset set) plus
per-region **Morph Groups** (`FMRG` name + `FMRS` blend intensity), and its `MRSV`
**Body Morph Region Values** blend the body-shape keys.

Each face part (head, eyebrows, eyelashes, teeth…) has its own
`performance/morph.dat`, so the whole face animates together. The runtime
**in-house animation/behavior system** (`.agx`/`.af`) drives which action units
blend for dialogue emotion, idle emotes, and lip-sync. (The `_facebones.nif` rig
is a *separate* mechanism — facial-**region bone** weighting for chargen sculpting;
expressions themselves are morph-based, not bone-based.)

**Every attached face part carries its own `performance/morph.dat` holding a
*subset* of the same named action units** — not just head/eyebrows/eyelashes/teeth
but **every individual hairstyle** (and tear meshes, hair beads, etc.). Sizes scale
to what each part needs: the head has 96 keys, an eyebrow 54, a tear mesh 73, and a
hair mesh only ~15 (the big `jawOpen`/`jawThrust`/`neckFlex`/`browLowerer`
deformations that drag the scalp — no fine lip morphs). When the animation system
sets an action unit, **every part with that key deforms by its own authored delta**,
which is how hair/brows/eyelashes stay glued to the moving face. There are **no
emotion- or phoneme-named morphs** — moods and visemes are both composed from these
raw action units by the animation system.

#### The full expression-AU vocabulary (verified from vanilla `performance/head/morph.dat`)

The complete facial set is **96 action units on the head** (the female head is the
superset; the male head has 88 — the 8 extra are all `c_…` combination morphs, no
male-only keys). These are the names a custom head's `performance/morph.dat` must
reproduce to animate/lip-sync. **75 primary AUs**, grouped by region:

```
Brow    browLowererL/R  innerBrowRaiseL/R  outerBrowRaiseL/R
Eye     eyeClosedL/R  eyeOpenL/R  eyeUp  eyeDown  eyeLeft  eyeRight
        lidTightenerL/R  squintL/R
Cheek   cheekPuffL/R  cheekRaiseL/R  cheekSuckL/R  dimplerL/R
Nose    noseWrinkleL/R  noseDepressor  nostrilCompressor  nostrilDilator
        nasolabialFurrowL/R
Jaw     jawOpen  jawClench  jawLeft  jawRight  jawThrust
Upper   upperLipRaiseL/R  upperLipDownL/R  upperLipFunnel  upperLipPuff
 lip    upperLipSuck  upperLipThickness
Lower   lowerLipDepressL/R  lowerLipUpL/R  lowerLipFunnel  lowerLipPuff
 lip    lowerLipSuck  lowerLipThickness
Lip     lipCornerPullL/R  lipCornerDepressL/R  lipCornerInL/R  lipStretchL/R
 shape  lipPucker  lipPress  lipTighten  lipZipperL/R  sharpLipPullL/R
Chin    chinRaise  chinRaiseUpperlipTweak
Neck    neckFlexL/R  swallow
Ear     HideEar          (collapses the ear region for helmet fit — biped slot 19)
```

Plus **21 combination/corrective `c_` morphs** that fire when two AUs co-activate
(`c_jawdrop`, `c_eyeDown_eyeClosedL/R`, `c_eyeUp_eyeClosedL/R`, `c_eyeLeft_eyeClosedL/R`,
`c_eyeRight_eyeClosedL/R`, `c_eyesClosed50L/R`, `c_squintL/R_eyesClosedL/R`,
`c_squintL/R_cheekRaiserL/R`, `c_cheekRaiserL_eyesClosedL/R`,
`c_innerBrowRaiserL/R_browLowererL/R`, `c_puckerer_lowerFunneler`,
`c_puckerer_upperFunneler`).

Other parts carry a **subset** of the same names plus their own extras: the **tongue**
adds `tongueIn/Out`, `tongueUp/Down`, `tongueLeft/Right`, `tongueCurlUp/Down`,
`tongueThick`, `tongueThinner`; **headgear** (hats/masks) carry `Hat` / `Mask` hide
morphs in a performance file. Every hairstyle, eyebrow (54), eyelash (top 65 / bottom 47),
teeth (29) and tear (73) mesh carries its own subset so it deforms with the face.

> **Tooling note.** Splitting authored shape keys into the two output files is a name test:
> a shape key whose name is in this AU vocabulary (+ tongue / `Hat` / `Mask`) exports to
> `…/performance/<part>/morph.dat`; everything else is a creator slider and exports to
> `…/chargen/<part>/morph.dat`.

> **Furry-race implications.**
> - A muzzle/snout head that doesn't share human topology **needs its own
>   `performance/morph.dat` authoring the action units on the new mesh, matched by
>   name**, or the face is frozen in dialogue and won't lip-sync.
> - **Animated ears/appendages via expression** (e.g. "sad → droopy ears") work the
>   same way, keyed to *action units* rather than named emotions — droop on
>   `innerBrowRaise` + `lipCornerDepress` (sad), pin back on `browLowerer` (angry),
>   perk on `outerBrowRaise`/`cheekRaise` (happy). Key them to the **emotional**
>   AUs (brow/cheek), not the speech AUs (`jawOpen`/`lipPucker`/funnelers double as
>   visemes and would twitch the ears during dialogue).
> - **Eyewear is nearly absent in vanilla** — a full ARMO scan finds only **1 eyepatch**
>   (slot 26) and **10 Neuroamps** (slot 18, temple/ear-mounted AR devices); no glasses/
>   goggles exist as face apparel (eye tech lives in helmet visors). So a muzzle race has
>   almost no human-eye-spaced eyewear to conflict with. The one fit to watch is the
>   **Neuroamp** vs. animal **ears** (slot 18 sits at the temple/ear), not the eyes.
> - The head's performance morphs include a **`HideEar`** key — the morph that
>   **collapses the ear region when a helmet is equipped** (apparel on biped slot
>   19, *Hide Ear*, drives it). A furry head with integrated ears/horns just
>   authors its own `HideEar` delta that tucks them away; because a race is a
>   HumanRace clone, vanilla helmets drive it automatically. This is HideEar working
>   **as designed** (helmet fit) — not a repurposing.

### Named facial expressions (`FXPD`) — dialogue-driven bundles of action units

The raw performance morphs above are the *primitives*; the engine composes named,
higher-level expressions from them via the **`FXPD` "Facial Expression"** record —
a flat, weighted bundle:

```
FXPD: EDID + FULL(display name) + Morphs[] { MNAM = morph name, MWGT = weight 0..1 }
```

`Starfield.esm` ships ~**31** of these (`facialExpression_Afraid`, `_Angry`, `_Happy`,
`_Depressed`, `_Disgust`, `_Flirt`, `_Pain`, `_Rage`, `_Shocked`, `_Smug`, `_Yawn`, …),
each listing 2–42 of the **same action-unit names as the performance `morph.dat`**.
For example `facialExpression_Afraid` = `browLowererL 0.638`, `innerBrowRaiseR 0.853`,
`eyeOpenL/R 1.0`, `jawOpen 0.155`, `lipCornerDepressL/R ≈0.3`, `nostrilDilator 0.621`,
`neckFlexL/R`, … So an expression is just *"set these AUs to these weights."* This is the
moddable successor to Skyrim/FO4's engine-internal `Mood<Emotion>` expression morph — see
[Morphs & Shape Keys → How dialogue drives these morphs](../../file-formats/morphs-shapekeys.md) for the `.tri`
ancestry and the 8-emotion enum it replaced.

**How they're triggered (and what is *not* a link).** No plugin record references an
`FXPD` by FormID — DIAL, INFO, and SCEN have **no `FXPD` field**, and a full dump of
those groups contains no reference to a `facialExpression_*` FormID. What dialogue and
scenes *do* reference is the **"Anim (Face) Archetype" keyword** — a `KYWD` named
`AnimFaceArchetype*`, carried in a reusable *Animation* struct (`INFO` responses, scene
phases, packages) via its `FLMV` "Anim Face Archetype" field. Those archetype keywords
**name-parallel the `FXPD` set** (`AnimFaceArchetypeAngry` ↔ `facialExpression_Angry`,
`…Afraid` ↔ `…Afraid`, `…Shocked`, `…Depressed`, `…Disgust`, `…Smirk`, …), but only by
name: their FormIDs are unrelated (`KYWD AnimFaceArchetypeAngry [000FA84A]`,
`FXPD facialExpression_Angry [0020D3A2]`). So the trigger path is **dialogue/scene →
`AnimFaceArchetype` keyword → (in-house animation/behavior layer) → the matching `FXPD`
morph bundle** — the keyword↔`FXPD` binding is by **name/convention in the anim system,
not an editable plugin reference**. (`INFO` responses additionally carry a per-line
*Emotion* keyword + value in `TRDA`.)

> **Tested in game (2026-10-08): the runtime reads `FXPD`, but only for the action units
> it already knows.** Raising `jawOpen` to 1.0 in an override of `facialExpression_Angry`
> opened the jaw whenever Angry was applied in photo mode. Two morph names added to the
> same record (`CanineEarBackL`/`R`, defined with real deltas in the head's performance
> `morph.dat`) did nothing: not in photo mode, not in the CK's character-window
> expression preview, not on a re-baked NPC. Morphs are matched by name, not by their
> position in `morph.dat`; the head tested had its keys in a different order from vanilla
> and every vanilla action unit still worked. Tested through photo mode and the CK, not
> through a dialogue line.

> **Furry-race implications.**
> - Because an `FXPD` references morphs **by name**, and every face part only responds
>   to the AU keys *its own* `performance/morph.dat` defines, a muzzle head that authors
>   the vanilla AU names (`browLowererL`, `jawOpen`, `innerBrowRaise`, …) is driven by the
>   **vanilla dialogue expressions automatically** — no behavior-graph authoring, no
>   record edits. This is the cheapest path to dialogue-driven emotion on a non-human head.
> - **`FXPD` records are global, not per-race.** There is no race field and dialogue picks
>   the expression, not the actor's race — so you *cannot* give an anthro wolf a different
>   `_Angry` mix from a human by adding a race-specific expression alone.
> - **New action units don't work.** Adding species morphs (ear-back, ear-droop) to the
>   head's `performance/morph.dat` and naming them in the global `FXPD` records does
>   nothing: the engine ignores action-unit names outside its own set (tested above).
> - **Fold species motion into vanilla action units instead** (follows from the test; not
>   itself tested yet). Add the ear-back deltas into the head's own `browLowererL`/`R`,
>   which `facialExpression_Angry` weights at 0.84, and the ears move wherever those brows
>   do: every expression and dialogue animation that uses them, with no record edits. The
>   trade-off is that the ears follow that action unit everywhere, not just in one
>   expression.

### The morph-delta file (`.morph` / `morph.dat`)
Stored under `Data/meshes/morphs/…/morph.dat` — always named `morph.dat`. Only the folder
path varies and is stored in the plugin file (e.g.
`meshes/morphs/human/female/chargen/body/morph.dat`); **not** hash-named like `.mesh`
files. Binary layout **verified** against Outfit Studio's `SFMorphFile` (little-endian):

```
char   magic[4] = "MDAT"
uint32 numAxis            // always 3
uint32 numVertices
uint32 numShapeKeys
  per shape key:  uint32 nameLen + name bytes (no null terminator)
uint32 numMorphData
uint32 numOffsets         // == numVertices
morphData[numMorphData]   // 16 bytes each:
    uint16 offset[3]      //   position delta, half-float, in metric (.mesh) units;
                          //     × havokScale (69.969) → game units, as with .mesh positions
    uint16 targetVertColor//   target vertex colour, RGB565 (5:6:5). Default gray 0xBDF7 (~0.74)
    uint32 normal         //   delta normal,  DEC3N signed (axis = (n>>k & 1023)/511.5 − 1.0)
    uint32 tangent        //   delta tangent, DEC3N signed
offsets[numOffsets]       // 20 bytes each — sparse per-vertex:
    uint32 dataStart      //   start index into morphData
    uint32 keyMarker[4]   //   128-bit bitfield → which shape keys touch this vertex (max 128 keys)
```

So a morph is **dense over vertices** (one `offsets` entry each, `numOffsets ==
numVertices`) but **sparse over keys**: a vertex stores a run of deltas only for the shape
keys whose bit is set in its `keyMarker`, and the set bits (ascending) map 1:1 to that
vertex's consecutive `morphData` records. Position deltas share the `.mesh`'s `havokScale`
factor.

> **Corrections (verified byte-exact against vanilla + the SGB `MorphIO.cpp` source,
> 2026-07-14):** the normal/tangent are **DEC3N signed** (earlier notes said UDEC3), and
> the position half-float is stored **metric** and multiplied — not divided — by
> `havokScale` to reach game units. A round-trip reader/writer reproduces a vanilla
> `morph.dat` byte-for-byte with this layout.

**`targetVertColor` is an RGB565 per-vertex colour**, **constant per vertex across all of
that vertex's morph keys** (verified: for `chargen/coily_mohawk_f`, 0 of 10,011 multi-key
vertices differ across keys; same for the head). SF vertex colour drives **material
masks** (hair/clothing use R/G/B channels — `HairSettingsComponent.AOVertexColorChannel` /
`DepthOffsetMaskVertexColorChannel`; `AlphaBlenderSettings.VertexColorChannel`; chromatic
values like magenta `(1,0,1)`; faces use a near-gray baked AO `0xBDF7`). It's a constant
on most morphs — of 1194 vanilla `morph.dat`, only 49 carry a non-constant colour. It
**correlates with the mesh's own vertex colour** but is not byte-equal (on the hair sample
R/B match, G differs); the exact relationship is **unresolved**.

Because it's one value per vertex (not per morph), it maps to a Blender **colour
attribute**: PyNifly import writes the per-vertex colours there, export RGB565-encodes
them back (gray default if absent) — so a morph round-trips from mesh + shape keys + one
colour attribute, no per-morph colour authoring. (Whether the engine reads these colours
at all is unconfirmed.) Note that the `.mesh` file does carry vertex colors and they are
used.

**Starfield Geometry Bridge** to Blender workflow (as of 09-2026):
- Import the `.mesh` first, then import the `.morph` onto the active mesh.
- Model needs a **`Basis`** shape key (base look) plus shape keys named to match
  the morph keys; **all shape-key values range 0.0–1.0**, relative to Basis. The
  engine does **not** allow "oversliding" past 1.0.
- Custom chargen sliders are wired up with a **JSON config** whose `"Key"` must
  match the morph name in the `.morph` file, exposed in the creator via the
  **CharGenMenu** mod (there is no vanilla UI hook to add brand-new sliders).

Reference implementations: Outfit Studio `SFMorphFile.{h,cpp}` (reads **and** writes) and
StarfieldMeshConverter's `MorphIO`. Both are self-contained (~250 lines) with no NIF-library
dependency beyond half-float + DEC3N helpers.

**PyNifly** to Blender workflow:
- Import the nif; it will bring the mesh with it even if the mesh is external.
- Import the `.morph` on the active mesh separately; there's no link between nif and mesh.
- Any morphs not part of the above "performance" set will be exported to the chagen morph file.

### Two ways to change face shape — bone morphs vs. vertex morphs

Starfield has **two independent systems** that both reshape a face, with very
different costs. 

| | Bone morphs | Vertex morphs |
|---|---|---|
| Enabled in | `<RaceEDID>FacialBoneRegions<Sex>.txt` (JSON) | `chargen/…/morph.dat` |
| Wired by | file naming convention off the race EDID | `MRPH` `TCMP` + race `MPGN`/`MPGM` |
| Selected per NPC by | the **Face Morphs** array (`FMRI` region + `FMRG` group + `FMRS`) and the **Face Dial Positions** array (`FMSI` + signed `FMRS`) — see below | the **Morph Groups** array (`BMPN` "Blend Name" + `BMPV` "Intensity") |
| Can express | translate / rotate / scale of existing face bones | arbitrary per-vertex displacement |
| **Propagates to attached parts** | **yes, automatically** — anything skinned to `faceBone_*` follows | **no** — each part must re-author the same named keys |

The propagation difference is the big one. A vertex morph only deforms the mesh it was
authored for, so every eyebrow, beard, hair, teeth and eyelash mesh needs its own
`morph.dat` carrying **the same key names** — the identical tax the performance/expression
AUs pay (see above). A bone morph moves the skeleton, so every part weighted to those
bones follows for free, including headgear, *as long as the bone weights match*.

The tradeoff is expressive range: bones can only move, rotate and scale what is already in
the rig. Skull proportions, muzzle length, ear size and set are well within reach; fine
surface detail that has no bone under it is not.

**What shipped custom races actually do** (as of 09-2026): The published Felid race puts
its per-species head shapes in the **chargen `morph.dat`** — its head chargen morph
carries 29 keys including `Tiger_Cheeks`, `Jaguar_Jaw`, `SnowLeopard_Nose`,
`PointedEars_Ears`, matching the race's `MPGM` morph-group members one-for-one, and NPCs
select them via `BMPN`/`BMPV`. Its `FacialBoneRegions` files are a renamed copy of the
vanilla human ones, phenotype names and all. The cost shows up exactly where the table
predicts: its eyebrow chargen morph re-authors seven of the same keys (`Tiger_Forehead`,
`Jaguar_Forehead`, `SnowLeopard_Nose`, …) so brows track the species head shape.

Putting per-species shapes in the **bone region file instead**, as additional
`SculptRegion: false` phenotype regions with matching race `FMRU` entries, gets
that propagation for free — at the price of being limited to bone transforms.
For a race whose sub-species differ mainly in skull proportion this is the
cheaper architecture; for one that needs genuinely different surface topology it
is not sufficient on its own. The two systems compose, so a hybrid (bones for
proportion, a few vertex morphs for detail) is available.

See the Creation Kit page, §8, for the FacialBoneRegions file schema, locations
and the vanilla sculpt-region/slider inventory.

### How an NPC stores its face — three arrays, two systems

An `NPC_` record carries **three** separate face arrays. They look redundant —
two of them hold what appears to be the same phenotype-and-region weighting —
but they feed the two systems above, which have to be driven independently.

| NPC array | Fields | Drives |
|---|---|---|
| **Face Morphs** | `FMRI` region ID + `FMRG` group + `FMRS` weight (0…1) | **bones** — apply one phenotype region's slider, restricted to one face group |
| **Face Dial Positions** | `FMSI` slider ID + `FMRS` position (**signed**, −1…+1) | **bones** — one individual sculpt slider |
| **Morph Groups** | `BMPN` key + `BMPV` weight | **vertices** — one key in the chargen `morph.dat` |

**Face Morphs → bone morphs.** `FMRI` is the `ID` of a `SculptRegion: false`
region in `FacialBoneRegions<Sex>.txt`. That region holds a single `ZeroToOne`
slider driving **all 48 face bones** at once — a whole base face. `FMRG` then
names one of the **nine columns of the `…Mapping.csv`** (`Cheeks`, `Chin`,
`Ears`, `Eyes`, `Forehead`, `Jaw`, `Mouth`, `Neck`, `Nose`), which is a **per-bone
mask**: the CSV says how much each bone belongs to that group, 0–100. So one
entry reads *"apply phenotype `male_as_md1` at 0.24, but only to the bones the
Cheeks column selects."* That is how a single 48-bone slider becomes nine
independently blendable regions.

**Face Dial Positions → the sculpt sliders.** `FMSI` indexes a **slider inside**
a `SculptRegion: true` region, not the region itself — the Mouth region (ID 22)
owns sliders 24, 25, 76, 77 — which is why dial indices fall in the gaps between
region IDs. Values are signed because these sliders are bipolar
(`ZeroToOne: false`): `'down - up'`, `'narrow - wide'`, `'underbite - overbite'`.

**Morph Groups → vertex morphs.** `BMPN` is a literal key in the chargen
`morph.dat`. For a phenotype-grid morph the key is the composed
`<phenotype>_<region>` name, which is exactly what Face Morphs expresses as a
pair — hence the apparent duplication. But the array is not limited to the grid:
it is also where body-build keys (`Overweight`, `Thin`, `Strong`) and a custom
race's species morphs live, since those exist only as vertex data.

#### What the vanilla data shows

Measured over all **7,131 `NPC_` records in `Starfield.esm`**, resolving `FMRI`
through `HumanRace`'s region table and composing `<phenotype>_<FMRG>`:

| | |
|---|---|
| carry both Face Morphs and Morph Groups | 2,982 |
| carry Morph Groups only | 140 |
| **carry Face Morphs only** | **0** |
| composed key in both, identical value | 38,241 |
| composed key in both, differing value | 25,501 |
| key only in Face Morphs (bone-only shaping) | 6,595 |
| key only in Morph Groups (no bone equivalent) | 10,931 |

Two things follow. The 38,241 exact value matches confirm the composition rule
`BMPN == <phenotype>_<FMRG>` — the two arrays really are addressing the same
conceptual blend. But they are **not** copies of each other: the values diverge
on 25,501 entries in both directions, and each array carries thousands of keys
the other lacks. The creator writes both from one slider, then the two systems
are tuned separately.

**Face Morphs never appears without Morph Groups**, in any vanilla NPC. Vertex
morphs stand alone; bone morphs are always accompanied. A custom race can
therefore ship vertex morphs with no rig work at all — which is what the
published felid race does — but should not expect the reverse to be a
well-trodden path.

---

## 4. Tints, complexions & overlays — the AVM system (`AVMD`/`AVMS`)

Starfield replaced the fixed `[Skyrim]` tint-mask layers with a generalized **Additive
Visual Material (AVM)** system. Individual races have no tint layer list -- there's one
for all races.

### 4.1 Per-NPC tint application (`NPC_` → "AVMD Tints")
**Tints are applied on the `NPC_` record** — Each NPC carries an `EDCT` **Tint Count**
plus an **AVMD Tints** array; each entry is one applied layer:

| Field | Meaning |
|---|---|
| `MNAM` | the **group type** — `Simple Group` / `Complex Group` / `Modulation`. |
| `TNAM` Tint Group | the **slot** — one of the layer names in §4.3 (`Dermaesthetic`, `Accents1`, `Lipstick2`…). Combines with `MNAM` to give the `EDID` of the target group. |
| `QNAM` Tint Name | which option within the group |
| `VNAM` Tint Texture | the texture file path |
| `NNAM` Tint Color | RGBA color |
| `INTV` Intensity | 1–128 |

**The entry is self-contained.** It carries the texture path, the color and the intensity,
so nothing at runtime has to resolve the group in order to find the asset. Composited over
the face material at runtime or during facegen. The NPC also names its per-slot colors
directly as strings (`HCOL` hair, `FHCL` facial hair, `BCOL` eyebrow, `ECOL` eye, `JCOL`
jewelry).

**The FaceGen bake uses the stored `VNAM` literally** — it never re-resolves the option
through its group. 

- Measured: **577 of 20,751** vanilla NPC tint entries (in `ComplexionMask1`/`2`,
`Dermaesthetic` and `TattooMask`) store a path that exists in no archive, because the
texture was renamed or moved after the NPC was authored (`moles_many_small_02.dds` →
`…_mask.dds`, `…_derm.dds` → `…_derm_color.dds`,
`faces\makeup\tattoo_makeup_geometric_mask.dds` →
`faces\chargen\postblenddetails\tattootint\…`). Their `QNAM` option resolves through the
group to a real file but it is *not* used. `TattooMask` is the control, since a tattoo is
unmistakable in a baked `_color`: of the 7 vanilla NPCs carrying one, 5 store a valid path
and 2 a stale one. The valid tattoos checked (skull, eagle, skull, leaf) are in the baked
texture; both stale ones — Valerie Mosquera and the `City_AC_FABQ10_Visitor` — are
**absent**. A stale `VNAM` silently drops the layer, and Bethesda ships hundreds of them.
- Also: `NNAM` `(0,0,0,0)` is not invisible — those skulls bake black.

For an author this means renaming or moving a tint texture breaks every NPC already
authored against it, and fixing the group does not repair them; the records have to be
re-saved.

**Colour or opacity — the slots split cleanly.** Measured over every vanilla NPC
carrying tints: `Dermaesthetic` (2,949 NPCs) and `Complexion1`/`Complexion2` (2,432 /
1,279) **always** carry `NNAM` = `(0,0,0,0)` and vary only by `INTV`, so they are pure
texture overlays differing in opacity alone. `ComplexionMask1`/`ComplexionMask2` (2,661 /
2,290) are the layers that actually shift **hue**, carrying **34 distinct RGBA** values
backed by their paired 29-entry `Modulation` group. Across every tint slot in
`Starfield.esm`, only **142 distinct RGBA** values appear — authored from a working
palette, even though the field is free-form.

**One layer per slot.** Across 3,800 NPCs in `Starfield.esm`, `ShatteredSpace.esm`
and the `SFBGS` plugins, **no NPC ever lists the same `TNAM` twice** — and neither
does the shipped Felid race across its 92 tinted NPCs. A slot is single-occupancy.
The most any vanilla NPC carries is 16 layers; the median is 7–8.

Two consequences for anyone authoring a race. To show several marks at once you
either **bake them into one option** — `Burn_AlloverLight` and
`Burn_LeftCheekManySmall` are pre-composited multi-scar textures — or **spend one
slot per mark**. The number of concurrent overlays is capped by the slot list,
not by anything per-NPC.

### 4.2 The `AVMD` record

`AVMD` ("AVMS Data") records define the tint/complexion **groups and options**
themselves. `Starfield.esm` holds **6,154** of them — 2,399 Simple, 2,029 Complex,
1,726 Modulation.

| Field | Meaning |
|---|---|
| `EDID` | e.g. `SimpleGroup_Dermaesthetic`, `Modulation_ComplexionMask1` |
| `MNAM` | group type: `None` / `Simple Group` / `Complex Group` / `Modulation` |
| `YNAM` | the group's name |
| `TNAM` | the group's identifier — this is the lookup key used in other records |
| `ITMC` | entry count |
| entries | `LNAM` option name, plus `VNAM` (texture or typed reference) and/or `NNAM` (color) |
| `MODT` | texture-type flags — Rough / Opacity / Normal / AO / Metal / Biome Conditions / Emissive. Not always present; when present not always correct. Left blank for aldebo. |
| `AVMP` | optional parent `AVMD` |

**Everything in this system resolves by NAME, never by FormID.** Nothing holds an `AVMD`'s
FormID — not the RACE, not the NPC, not another `AVMD`. Records are found by combining the
group type with the `TNAM` name ID, and possibly other elements. So
`SimpleGroup_ColorlessAccents1_Color`, `SimpleGroup_ColorlessAccents1_ao`,
`SimpleGroup_Chargen_ColorlessAccents1` are all found by building the editor ID from the
parts. Similarly `Modulation_Lipstick1` is associated with `SimpleGroup_Lipstick1` only by
editor ID. 

**Three AVM group kinds:**

| Kind | Entry = | Used for |
|---|---|---|
| **Simple Group** (type 1) | `LNAM` name + `VNAM` **texture path** | a texture option (skin tone, eye/teeth/hair texture, a face overlay) |
| **Complex Group** (type 2) | `LNAM` name + reference to another `AVMD` | bundles channels, or exposes a group for a head part's **color mapping** |
| **Modulation** (type 3) | `LNAM` name + `NNAM` **color** | a solid color option for another group such as lipstick, tattoo ink, or jewelry |

A **Complex Group entry references another `AVMD` two ways**, and the bare form
dominates about 50:1:

- **bare `LNAM`** (5,728 uses) — the name alone. Presumably tried against the Simple,
  Complex, and Modulation groups until a hit is found.
- **`VNAM` = `<Prefix>_<Name>`** (114 uses) — `SimpleGroup_` / `ComplexGroup_` /
  `Modulation_` reference includes the group type explicitly. Used even when more than one
  group is found and will be used. (E.g. `ComplexGroup_PostBlendFaceCustomizationLayers`
  references `Modulation_ComplexionMask1` but will access `SimpleGroup_ComplexionMask1` as
  well.)

⚠️ The two forms are not interchangeable in a given record — where a Complex Group
uses `VNAM`, the `LNAM` beside it is only a **label**. `ComplexGroup_FaceSkinTones`
has `LNAM 'male_af_md1'` with `VNAM 'SimpleGroup_FaceSkinTones_male_af_md1'`, and a
bare `male_af_md1` matches no record at all.

**Modulation groups are reached almost exclusively from Complex Groups** — 1,684 of
the 1,726 are referenced that way (mostly the creature/biome color sets). **No NPC
ever names a Modulation group directly**: of all vanilla NPC tint entries, 20,751
name a Simple Group, 4,298 a Complex Group, and zero a Modulation. The remaining 34
are reached by name-pairing (§4.4).

Face overlays (complexion, dermaesthetic, scars, tattoos, lipstick, eyeshadow,
cheeks, accents…) are Simple Groups whose textures live under
`textures/actors/human/faces/chargen/postblenddetails/<category>/` and apply **only
to the "Face" head part**. 

#### The groups a custom race usually has to touch

**These groups are global — nothing scopes an `AVMD` to a race.** There is no race
field naming them (a RACE names only `BSTT`/`HSTT`/`FSTT` and `FCTP`), and lookups go
through the one game-wide name index. A race reaches them only **through its head
parts**, one part at a time, so a custom race mixes vanilla and its own freely.

Beyond the face overlays, six vanilla groups cover hair, eyes, brows and teeth. All
six verified against `Starfield.esm`:

| Group | FormID | Kind | Options | Holds |
|---|---|---|---|---|
| `HairColor` | `000ECD2E` | Complex | 8 | the hair colour palettes |
| `FacialHairColor` | `000ECD30` | Complex | 1 | beard colour |
| `EyebrowColor` | `000ECD2D` | Complex | 12 | brow colour |
| `EyebrowOpacity` | `0000EF9F` | Simple | 16 | brow opacity — **a part with no entry renders transparent** |
| `EyeColor` | `000377DC` | Simple | 12 | iris textures |
| `TeethCustomization` | `0006160A` | Simple | 4 | teeth textures |

**How they're reached differs by feature, and only hair and brows involve the head
part at all.** Eye and teeth parts carry no `NAM2`/`NAM3` — `Human_Female_LeftEye` has
neither — because those groups are flat lists the NPC indexes by name directly:

| Feature | Group | Shape | Branch chosen by | Option chosen by |
|---|---|---|---|---|
| eyes | `EyeColor` | Simple, 12 options (`Hazel`, `Iron`, …) | Hardwired lookup in `SimpleGroup_EyeColor` | NPC `ECOL` |
| teeth | `TeethCustomization` | Simple, 4 options (`Teeth_Clean`, …) | Hardwired lookup in `SimpleGroup_TeethCustomization` | NPC `TETC` |
| hair | `HairColor` | Complex, 8 entries — one per hair **type** | Simple group identified by head part's `NAM2` (e.g. `Hair_Short`) | NPC `HCOL` |
| beards | `FacialHairColor` | Complex, 1 entry | head part `NAM2` (`FacialHair_Shared`) | NPC `FHCL` |
| brows | `EyebrowColor` | Complex, 12 entries — one per brow **type** | head part `NAM2` (`Eyebrows_StandardMale`) | NPC `BCOL` |

So the Complex colour groups are **indexed by the part's `NAM2` value**: the part says
which kind of hair or brow it is, that picks the branch, and the NPC's colour string
picks an option inside it. `NAM3` names the colour group itself on the 25 brow parts
(`EyebrowColor`), and on 109 hair parts it instead names a scalp-mask *option*
(`FadedAfro_Cap_Mask`) inside `HairFollicleMask` — the field does double duty.
Vanilla writes the literal `' NONE'` (with a leading space) where a part has no value.
As everywhere in this system, all of these are name lookups — nothing holds a FormID.

**The shipped Felid race shows the mixing in practice.** Of its 22 head parts carrying
these fields, `NAM2` names a vanilla branch 17 times (`Hair_Short`, `Hair_Afro`,
`Eyebrows_Apart`, `FacialHair_Shared`) and its own `Eyebrows_Hair_Short` the other 5 —
which is why it also ships an `AVMP` child extending `EyebrowColor`, since a new brow
type needs a branch in the colour group to match. Every brow part names vanilla
`EyebrowColor` in `NAM3`; its hair and beards carry `' NONE'`.

So a race needs its own group only where its artwork demands one, and `AVMP` (see
above) is how a new branch or option joins a vanilla group instead of replacing it.

Skin tones work differently again: the race names its groups in `BSTT`/`HSTT`/`FSTT`
and indexes them positionally with `STON`, so the option *names* there carry no
meaning. That whole mechanism is §4.5.

**Adding options in bulk.** Either edit the groups directly in xEdit, or generate them
with the config-driven **RTFP** patcher (`[AVMData]` / `[FormList]` `add_entr`
directives, `minver=115`), which is how the CharGen Resources resource ships its
additions.

#### `AVMP` — add options to a vanilla group without overriding it

`AVMP` ("AVMS Parent", per SF1Edit: `wbFormIDCk(AVMP, 'AVMS Parent', [AVMD])`) is the
one place this system uses a FormID. A child `AVMD` names a parent `AVMD`, and the
child's options are **added to the parent's set** — the parent record is never
touched, so two mods can extend the same slot without conflicting. It is the
conflict-free alternative to overriding a vanilla group.

Measured across the official plugins and the shipped Felid race:

- **The base game never uses it: 0 of 6,154 `AVMD`s.** Only `ShatteredSpace.esm` (3)
  and Felid (5). (Raw `AVMP` byte matches inside `Starfield.esm` are false positives
  in compressed record data — count subrecords, not bytes.)
- Always **exactly one `AVMP` per record, and always the last subrecord**.
- Bethesda's own naming convention is **`<ParentTNAM>_AVMDEXT`**; Felid copies it.
- In all 8 real cases the child and parent share **zero option names** — children add,
  never replace — and are always the **same kind** (Simple extends Simple, Complex
  extends Complex).
- **Extend both the chargen-side and the runtime-side group.** ShatteredSpace extends
  `Chargen_TattooMask` *and* `TattooMask`; Felid extends `Chargen_Lipstick2` *and*
  `Lipstick2`.

| child | parent | adds |
|---|---|---|
| `Chargen_TattooMask_AVMDEXT` (ShatteredSpace) | `Chargen_TattooMask` `[00097579]` | 13 DLC tattoo masks |
| `HairFollicleMask_AVMDEXT` (ShatteredSpace) | `HairFollicleMask` `[000A2711]` | 3 scalp masks |
| `SimpleGroup_Lipstick2_Felid_AVMDEXT` | `Lipstick2` `[00393D6F]` | 12 face patterns |
| `ComplexGroup_EyebrowColor_Felid_AVMDEXT` | `EyebrowColor` `[000ECD2D]` | 1 eyebrow group |

This is the mechanism behind §4.9's "new records under new names": a distinct `TNAM`
keeps the child out of the vanilla name index, and `AVMP` is what still delivers its
options into the vanilla slot.

⚠️ `AVMP` can only **add**. A race that wants its own options *instead of* vanilla's
has to change the group the creator reads from — see §4.11.

### 4.3 The layer stack — `ComplexGroup_PostBlendFaceCustomizationLayers`

The set of slots lives in **one record**:
`ComplexGroup_PostBlendFaceCustomizationLayers` (`AVMD:00393D76`). Its 26 entries, in
record order, **describe** the compositing stack bottom to top — but editing them does
not change it, which is the subject of the experiment below:

```
 1 Dermaesthetic          10 ColorlessAccents2      19 Lipstick1
 2 ComplexionMask1        11 TattooColorMap *       20 Lipstick2
 3 Complexion1            12 TattooTint *           21 Eyeshadow1
 4 Complexion2            13 TattooMask             22 Eyeshadow2
 5 ComplexionMask2        14 MakeupFullPaintMask *  23 Eyeliner1
 6 Scars                  15 MakeupFullPaintMask1   24 Eyeliner2
 7 Accents1               16 MakeupFullPaintMask2   25 EnvironmentColor *
 8 Accents2               17 Cheeks1                26 EnvironmentMask
 9 ColorlessAccents1      18 Cheeks2                (* = broken, see below)
```

Read as paint layers: skin detail → complexion → scars → accents → tattoos →
makeup → blush → lips → eyeshadow → eyeliner → environmental grime last.

**An NPC's tint array is this list filtered to the layers in use.** Verified over
3,020 NPCs carrying tints: **zero pairs ever appear in conflicting order**, and a
topological sort of the observed orderings reproduces the record's order exactly,
including the six pairs that never co-occur in any NPC.

**How the record is found: by hard-coded name.** It has no `AVMP` parent, no record
anywhere holds its FormID, and no RACE mentions it. The string
`PostBlendFaceCustomizationLayers` appears once in each of `Starfield.exe` and
`CreationKit.exe`, in a cluster with other well-known group names (`HairTypes`) and
the blend-mode literals. So the engine carries a short list of group names it looks
up directly, and this is one of them.

#### ⚠️ Skin layer order is built in

The record *documents* the order; it does not *define* it. **Neither reordering this
record nor reordering an NPC's own tint array changes what composites on top.**

The experiment, on `CF_NaevaMora [00009138]`, who ships with both a scar and an
accent. Two vanilla textures were replaced with full-face opaque colours —
`scar_nosegouges_color.dds` → red, `accents_undereyebagssmall_color.dds` → blue —
and both layers set to the same intensity, so whichever composites last wins the
whole face. The result was read out of the baked
`facecustomization\Starfield.esm\00009138_Color.dds`, not judged by eye:

| Test | Change | Baked face |
|---|---|---|
| 1 | vanilla order; scar only | **red** (control — the layer works) |
| 2 | vanilla order; scar + accent | **blue** — `Accents1` is above `Scars` |
| 3 | NPC's stored tint array reversed (`Accents1` before `Scars`) | **blue**, unchanged |
| 4 | **this record** reordered — `Accents1` moved below `Scars` | **blue**, unchanged |

Test 4's bake measured **99.8% pure blue, 0.1% red**. The Creation Kit was restarted
between the edit and the bake, so this is not the CK serving a cached load order.
Test 3 also showed the CK's post-blend list displaying its own canonical order rather
than the array's stored order — the same fixed sequence showing through in the editor
UI.

Two useful corollaries: **a mod cannot re-layer the face**, and the order vanilla
data appears in is reliable *documentation* of the built-in sequence, since the
built-in order and the record agree everywhere the data can show it (§4.3's
topological check over 3,020 NPCs).

For a custom race this is a hard constraint, not an inconvenience: a species marking that
must sit **under** a scar has only the three slots below it available in the game UI —
`Dermaesthetic`, `Complexion1`, `Complexion2` — and everything else will layer over scars
like makeup, whatever the marking actually represents.

**Not tested:** the live player composite (the bake is the Creation Kit's), and
whether *deleting* a slot from this record disables it — a removal would test the
claim more sharply than a reorder does.

⚠️ **The stack is global, not per-race.** There is no race-level field pointing at a
layer list — contrast the skin tones, which the race *does* nominate via
`BSTT`/`HSTT`/`FSTT`. Every race draws on this one record, and a custom race gets no
variant of its own. No vanilla DLC overrides it, and neither does the shipped Felid
race — which, given the test above, would have gained them nothing.

**Four of the 26 entries are broken, and the game ships that way:**

| Slot | `VNAM` target | Status |
|---|---|---|
| `TattooColorMap` | `SimpleGroup_TattooColorMap` | no record of that name, under any type |
| `TattooTint` | `SimpleGroup_TattooTint` | no record of that name |
| `MakeupFullPaintMask` | `SimpleGroup_MakeupFullPaintMask` | no record — though `…Mask1`/`…Mask2` both exist |
| `EnvironmentColor` | `SimpleGroup_EnvironmentColor` | resolves, but has **zero entries** |

Checked against every `AVMD` in the base game plus `ShatteredSpace` and the `SFBGS`
plugins. These are the same four slots **no NPC ever uses**, and `TattooColorMap` /
`TattooTint` are also the only slot names **absent from both executables** — the
signature of a cut feature whose code went away while the data entry stayed. The
practical lesson: **an unresolvable entry is skipped, not fatal.**

### 4.4 Slot name-pairing 

The `VNAM` in the layer record is **not** the only route to a slot's content. **15 of the
26 slots have a same-named `AVMD` of another type that the stack never references
directly**, found by the name alone:

| Stack names | Slot also exists as | Slots |
|---|---|---|
| Modulation | Simple | `ComplexionMask1/2`, `TattooMask`, `MakeupFullPaintMask1/2` |
| Simple | Modulation | `Cheeks1/2`, `Lipstick1/2`, `Eyeshadow1/2`, `Eyeliner1/2`, `EnvironmentMask` |

Which half the stack names looks like authoring accident — both resolve, and the engine
finds the other by name regardless. The division of labour is consistent: **the Simple
group supplies the mask textures, the same-named Modulation group supplies the legal
colors.**

Tattoos are the clearest worked example. The stack names `Modulation_TattooMask` (9 colors
— Black, Brown, Red, Pink, Blue, Teal), while the designs live in `SimpleGroup_TattooMask`
(13 — Dagger, Leaf, Cat, Circuits01, Dragon), which nothing references. All 7 NPCs using
the slot address it as `Simple`.

Evidence that the pairing is real: of 14,091 NPC tints in a slot that has a
same-named Modulation group, **75.5% carry a color that appears in that group's
palette** (misses are dominated by "no color set", `00000000`).

⚠️ **A paired Modulation group cannot be pointed at — only *be*.** Extending a
slot's color options therefore requires **overriding the vanilla Modulation
record**; extending its textures does not. This is exactly what the Felid race does
(§4.7).

#### What feeds each slot

The 26 slots have 5 different semantics. Counts are vanilla option counts, measured per
group kind:

| Fed by | Slots | Shape |
|---|---|---|
| **Full-colour texture** | `Dermaesthetic` (84), `Complexion1` (13), `Complexion2` (13) | a Simple group of `*_color.dds`; the texture's own alpha is the strength |
| **Mask + palette** | `ComplexionMask1`/`2` (46 masks, 29 colors), `TattooMask` (13, 9), `MakeupFullPaintMask1`/`2` (21, 22), `Cheeks1`/`2` (3, 40), `Lipstick1`/`2` (5-6, 40), `Eyeshadow1`/`2` (6, 40), `Eyeliner1`/`2` (9, 40), `EnvironmentMask` (7, 5) | Simple group of greyscale `*_mask.dds` + same-named Modulation palette (§4.4) |
| **Four coordinated channels** | `Scars`, `Accents1`/`2` | a Complex group of 4 entries fanning out to `_color` / `_normal` / `_rough` / `_ao` Simple groups |
| **Four coordinated channels, monochrome** | `ColorlessAccents1`/`2` | same as above *but* only the alpha channel of the "color" texture is used. |
| **Nothing** | `TattooColorMap`, `TattooTint`, `MakeupFullPaintMask`, `EnvironmentColor` | the four broken slots (§4.3) |

Only the first three slots in the stack — `Dermaesthetic`, `Complexion1`, `Complexion2` —
paint *below* `Scars`. Everything above is conceived as makeup, paint or grime that layes
over the natural skin. **That is the constraint for a furry race:** fur markings that
should sit under a scar have just those three slots, one of which (`Complexion1`/`2`)
ships as colour-temperature washes. Markings placed in `Cheeks` or `Lipstick` will layer
over scars as though they were blush.

The game UI labels differ from the record names: `Complexion1` appears as *"Complexion
Color Temp"* and `ComplexionMask2` as *"Complexion Blemishes"*.

### 4.5 Skin tones and `STON`

`STON` (NPC "Skin Tone Index") is a **positional index into the entry list** of the
skin-tone Simple Group the race nominates. One value resolves three times:

```
NPC.STON = 3
  RACE.BSTT "Male_Naked_Body_Skin_Tones" (Simple)  -> entry[3] = NakedBodyM_sk3_color
  RACE.HSTT "Male_Hands"                 (Simple)  -> entry[3] = DefaultHandsM_sk3_color
  RACE.FSTT "FaceSkinTones"              (Complex) -> per-phenotype Simple
                                                   -> entry[3] = male_af_md1_sk3_color
```

One index keeps body, hands and face on the same tone — which is what makes the
neck seam match. The face path is two levels: `FSTT` names a **Complex** Group whose
22 entries are the phenotype names, resolving (via prefixed `VNAM`s) to
`SimpleGroup_FaceSkinTones_<phenotype>`.

Seen whole, a race's skin tones are a **grid**: one column per list, one row per tone.

```
                 BSTT                 HSTT                 FSTT  (Complex Group)
                 Body Skin Tone       Hand Skin Tone       Face Skin Tone
                     |                    |                    | 
                     |                    |                    v
Complex Group        |                    |         per phenotype (sex_ethnicity_age)
                     |                    |            +---------+---------+
                     v                    v            v         v         v
Simple Group       Body                 Hands       female_af_md1  …  male_eu_yo1
             +------------------+------------------+-------------+---+-------------+
 STON 0      | SkinTone1        | SkinTone1        | SkinTone1   | … | SkinTone1   |
 STON 1      | SkinTone2        | SkinTone2        | SkinTone2   | … | SkinTone2   |
 STON 2      | SkinTone3        | SkinTone3        | SkinTone3   | … | SkinTone3   |
   …         | …                | …                | …           | … | …           |
 STON N      | SkinToneN        | SkinToneN        | SkinToneN   | … | SkinToneN   |
             +------------------+------------------+-------------+---+-------------+
```

`STON` picks a **row**, and the row has to exist in every column — the body list is
the master count, and hands, every phenotype's face list, and the dermaesthetic
filter (§4.11) must all match it. That is the rule the CK validators below state four
different ways.

**The cost of one extra tone is therefore one texture per column, not one texture.**
A race with *P* phenotypes pays *P* + 2 albedo textures per tone — one body, one
hands, and one per phenotype face. Vanilla human runs 22 phenotypes × 9 tones = **198
face albedos** (plus 9 body and 9 hands), and every phenotype supplies a texture for
every tone whether it suits that phenotype or not.

⚠️ **`STON` is stored 0-based and displayed 1-based.** The xEdit definition is
`wbEnum(['1'..'9'])` over a `uint8`, so raw `0` shows as **"1"**. The raw byte is the
index and lines up with the `sk0`…`sk8` entry names.

**Group length is not fixed at nine.** Humans use 9, `Child_*` skin-tone groups have
3, `Mannequin_Body_and_Hands` has 1, and the Felid race ships 19. Nine is the human
convention and the enum's ceiling, not a requirement — but `STON` must stay inside
whatever length the group has. There is headroom: the largest Simple group in shipped
data is **84** entries (`Dermaesthetic`), and Felid ships 19 tones. ⚠ Do not assume the
`uint8` means 256 is reachable, though — the engine carries a named maximum,
`SkinToneCountMaxC` (*"is out of range SkinToneCountMaxC [0..%u)"*), whose value is not
known. Verified over every `NPC_` in `Starfield.esm`, the range tracks the group length
exactly:

| race | entries in its groups | `STON` values used | NPCs |
|---|---|---|---|
| `HumanRace` | 9 | 0–8 (all nine) | 3,326 |
| `ChildRace` | 3 | 0–2 | 51 |
| `MannequinRace` | 1 | 0 | 75 |
| no skin-tone group (robots, fauna) | — | 0 | — |

⚠ **The index is positional, not parsed from the filename.** `HumanRace` is tidy —
entry *N* is `…_skN_…` in body, hands and face alike — which makes `STON` look like it
means "the sk*N* texture". It does not. `ChildRace` runs entry 0 =
`female_child_01_body_color` (no suffix at all), 1 = `…_sk2_…`, 2 = `…_sk3_…`. The only
real requirement is that the body, hands and face lists are the **same length and in the
same order**; if they drift, an NPC gets a face that does not match its body, silently.

**The Creation Kit enforces this, in its own words.** Its validator strings state the rule
outright, and name the **body** skin-tone group as the master count everything else must match:

- *"Validates that the number of subtype entries for hand skin tones matches the number of
  entries for body skin tones."*
- *"Validates that the number of subtype entries for each type of face skin tone matches the
  number of entries for body skin tones."*
- *"Validates that the number of subtype entries for the complex group DermaestheticChargen
  (dermaesthetic skin tone filters) matches the number of entries for body skin tones."*
- *"Validates that all face skin tone labels are prefixed with 'male' or 'female', and there is
  a subtype label for the default skin tone textures of each sex."*

The individual error messages show what each rule actually checks — and that the **default is
checked separately from the phenotypes**:

- *"Empty skin tone subtype at facial bone region '%d' on %s."*
- *"Invalid skin tone subtype '%s' at facial bone region '%d' on %s. (should be a valid subtype
  from '%s')"* — a phenotype row names a face the group has no label for.
- *"Facial skin tone type '%s' at facial bone region '%d' on %s contains %d subtypes but should
  have %d subtypes."*
- *"Invalid **default** %s skin tone subtype '%s' on %s. (should be a valid subtype from '%s')"*
- *"**default** %s skin tone subtype '%s' on %s contains %d subtypes but should have %d
  subtypes."*

⚠ **Every face skin-tone group needs a `male_default` and a `female_default` label,
whether or not the race has any phenotypes.** The default is not a phenotype — it has no
`FMRI` row (see below) — so it is easy to leave out; the CK checks it on its own, both
that it exists and that its group is as long as the body's. `male_default` and
`female_default` are also literal strings in `Starfield.exe`, so the game looks them up by
name as well. Every vanilla race that has face skin tones carries both:

| race | `FSTT` group | labels | `FMRI` phenotype rows per sex | defaults |
|---|---|---|---|---|
| `HumanRace`, its `SFBGS…_HumanRace` copies, `SFBGS001_RedeemedRace` | `FaceSkinTones` | 22 | 9 | both |
| `ChildRace` | `FaceSkinTones_Child` | **2** | **0** | both |

`ChildRace` is the minimal shape: no phenotype table at all, and a face group that is *nothing
but* the two defaults, each pointing at a Simple group as long as the child body group. A race
that needs one face per sex can copy it.

It confirms the 0-based storage too — *"The skinToneIndex should be in range [0..%u] (which is
range [1..%u] in the CK gui) as defined in AVMS simple group"* — and that an out-of-range
`STON` is *"clamp[ed] to range at runtime"*, not fatal. Note the count is read from the **AVMS
Simple group**, which is also what the in-game creator uses to size its skin-tone slider.

⚠ **Only the face has a phenotype axis.** `BSTT` and `HSTT` name a Simple Group
*directly*, so body and hand colour is exactly that group's length — nine variants,
shared by every human in the game. `FSTT` goes through the Complex Group, so the face
gets 22 × 9 = **198** albedos. **The body and hands also have no filename route:**
`%s\%s_sk%u_color.dds` is the *only* skin-tone-indexed texture format string in either
executable, and it is the face one, so `BSTT`/`HSTT` → `AVMD` is the sole way a skin tone
ever reaches a body. A race cannot skip the AVMD groups by following the filename convention.
A race whose sub-types differ by more than lightness — fur
pattern, species markings — **cannot express that on the body through this mechanism at
all**, because the body path never sees the phenotype. Lengthening the body ladder does
not help either, since the phenotype and `STON` are selected independently (below).

**On the body and hands, a skin tone changes only the albedo.** Every entry in a
`BSTT`/`HSTT` group is a `_color` texture, and nothing in the chain names any other map.
Normal, roughness and AO are **fixed paths in the `.mat`** — slots 1, 3 and 5 of the base
texture set — shared by every tone. Vanilla, verified in `Naked_M_Body.mat`,
`Naked_F_Body.mat` and `DefaultHandsM.mat`:

| slot | `Naked_M_Body.mat` base texture set |
|---|---|
| 0 | `nakedbodym_sk3_color.dds` — the albedo the skin tone replaces |
| 1 | `nakedbodym_normal.dds` |
| 3 | `nakedbodym_rough.dds` |
| 5 | `NakedBodyM_ao.dds` |

So one body material cannot give different tones different normals or roughness; a
per-species fur normal needs a different material, which means a different body.

A body (hands, face) material is made up of multiple layers and the second and higher
levels are composited with a mask. **The `_mask` texture is not a skin-tone mask.** These
materials (`BodySkin2Layer` shader) layers carrying only a **detail normal** —
`faces\FaceDetails\Young_Cheek_detail_normal.dds`, tiled 50 × 50 on the body and 15 × 15
on the hands — and `NakedBodyM_mask.dds` / `defaulthandsm_mask.dds` is slot 0 of
`Blender1`, the blender that lays that detail over the base layer. It controls where the
micro-detail goes; the skin-tone albedo is not masked at all.

#### How the phenotype maps are chosen and blended

`FSTT` names an `AVMD` Complex Group — `ComplexGroup_FaceSkinTones` for humans. That
record is a lookup table: each entry pairs an **`LNAM`**, a phenotype name such as
`male_as_md1`, with a **`VNAM`** naming the Simple Group it leads to
(`SimpleGroup_FaceSkinTones_male_as_md1`).

The phenotype name then reaches the face albedo by **two separate routes**, both keyed on
that same name:

| route | how the albedo is found |
|---|---|
| **AVMD** | the Complex Group entry whose `LNAM` matches → its Simple Group → entry `[STON]` → that entry's `VNAM` texture path |
| **filename** | built from a format string compiled into `Starfield.exe` and `CreationKit.exe` |

The format string is `%s\%s_sk%u_color.dds`, in C `printf` notation: `%s` inserts a string
and `%u` an unsigned integer. Filled in, the first `%s` is the race's `FCTP` directory,
the second is the phenotype name, and `%u` is the NPC's `STON` — so
`actors\FSFCanine\faces\chargen\male_as_md1_sk3_color.dds`. Where the AVMD route resolves
it wins; the normal, roughness and AO maps have **only** the filename route ([Creation Kit
§3](creation-kit.md#albedo-has-a-second-route-the-other-three-do-not)).

Either way, a route resolves **one map for one phenotype**. A face is not made of one,
though: the single `%s` is one *call*, not one phenotype. The engine resolves a map per
source and composites them **region by region**, and both executables carry the machinery to
do it, sitting in the string table beside the format string above:

| string in `Starfield.exe` and `CreationKit.exe` | what it is |
|---|---|
| `%s\FCT_%s_mask.dds` | the mask for one face region — `%s` is the `FCTP` directory, then a region name |
| `%s\FCT_null_mask.dds` | a hard-coded maskless variant; when it is used is unconfirmed |
| `uMaxBlendSources:FCT` | ini setting capping how many sources one face may blend |
| `fBlendIntensityThresholdPerRegion:FCT` | the per-region weight below which a source is dropped |
| `bBlendValidation:FCT` | validation toggle |

The masks exist and they line up exactly: `Actors\Human\Faces\Chargen` ships
`FCT_Cheeks_mask.dds`, `_Chin_`, `_Ears_`, `_Eyes_`, `_Forehead_`, `_Jaw_`, `_Mouth_`,
`_Neck_` and `_Nose_` — the nine `MPGN`/`FMRG` region names, one for one — plus
`FCT_null_mask.dds`.

None of the three settings appears in any shipped `.ini`, so their defaults are compiled in
and unknown.

This applies to `_normal`, `_rough` and `_ao` as much as to the albedo: they are keyed on the
phenotype by the same kind of format string, so they are blended from the same sources. A
custom race needs the full set for **every** phenotype it can blend, not just for its default.

**Nothing on the NPC stores those names.** Checked across all **7,131** `NPC_` records in
`Starfield.esm`: not one carries a `FaceSkinTones` key verbatim in any subrecord. They are
reached indirectly, which is why they are easy to miss:

```
NPC Face Morphs:   FMRI (row id) + FMRG (face group) + FMRS (weight 0...1)
RACE FMRI/FMRU:    row id -> "male_as_md1"      (looked up in the NPC's OWN sex's table)
FSTT Complex:      LNAM "male_as_md1" -> SimpleGroup_FaceSkinTones_male_as_md1
STON:                                 -> entry[N]
```

So the keys are a property of the **face-morph blend**, not a stored field.

⚠ **The `FMRI` id space is per sex.** `HumanRace` uses id **1** for `male_as_md1` *and* for
`female_eu_md2`, and id **9** for `male_af_md1` *and* `female_af_md1`. Resolve an NPC's `FMRI`
through the table of its own sex — `ACBS` flag bit 0 is Female — never through a single
merged lookup. Merging them silently relabels those male phenotypes as female ones, and every
statistic built on top is quietly wrong.

That blend is rarely a single phenotype:

| phenotypes blended | NPCs |
|---|---|
| 1 | 420 |
| 2–4 | 748 |
| 5–6 | 1,187 |
| 7–9 | 636 |

Median 5–6. And the mixing happens *inside* a region, not only between regions — counting the
distinct phenotypes that contribute to the **same** `FMRG` region, across the same NPCs:

| phenotypes in one region | region instances |
|---|---|
| 1 | 5,082 |
| 2 | 1,533 |
| 3 | 592 |
| 4–5 | 240 |
| 6–8 | 589 |

**2,954 of 8,036 region instances — 37% — draw on more than one phenotype**, up to eight
(`FC_Neon_GenericCustomerM01`'s Neck alone blends six), so `uMaxBlendSources` is at least 8.
The weights are not normalised either: per region they sum to anywhere from 0.0 to 2.0,
median 0.49.

**`<sex>_default` is never authored.** Zero of the 2,991 NPCs with a resolvable blend
include it — it is purely the fallback for an actor whose blend resolves to nothing,
which is why an unbaked or preset actor bakes out as `male_default_sk0_color.dds`.

**Four of the 22 keys are unreachable by blending.** `HumanRace` has **9 `FMRI` rows per
sex**, and the diff is clean in one direction: every blendable phenotype has a texture
group, but `male_default`, `female_default`, `male_eu_md1` and `female_eu_md1` have no
`FMRI` row. The two defaults are the hard-coded fallback, so the genuinely dead keys are
just the two `eu_md1` entries. Instead `eu_md2` entries exist and are used, the only
ethnicity/age combination to use an index other than 1. **A Complex Group entry with no
matching `FMRI` row in the race is dead weight** — easy to add to a custom race and never
reach. (The reverse — a phenotype row with *no* entry — is worse, and the Creation Kit
rejects it: see the validator rules above.)

**Phenotype and `STON` are independent axes.** Correlated in vanilla, but not linked:
every one of the 18 phenotypes (9 per sex) appears with **4–9 distinct `STON` values**,
and `female_af_md1` and `male_af_md1` each span all nine (321 and 88 `HumanRace` NPCs).
Mean `STON` is 3.38 for `af` phenotypes, 1.57 for `eu` and 1.09 for `as`; `af` and `as`
span the full 0–8 range and `eu` 0–7. Authors pick sensible pairings; the format enforces
none, so a creator can put any face on any body tone.

### 4.6 Dermaesthetic is *not* tied to the skin tone

A natural assumption, and wrong. The `Dermaesthetic` group's options are named for a
phenotype **and** a tone (`Asian_Male_Ol1_Sk1` → `male_as_ol1_sk1_derm_color.dds`), which
looks like it should track `STON`. It does not, and it cannot: the group only ships **four
tone bands — `sk1`, `sk3`, `sk6`, `sk8`** — uniformly across all 21 phenotypes it covers,
so five of the nine `STON` values have no matching texture at all.

Measured over 2,949 NPCs carrying both: **466 agree (15.8%), 2,483 do not.** Mean
dermaesthetic band does rise with `STON` (2.79 at `STON` 0 → 6.51 at 5) but every `STON`
value draws on all four bands. The phenotype matches one the NPC actually blends only
**45.7%** of the time, and the **sex disagrees on 739 NPCs** — the retail
`CF06_LvlSyndicate_Unaggressive_F01` is female, blends three female phenotypes, and wears
`male_as_md2_sk6_derm_color.dds`.

The layer is an independent overlay carrying subtle skin detail, picked by eye. It does
not need to be authored as a phenotype × tone matrix. Note that the alpha on vanilla
textures goes to 0 at the neck seam, so they'll blend with the body.

**Nor is it required.** It is the most-used slot (3,633 entries across the official plugins), but
of the 2,094 `HumanRace` NPCs with their own appearance data (not inherited from a template),
**323 have no `Dermaesthetic` layer**:

| | NPCs |
|---|---|
| `Dermaesthetic` present | 1,771 |
| other tint layers, but no `Dermaesthetic` | **46** |
| no tint layers at all | 277 |

The 46 are fully tinted faces with the slot simply unused — named characters among them (Gerhard
Pohl, Captain Petrov, Ellie Yankton, Sarah Filburn, Amanirenas) and ten generic
`EncCitizenFaceM…_15` faces. Of the 277, 185 are voice-only placeholders (`AUDIOONLY`,
`NoAppearanceData`); the rest include the 21 `*_scan` phenotype NPCs, the 16
`ChargenHeadShapePreset_*` NPCs and the Starborn faces. **Children barely use tints at all:** 43
of 50 `ChildRace` NPCs have no tint layer, and only 4 have `Dermaesthetic`.

### 4.7 The four accent slots share two texture sets

`Accents1` and `Accents2` are **content-identical** — 24 options each, same names,
same texture paths, zero differences — held in **separate, duplicated records**
(`SimpleGroup_Accents1_color` `0003CD42`, `SimpleGroup_Accents2_color` `0003CD46`).
The duplication exists solely so a face can wear two accents at once: of 1,294 NPCs
using both, **all 1,294 pick different options** in each.

The Colorless variants go further — they are **aliases onto the same records**:

```
ComplexGroup_Accents1           -> SimpleGroup_Accents1_{color,normal,rough,ao}
ComplexGroup_ColorlessAccents1  -> SimpleGroup_Accents1_{color,normal,rough,ao}   (identical)
```

So **two texture sets serve four slots**. Nothing in the data distinguishes
"colorless": all four slots have only a Complex definition (no Modulation palette),
and every vanilla use of all four carries `NNAM = 00000000`. The distinction is in
the engine, keyed on the slot name — and it is literal.

#### "Colorless" means the colour channel is discarded (tested)

**`ColorlessAccents1/2` ignore the `_color` texture's RGB and use only its ALPHA**, as
the coverage mask for the `_normal`/`_rough`/`_ao` detail. `Accents1/2` apply the
colour.

Isolated in the Creation Kit, where only the slot changes. One vanilla option
(`Accents_UnderEyeBags_Small`) had its `_color` texture replaced with opaque blue,
then assigned to one slot and the other on the same NPC:

| slot | baked face |
|---|---|
| `Accents1` | **blue** — the colour texture is applied |
| `ColorlessAccents1` | **no blue** — same texture, same NPC, same bake |

Confirmed a second time with a different option (`Blemish_VeinsMany`): in the CK it
can be applied with or without colour by choosing the slot, and there is no way to
apply it with colour from the in-game creator.

In game it behaves the same way: a bright green `_color` texture on a colorless
accent shows no green at all, and a texture whose alpha is opaque nearly everywhere
spreads the accent's *detail* across the whole face — the alpha is acting as the
mask, exactly as the slot name implies.

⚠️ **A player can never wear a coloured accent.** There is no `Chargen_Accents1` or
`Chargen_Accents2` group, so the character creator reaches only the two Colorless
slots (via `Chargen_ColorlessAccents1/2`). `Accents1/2` are authoring-only — the CK
and NPC records can use them, the in-game creator cannot.

**How vanilla works around it: it authors the same motif into several slots.** The
"many veins" blemish is the clearest case — it exists three times over, and what you
can do with it depends entirely on which slot you reach it through:

| Offered as | In | A player gets |
|---|---|---|
| `Blemish_VeinsMany` — `_color`/`_normal`/`_rough`/`_ao` | `Accents1/2`, `ColorlessAccents1/2` | detail only; the creator reaches it via `ColorlessAccents`, so **no colour** |
| `Blemish_VeinsMany` — the same four textures | `Scars` (`Chargen_Scars_*`) | colour **and** detail — the scar slot applies both |
| `Veins`, `Veins_2` — `veins_mask.dds` | `ComplexionMask1/2` ("Complexion Blemishes" in the UI), with dedicated `Vein_Red` and `Vein_BlueGreen` entries in the Modulation palette | colour, tinted per choice, but **no normal/rough/AO** |

So the engine gives you colour *or* surface detail from these slots, not both — and the
authors worked around it by duplicating the artwork into a slot with the other half. A
custom race that needs both from one mark has the same options: duplicate it, or put it in
`Scars`, which is the only creator-facing slot carrying all four channels.

For a custom race the practical reading is which slots can carry **multi-coloured** marks
at all:

| creator slot | colour |
|---|---|
| `Dermaesthetic`, `Complexion1/2` | full-colour texture |
| `Scars` | full-colour texture + normal/rough/ao |
| `Cheeks`, `Lipstick`, `Eyeshadow`, `Eyeliner`, `TattooMask`, `MakeupFullPaint` | greyscale mask × **one** Modulation colour |
| `ColorlessAccents1/2` | **none** — alpha-masked normal/rough/ao detail only |

`Scars` shows the other Complex-group idiom — one slot fanning out to four
same-named Simple groups (`Scars_color/_normal/_rough/_ao`, 25 options each), so a
single layer buys four synchronised channels. 581 NPCs carry a scar; every one has
exactly one.

### 4.8 The stack is sex-agnostic

Nothing in `PostBlendFaceCustomizationLayers` distinguishes male from female — no
per-gender blocks (unlike the RACE chargen payload, which repeats per sex), and the only
sex marker is embedded in the phenotype strings. 24 of the 26 slots have no sex-specific
content at all.

The two exceptions both encode sex in **option names inside a single shared group**,
not in the structure:

- **`Dermaesthetic`** — all 84 options are sex-specific, in one group, and as above
  the engine does not enforce the match.
- **`EnvironmentMask`** — the option names look neutral (`Dirt_Light`,
  `Dirt_GroundHeavy`) but *every* texture is `test_dirt_female_*_mask.dds`. The
  grime layer ships female-only placeholders applied to everyone.

So per-sex overlay content is a naming convention an author maintains, not something
the format supports or checks.

### 4.9 Worked example — how the shipped Felid race uses this

The published felid race is the useful precedent, because of what it **doesn't** do.

- It **never touches** `ComplexGroup_PostBlendFaceCustomizationLayers`.
- It **repurposes the `Lipstick2` slot** for species face patterns. 23 of its 34
  race-plugin NPCs use `Lipstick2` and nothing else:

  ```
  NPC ChargenPresetMaleFelid_Leopard
     MNAM Simple   TNAM Lipstick2   QNAM LeopardFacePatterns_Default
     VNAM Textures/actors/Felid/faces/chargen/postblenddetails/FacePatterns/
          LeopardFacePattern_Default_color.dds
     NNAM ff000000   INTV 64
  ```

- Its only vanilla overrides are **surgical and additive** — one entry
  (`Stripe_Black`) added to each of `Modulation_Lipstick2` (40→41) and
  `Modulation_Chargen_Lipstick2` (38→39), nothing removed. That override is
  unavoidable given §4.4: a paired Modulation group can't be referenced.
- Everything else is **new records under new names** — `Male_Naked_Body_Skin_Tones_Felid`,
  `FaceSkinTones_Felid`, `Eyebrows_Hair_Short`. Its `_AVMDEXT` records claim their own
  distinct `TNAM`s, so they don't collide with the vanilla name index.
- Its NPCs freely mix its own options with **vanilla** ones (`Blush`, `Freckles_Nose`,
  `Eyeliner_Upper_02`) resolved out of `Starfield.esm`.

The takeaway for a custom race: **work within the existing slot vocabulary.** A
five-species cat race needed no new slots, no layer-list edit, and two one-line
overrides.

Body shape is also stored per-NPC as **`MRSV` Body Morph Region Values**:
five floats — **Head / Upper Torso / Arms / Lower Torso / Legs** — the runtime
expression of the body triangle.

### 4.10 The `Chargen_*` groups decide what the creator shows, and in what order

A slot usually has two groups: the runtime one (`ComplexionMask1`) and a chargen-side twin
(`CHARGEN_ComplexionMask1`). **The in-game character creator reads the chargen-side group,
and its record order is the order the options appear in the UI.**

Across the 20 slots that have both, 16 hold the same options in the same order —
which is why the distinction stays invisible until it doesn't. The exceptions:

| | slots | effect |
|---|---|---|
| **re-ordered** | `ComplexionMask1`, `ComplexionMask2` (46 options), `TattooMask` | `CHARGEN_ComplexionMask1` opens `Freckles_Nose`, `Freckles_Forehead`, `Freckles_Cheek`…, which sit at #21, #26 and #22 in the runtime group |
| **subset** | `Eyeliner1`, `Eyeliner2` | the creator offers 6 of the runtime 9 — three options exist but cannot be chosen |
| **absent** | `Accents1`, `Accents2` | no chargen-side group at all, so the creator cannot reach the slot (§4.7) |

⚠️ The prefix is inconsistent in vanilla — `CHARGEN_Cheeks1` and `CHARGEN_ComplexionMask1`
in caps vs `Chargen_Lipstick2` and `Chargen_Dermaesthetic`. Every lookup here is by name,
so a custom group must match the spelling the slot already uses.

So the chargen-side group does three jobs: **which** options are offered, in **what
order**, and — for dermaesthetic — **filtered by skin tone**, which is the next section.

### 4.11 What in-game chargen offers

Two different records decide what a slot shows in the character creator:

- **`Dermaesthetic`** (Simple) contains skin tone overlays. They are named after the
  phenotype and skin tone options (`<ethnicity>_<sex>_<age><n>_Sk<m>`) but the skin tone
  options are not complete (1, 3, 6, 8) and the alpha lightens the degree to which they
  are applied. 
- **`Chargen_Dermaesthetic`** (Complex, `[000D4004]`) is the **chargen filter**: 9 entries
  index simple groups `chargen_DermaestheticSkinTone0`…`8`, one per skin-tone **index** --
   BUT these simple groups are not simple maps to the skin tone. Instead, groups 0-4
   select skin tones 1/3/6, whereas groups 5-8 select skin tones 3/6/8. Presumably the
   dermaesthetic overlay only looks good if it's not too different in tone from the
   underlying skin.

NPC tint entries reference these names, and §4.1 shows the bake reads the stored `VNAM`
path — so **removing a vanilla entry here cannot break an existing NPC**, but it does
make that option unavailable for any NPC built afterwards.

The in-game character creator offers the intersection. **To restrict a slot to your own
options, trim the filter, not the master list.**

⚠️ **The filter is keyed by tone index and shared by every race — there is no
per-race variant.** Whatever you put there, a human character created in the same
load order sees it too. The same pattern holds for the head-part option lists
(`HeadPartsChargenOptionsMale` `[0003D9AF]`, 98 entries;
`HeadPartsChargenOptionsFemale` `[0003D9B0]`, 76) and for the preset gallery
(`CharGenPresets` `[0003F551]`) — all global, all replaced wholesale rather than
extended. A race mod that takes them over should ship that takeover in a separate
player-facing plugin, the way Felid splits `FelidRace.esm` from `FelidPlayer.esp`,
so the race can be installed without it.

The CK validates that the filter is consistent with the master list — *"all entries
from skin tone filters are valid entries from the main Dermaesthetic reserved
type"* — so entries left in the filter that the master list no longer defines are a
reported error.

### 4.12 Which slots vanilla actually uses

Picking a slot to repurpose is mostly a question of who else is in it. NPCs in
`Starfield.esm` carrying each slot (by `TNAM` on their tint blocks; 22 slots appear
at all):

| slot | NPCs | | slot | NPCs |
|---|---|---|---|---|
| `Dermaesthetic` | 2,949 | | `Eyeshadow2` | 1,053 |
| `ComplexionMask1` | 2,661 | | `Cheeks1` | 975 |
| `Complexion1` | 2,432 | | `Eyeliner2` | 950 |
| `ComplexionMask2` | 2,290 | | `Scars` | 581 |
| `Accents1` | 1,958 | | `Cheeks2` | 568 |
| `Eyeshadow1` | 1,730 | | **`Lipstick2`** | **534** |
| `Lipstick1` | 1,515 | | `EnvironmentMask` | 449 |
| `Accents2` | 1,384 | | `ColorlessAccents1` | 255 |
| `Complexion2` | 1,279 | | `ColorlessAccents2` | 120 |
| `Eyeliner1` | 1,235 | | `MakeupFullPaintMask1` | 88 |

That is the case for Felid's choice of `Lipstick2` (§4.9): it is the least-used paint
slot, it composites **19th of 26** — above complexion, scars and accents, so a species
marking is not painted over — and its vanilla content is six placeholder assets
(`testlipliner01_mask`, `testlipstain02/03_mask`, two of which even point into the
`lipstick1` folder). A complexion slot would have collided with 2,000+ NPCs and sits
at position 2-4, under everything else.

Slot *type* is not the constraint: both texture kinds are legal in a slot.
`Complexion1`'s own options are full-colour `*_color.dds`, while `ComplexionMask1`'s
are `*_mask.dds` tinted by a Modulation palette.

### 4.13 Overlay texture formats — uncompressed, and the header matters

Face-customization layers are authored **uncompressed**. Census of all 448 vanilla
files under `textures/actors/human/faces/chargen/postblenddetails/`, every one
**1024×1024 with a single mip** (as are all 274 base maps in `faces/chargen/` itself; the
size has to match across the set, below):

| suffix | n | format | bytes |
|---|---|---|---|
| `_color` | 145 | DX10 `R8G8B8A8_UNORM_SRGB` | 4,194,452 |
| `_mask` | 179 | **legacy** header, uncompressed 8bpp red (R8) | 1,048,704 |
| `_ao` | 40 | legacy 8bpp | 1,048,704 |
| `_rough` | 39 | legacy 8bpp | 1,048,704 |
| `_normal` | 40 | legacy uncompressed 32bpp **signed** | 4,194,452 |
| `*_mask_1` | 5 | DX10 `BC4_UNORM` — the only compressed files here | 524,436 |

Bethesda's headers are also consistent, and differ from what a default `texconv`
run produces. For the same pixels, vanilla writes:

| field | vanilla | texconv |
|---|---|---|
| `dwFlags` | `0xA1007` (…`LINEARSIZE`) | `0x2100F` (…`PITCH`) |
| size field | whole image (`w×h×bpp`) | one row's pitch |
| `dwDepth` | 0 | 1 |
| `dwCaps` | `0x401008` (`COMPLEX/TEXTURE/MIPMAP`) | `0x1000` (`TEXTURE`) |
| DX10 `alphaMode` | 0 (unknown) | 1 (straight) |
| 8bpp pixel-format flags | `DDPF_RGB` (`0x40`) | `DDPF_LUMINANCE` (`0x20000`) |

Both encodings are legal DDS. They are called out because a mod author reports the
creator's dermaesthetic chooser rejecting layers that were the right format but
carried `texconv`'s header; matching vanilla's fields is the cheap way to take the
question off the table. `texconv` needs `-m 1` to stop building a mip chain, and
**no `-dx10`** for the 8bpp masks, since vanilla writes those with a legacy header.

**Every face texture must be the same size — any size (in game, 2026-10-18).** The creator
re-composites the face each time a tint layer changes, from the race's `FCTP` base maps
(`<phenotype>_sk<N>_color`, `_normal`, `_rough`, `_ao`, the `FCT_<region>_mask`s) and the chosen
options. A custom race whose files were at mixed sizes (colour 4096, normal 1024, rough 2048,
overlays 4096) looked right until the first dermaesthetic change, then rendered the face
**black**, for both sexes. With every file at 1024 it worked; with every file at 2048 it worked
too. So the rule is "one size", not "1024": vanilla's are all 1024 only because they all match.

The consequence for a race that goes bigger than 1024: **every vanilla option the creator still
offers it is 1024**: scars, accents, lipstick, the second complexion and so on. Picking any of
them would black the face. So either keep the face set at 1024, or replace or empty every tint
group the creator shows that race.

**Layers composite by the texture's own alpha** — there is no per-slot blend mode
doing it for you. A layer with opaque alpha lands flat on top and hides what is
beneath. Vanilla's dermaesthetic layers are correspondingly soft: in a sampled file
only **63 pixels of a million exceed alpha 250**, and the commonest non-zero values
are 1 and 17. They also keep real skin colour in RGB **underneath** transparent
areas, so bilinear filtering never bleeds a halo at an edge — worth copying, since
transparent-white padding will fringe.

---

## 5. The body & head mesh — `.mesh` files and `BSGeometry`

**The biggest structural change from `[FO4]`/`[Skyrim]`: geometry is no longer
stored inside the `.nif`.**

The NIF keeps the scene graph and the skinning; the vertices live in a separate
`.mesh` file it points at. **[meshes.md](meshes.md) is the reference for all of
it** — the `BSGeometry` block, the `geometries/` path scheme, the `.mesh` byte
layout, and where bone names and bind transforms are stored. This page covers
only what bites you on a *head part*.

**Practical gotcha:** the community reports "internal geometry" (embedding mesh
data in the NIF rather than an external `.mesh`) **causes issues with head
parts** — head parts should reference external `.mesh` files.

**Watch the mesh-path length.** The "creating a playable race" guide reports that
the path stored in `BSGeometry → Meshes` must be **≤ 46 characters** or the shape
renders invisible in game while looking correct in the Creation Kit — see
[meshes.md](meshes.md#hash-path-scheme-geometries). *Reported, not measured here.*
Head parts are where it would bite first, since a race-namespaced folder plus a
part name eats the budget fast; keep them short regardless.

### Body layout
The body is delivered by the race's `WNAM` Skin `ARMO` and its armor addons, cut
into biped slots (§7). Community body replacers (e.g. the SFF female body) show
the division as separate meshes for **body, hands, feet, first-person body/hands,
head**, each skinned to the shared skeleton, each with its own `.mesh`, morphs,
UVs, and skin-tone textures (`sk6/sk7/sk8` texture variants seen in the wild).
Head and body are **separate meshes joined at the neck**.

Tools: **NifSkope (fo76utils fork)** for Starfield NIFs; **Starfield Geometry
Bridge** / **StarfieldMeshConverter** (Blender) for `.mesh` and `.morph` I/O.
`[PyNifly]` — nifly's `BSGeometry` support is the C++ basis for reading these.

---

## 6. Skeleton, and adding a tail / ears / digitigrade legs

### The skeleton
Still a **NIF-based** `skeleton.nif` referenced by `RACE → Skeleton Data →
ANAM Skeletal Model`. Bone naming uses a **`C_` (center) / `L_` / `R_`** prefix
convention with a `Root` and `COM` (centre-of-mass) at the top, then `C_Hips`,
spine, neck, head, and limb chains. (Contrast `[Skyrim]` `NPC Root [Root]` /
`NPC COM [COM]` and `[FO4]` `Root`/`COM`/`Pelvis` — same idea, new names.)

**Verified** against the extracted vanilla `meshes/actors/human/characterassets/skeleton.nif`
(Gamebryo 20.2.0.7, BSVersion 173): **116 `NiNode` blocks**. The community `HumanRace.json`'s
"92 bones" counts only the **deform** bones and omits the ~24 helper nodes present in the file
(cameras, `AnimObject*`, IK/target helpers, physics nodes). The full ordered list, grouped:

- **Roots/helpers:** `HumanExportRoot, Root, COM, CamTargetParent, CameraTarget, Camera Control, Camera Control FP, Camera, AnimObjectA–D, Eye_Target, DirectAt, WEAPON, WeaponLeft, R_HandIk, L_HandIk, CharacterBumper, CharacterController` (+ one unnamed helper node).
- **Spine/head:** `C_Hips, C_Spine, C_Spine1, C_Spine2, C_Chest, C_Neck, C_Neck1, C_Neck_Twist, C_Head, L_Eye, R_Eye`.
- **Legs (mirrored L_/R_):** `Thigh, Calf, Foot, Toe, CalfMass, Knee, Thigh_Twist, Thigh_Twist1, Butt`.
- **Arms (mirrored):** `Clavicle, Biceps, Forearm, Wrist, Arm, Deltoid, Elbow, ArmMass, Biceps_Twist, Biceps_Twist1, Wrist_Twist, Wrist_Twist1, Wrist_Twist2, AnimObject1–3`.
- **Hands (mirrored):** `Cup, Thumb/1/2, Index/1/2, Middle/1/2, Ring/1/2, Pinky/1/2`.
- **Misc:** `C_BackPack, C_BackPackHose`.

Convention confirmed: `C_` = centerline, `L_`/`R_` = mirrored, suffixes `_Twist[N]` / `…Mass` / `…Ik`.
The skinned body NIF weights to a **38-bone subset** of these (via `SkinAttach`, see §5). The community
**SF Extended Skeleton** mod adds extra bones (tail, ears, breast, belly, genitalia…) on top of this
base and is the de-facto dependency for body mods that need new bones.

### Two ways to add animated appendages

**(a) Bone Modifiers (`BMOD`) — the Starfield-native, no-behavior-graph path.**
A race lists `BMOD` records under **Head Parts and Bone Modifiers → Bone
Modifiers**. Each `BMOD` has a `DATA` struct:
```
Type    : LookAtChain | MorphDriver | PoseDeformer | SpringBone
Driver  : source bone/node
Target  : bone to modify
Max Anim Distance
+ type-dependent data
```
- **SpringBone** — jiggle/physics chain (Strength, Damp, Scale, MaxDist,
  `Look At Parent`). **This is how a tail or ears can be made to swing at runtime
  without authoring a Havok behavior graph.**
- **LookAtChain** — chain that aims at a target (ears tracking, tail follow).
- **PoseDeformer** — corrective pose-driven deformation (position/angle/scale +
  falloff radius + axis).
- **MorphDriver** — drives a morph from bone motion (vector + falloff radius).

Because BMODs attach at the RACE level, a furry race can — *in principle* — add a
physics tail and mobile ears by (1) adding the bones to `skeleton.nif`, (2)
skinning the tail/ear `.mesh` to those bones, and (3) adding `SpringBone`/
`LookAtChain` BMODs — **all in data**, no behavior-graph compile step. That would
be the single biggest practical advantage Starfield has over `[Skyrim]`/`[FO4]`
for appendages (which needed XPMSSE + HDT/CBP or custom behavior work).

**Conflicting evidence — verify before relying on this.** The BMOD `SpringBone`
mechanism is confirmed to *exist* in the RACE record definition, but the shipped
community appendages tell a more cautious story: the **Felid** race's tail is
driven by **Havok cloth physics** (a low-poly sim mesh weighted to the tail bones,
baked with `BSClothExtraData` via the Havok Content Tools), and is widely reported
as "wonky." Separately, the **SF Extended Skeleton** documentation states its
added bones "do not have their own collisions" and are intended for cloth physics,
and one modder resource states plainly that "additional bones cannot be controlled"
by the game. It is **not yet confirmed** that any shipped mod drives custom
appendages through vanilla `BMOD SpringBone` rather than the cloth route. Treat
"tail/ears via BMOD" as a **promising but unproven** path and settle it with a
throwaway in-engine test early — the fallback is Havok cloth (proven, imperfect).

**(b) Full behavior graph.** For *animated* (keyframed, gameplay-reactive)
appendages you still need the Havok behavior graph (`RACE → Subgraph Data →
SGNM Behaviour Graph` + animation paths). There is **no public Starfield behavior
graph editor** (hkbProject authoring), so extending the behavior graph is a hard
blocker — most non-human mods **reuse `HumanRace`'s graph** and rely on BMODs +
new geometry rather than new locomotion.

---

## 7. Biped slots (the 64-slot layout)

Starfield uses **64** biped-object slots (indices), split into normal and
**spacesuit ("SS")** duplicates. Selected slots:

| # | Slot | | # | Slot |
|---|---|---|---|---|
| 0 | Hide Hair | | 17 | Beard |
| 1 | Morph Hair | | 18 | Neuroamp |
| 2 | Hide Head | | 19 | **Hide Ear** |
| 3 | BODY | | 20 | AddonRig |
| 4 | Hat | | 26 | Eyepatch |
| 5 | Backpack | | 27 | Morph Beard |
| 6 | Gloves | | 29 | Shield |
| 7 | Lower Body (Vis Only) | | 30 | BoostPackFX |
| 8 | Sleeves (Vis Only) | | 32 | SS Hide Hair |
| 9 | Head (Vis Only) | | 34 | SS Hide Head |
| 10–15 | Upper Body / Misc (Vis Only) | | 35 | SS BODY |
| 16 | Eyes | | 36–49 | SS Helmet…Beard |

`Hide Hair` / `Hide Head` / `Hide Ear` are toggle slots that let clothing hide
character parts; `Morph Hair` / `Morph Beard` reshape hair to fit helmets. The
`SS` block mirrors the whole set for spacesuits, so a race must consider both
regular and spacesuit rendering.

### The skin `ARMO` chain (`WNAM` → `ARMO` → `ARMA`)

A head part is named by the race directly; **the body is three hops away**. The race's `WNAM` names a skin **`ARMO`**, whose repeated
`INDX`+`MODL` pairs name **`ARMA`** armor addons — one per biped slot:

| `ARMA` field | Meaning |
|---|---|
| `RNAM` | the race the addon fits |
| `MODL` (repeated) | **Additional Races**. ⚠ On an **`ARMO`** the same signature is the *addon list* instead — same four letters, unrelated payloads. |
| `MOD2` / `MOD3` | male / female 3rd-person NIF |
| `MOD4` / `MOD5` | male / female 1st-person NIF |
| `NAM4` / `NAM5` / `NAM6` / `NAM7` | the `MRPH` body morph paired with each of those four models |
| `BO64` | biped slot mask — body `0x08`, hands `0x40` |
| record flags | `0x80` Is Skin, `0x100` Is Skin Hands, `0x400` No Model |

Vanilla human skin is `Skin_Naked` → `AA_Naked_Body` + `AA_Naked_Hands`. The `ARMO`'s own
`BO64` is `0x08` only and does **not** need to cover its addons' slots. The frozen-corpse
skin addons carry neither Is Skin flag, so a skin addon doesn't need one.

**But the flag decides the addon's colour (in game, 2026-10-14 and 10-18).** An addon flagged
**Is Skin** is painted with the race's **body** tone texture (`BSTT`) by the actor's `STON`;
one flagged **Is Skin Hands** gets the **hands** tone (`HSTT`). Either way the texture its own
material names is overridden. Two ways this bites:

- A tail flagged Is Skin Hands got the hands texture at body UVs: the wrong colour everywhere.
  A tail is skin, so flag it Is Skin.
- Crowd tails copied from a skin addon, each with its own blue material, came out red:
  the copies kept the flag, so the engine coloured them from the tone ladder and ignored the
  material. An addon that carries its own colour should have the flag cleared. (That clearing
  the flag fixes it is the next in-game check.)

⚠ **An addon whose race list excludes the actor's race is skipped without a word** —
that slot of the body simply does not render. This is the easiest way to end up with an
invisible body or missing hands on a custom race.

**`RACE\RNAM` "Armor Race" complicates the match.** A custom race normally points it at
`HumanRace` so vanilla clothing fits, which leaves its own skin addons with two candidate
races — and vanilla does not settle which the engine matches on:

| race | Armor Race | its skin `ARMA` names |
|---|---|---|
| `MannequinRace` | `HumanRace` | **`MannequinRace` only** |
| `HumanCorpseRace` | `HumanRace` | **`HumanRace`** (+ Corpse, Mannequin as additional) |

Mannequins work only under the actual-race rule; corpses work under either. `HumanRace`
itself leaves Armor Race unset. **Practical rule: list both** — it costs nothing, and it
is the first thing to check on an invisible body.

**Body morphs are indexed by vertex, exactly like the head.** `NAM4`/`NAM6` point at
`MRPH` records whose `morph.dat` must match the model's vertex count —
`MORPH_Human_Male_Body` is **6,464 verts, 3 keys** (the `Overweight`/`Thin`/`Strong`
body-build morphs, which are engine body-build morphs and *not* members of the race's
`MPGM` list). A body remeshed to a different vertex count cannot use them.

**An NPC can override the race's skin outright.** `NPC_` carries its own `WNAM` Skin
(`ARMO`), used by **1,851** NPCs in `Starfield.esm`, 147 in `ShatteredSpace.esm` and 36 in
`SFBGS00D.esm`. This is the only mechanism that puts a genuinely *different body* — rather
than a different tone — on an actor of a given race. ⚠ It is authored per record, so it
serves hand-built NPCs but **cannot be driven by chargen**: a playable race cannot offer
it as a player choice.

---

## 8. FaceGen (baking NPC faces)

`[Skyrim]`/`[FO4]` bake a per-NPC head into
`meshes/actors/character/facegendata/facegeom/<Plugin>/<FormID>.nif` plus a
face-tint `.dds`. Starfield keeps the concept: the Creation Kit bakes each NPC's
head part + morph-dial values + tint layers into a per-NPC head mesh and tint
texture written under `Data/…` (loose, then archived).

- **Verified:** the CK regenerates faces per-NPC (community "Regenerating Faces"
  guides exist); a **NPCs Face Data** Synthesis patcher fixes missing masters so
  the CK loads the right resources; and failed/mismatched facegen produces the
  classic **dark-face / neck-seam skin-tone mismatch** and floating eyes/teeth.
- **Resolved (2026-07):** the Starfield output layout is **not** FO4's `facegendata/facegeom`. The
  per-race **base head** is baked to a texture set at
  `Data\Textures\actors\Character\FaceCustomization\<Plugin>.esp\BaseHead<RaceEDID><Sex>_<map>.dds`,
  keyed by the race EDID — or `…\<NPC FormID>_<map>.dds` once the NPC has at least one tint layer.
  Full details, formats, and the CK/CKPE baking workflow are on the
  [Creation Kit & FaceGen page](creation-kit.md).
- **The bake never *reads* the material — but the material still drives the face at render time.**
  Keep the two apart, because the same `.dds` files are involved in both:
    - **What the bake reads:** all four maps come from the race's `FCTP` directory by filename
      convention (§1, `FCTP`) — albedo, normal, roughness **and** AO. Measured with the loose
      `male_default.mat` deliberately pointed at unrelated textures, the baked `_rough` and `_ao`
      came out byte-identical to `male_default_rough.dds` / `male_default_ao.dds` and `_Normal`
      identical within BC5 quantisation. The material's texture paths are never consulted. The
      albedo is optionally redirected per skin tone through the `FSTT` → `AVMD` chain (§4);
      normal, roughness and AO have **no** AVMD route.
    - **Why it looks like the material supplies them:** a head material's *base layer* points at
      those very same `FCTP` files. The bake reaches them by filename, not by following the
      material, so the two agree until you change one without the other.
    - **What the material still contributes:** its **upper layers are not baked in** and composite
      at render time instead — a vanilla head material carries five detail-normal layers (pore,
      stubble, lips, cheek, skin detail), each masked to a face region. So the per-region normal
      detail across the face *is* the material's doing; it simply never reaches the baked maps.
      (That last step is inference, not measurement — see the note in Creation Kit §2.)

  See [Creation Kit §2–3](creation-kit.md#2-facegen-output-what-it-bakes-and-where-verified).

Implication for a furry race's NPCs: every NPC of the race must be baked in the
CK with the race's head parts, morphs, and fur tints — a bulk, error-prone step.
This is exactly the pain point that the furrifier tooling (writing the baked
`.nif`/`.dds` directly instead of Ctrl+F4-ing in the CK) aims to eliminate.

---

## 9. Building a custom race

**A *truly new* playable race — own RACE record, own skeleton, own behavior graph — is not
a solved problem.** Every shipped "anthro/beast" race is a **skinned reworking of
`HumanRace`**: new head parts, new tint groups, new body/head `.mesh` + `.morph`, BMOD-driven
appendages, reusing the human skeleton and behavior graph. Plan for that shape of solution.

What follows is a realistic build order, easiest→hardest. Each step lists what it produces,
so this doubles as the completeness checklist.

1. **Clone `HumanRace`** (or override it) rather than authoring a new skeleton/behavior
   graph — you inherit locomotion, facegen wiring and biped slots for free.
   *Produces:* the `RACE` record, with `Skeleton Data` (`ANAM`/`NAM5`/`NAM6`/`DNAM`),
   `WNAM` Skin `ARMO`, `GNAM` Body Part Data and the FaceGen clamps set.
2. **Skeleton.** The human skeleton, or SF Extended Skeleton, **plus tail/ear bones** if
   you want animated appendages.
   *Produces:* `skeleton.nif`.
3. **Body & head meshes.** Model in Blender; export with PyNifly or Starfield Geometry
   Bridge, skinned to that skeleton. Starfield heads carry a much higher vert count than
   older games, so there is room to work. Consider both the normal and the **SS
   (spacesuit)** slots.
   *Produces:* body/head/hands/feet `.mesh` files and their NIFs (`BSGeometry` +
   `SkinAttach`). Keep mesh paths short (§5).
4. **Morphs.** Author performance (expression) and chargen shape keys for the head, and
   "Overweight" / "Strong" / "Thin" for the body.
   *Produces:* `.morph` files, `MRPH` records, and optionally a bone-morph definition.
5. **Head parts.** Create `HDPT` records for head, mouth/teeth, tongue, eyes — and the
   **Creature Head / Tail / Wings / Arms / Legs** types for muzzle, ears and tail. Set
   `RNAM Valid Races` to your race's `FLST`, point `MNAM` at the `MRPH`, and wire the
   defaults into `RACE → Head Parts`.
   *Produces:* the `HDPT` set and its `FLST`.
6. **Fur / markings.** Build `AVMD` tint groups (stripes, spots, muzzle mask, belly) —
   either overriding vanilla groups or extending them, since **slots resolve by name**
   (§4.4, §4.11). Reference them from `RACE → Chargen and Skintones` and head parts'
   `Color Mapping`. Layers stack, so patterns are additive overlays.
   *Produces:* `AVMD`/`AVMS` groups, skin-tone subtypes, and the `TXST`/face textures
   behind them.
7. **Chargen visibility.** Append your head parts to `HeadPartsChargenOptionsMale
   [FLST:0003D9AF]` / `…Female [0003D9B0]`. Eye Color needs **both** a left- and a
   right-eye head part. This list is one of several things the engine finds by hardcoded
   FormID rather than through your RACE record — see
   [§1, What the RACE record does *not* reach](#records-the-engine-finds-directly) for
   the consolidated set.
8. **Creator sliders.** Expose custom sliders via **CharGenMenu** + JSON whose keys match
   your `.morph` keys; define **Face Dials** and **Face Morph Phenotypes** in the RACE
   record for presets.
   *Produces:* the chargen wiring, plus `BMOD` Bone Modifiers (SpringBone for tail/ear
   jiggle, LookAtChain for ear tracking) on `RACE → Bone Modifiers`, and `BPTD` Body Part
   Data if you changed the anatomy's dismemberment regions.
9. **FaceGen bake.** Bake every NPC of the race in the CK; check the neck seam's skin-tone
   match and that eyes and teeth are not floating. Consider a direct facegen writer rather
   than mass Ctrl+F4.
10. **Player plugin.** Put the race in one plugin and the player overrides in a second, so
    the race can be present for NPC mods without forcing you to play as it. See
    "The player records" below.
11. **Ship it.** Pack as `<Name> - Textures.ba2` plus `<Name> - Main.ba2`; **`" -
    Meshes.ba2"` is no longer recognised by Starfield.** Players will also need SFSE,
    CharGenMenu, and likely SF Extended Skeleton.

### The player records

Setting `Player [NPC_:00000007]` to your race is not enough — the game swaps in **stand-in
copies of "you"** during the main quest, in crew slots, and in the creator, and each is its
own `NPC_` with its own race. Miss one and you turn human in that scene.

The ExoRace guide says "there are 12"; that is one mod's count, not a fixed number.
Measured across the shipped player plugins on disk — **Felid overrides exactly 12, Lupus
14** — the full vanilla candidate set is **16**:

| FormID | Record | Felid | Lupus |
|---|---|:-:|:-:|
| `00000007` | `Player` | ✔ | ✔ |
| `00017627` | `Crew_Elite_OtherPlayerFemale_NoAppearanceData` | | ✔ |
| `00017628` | `Crew_Elite_OtherPlayerNonbinary_NoAppearanceData` | ✔ | ✔ |
| `001A93A5` | `Crew_Elite_OtherPlayerMale_NoAppearanceData` | ✔ | ✔ |
| `00045F82` | `MQ401h_OtherPlayer_NoAppearanceData` | ✔ | ✔ |
| `001557FA` | `MQ302b_OtherYou_NoAppearanceData` | ✔ | ✔ |
| `0017F7A8` | `MQ401c_OtherYou_Loner_NoAppearanceData` | ✔ | ✔ |
| `0017F7A9` | `MQ401c_OtherYou_RI_NoAppearanceData` | ✔ | ✔ |
| `0017F7AA` | `MQ401c_OtherYou_FC_NoAppearanceData` | ✔ | ✔ |
| `0017F7AB` | `MQ401c_OtherYou_UC_NoAppearanceData` | ✔ | ✔ |
| `0017F7AC` | `MQ401c_OtherYou_CF_NoAppearanceData` | ✔ | ✔ |
| `0017F7AE` | `MQ401c_OtherYou_Constellation_NoAppearanceData` | ✔ | ✔ |
| `0024EF81` | `MQ_Unity_NoAppearanceData` | | ✔ |
| `002E7C8E` | `ChargenFemalePlayer` | ✔ | |
| `0007DC47` | `ChargenPlayer_Swap` | | ✔ |
| `00004858` | `ChargenFemalePlayer_Swap` | | |

The six `MQ401c_OtherYou_*` are the faction endings — that block is complete, `0017F7AD`
is not an `NPC_` at all. All 16 are `HumanRace` in vanilla. **`ChargenFemalePlayer_Swap` is
overridden by neither shipped mod**, and the two disagree on the crew and chargen entries,
so treat the list as "everything here, minus what you can show you don't need" rather than
copying either mod.

### Finishing fixes & gotchas

Concrete FormIDs/steps that trip up first-time race authors:

- **Spacesuit not showing:** add your race to `HumanRaceORChildRaceORHumanCorpseRace [CNDF:0003D8C1]`.
- **Dialogue camera too close:** add your race to `DC_Race_Human [CPTH:000C1056]`.
- **Invisible limbs in new-game chargen:** give `Clothes_GenWare_01 "Space Undersuit" [ARMO:00165722]` a skin ARMA / remodel it to your naked-skin model.
- **Eyebrows fully transparent:** they also need `SimpleGroup_EyebrowOpacity [AVMD:0000EF9F]`
  and `NAM3 - Mask` = `EyebrowColor` on the head part.
- Quirks: the **first** eyebrow in a list ignores its assigned texture (engine bug).

### Hard blockers
- **Behavior graph.** No public Starfield behavior-graph editor → no new
  locomotion;
  reuse human legs.
- **Format maturity.** `.mesh`/`.morph` are reverse-engineered, not documented
  by Bethesda; tooling (SGB/StarfieldMeshConverter/PyNifly) is the source of truth
  and can lag engine updates.
- **FaceGen scale.** Baking many NPCs is slow and fragile (dark-face bug).
- **Creator UI.** Radically non-human morphology stresses a UI/morph system
  designed around a human face; sliders assume human topology.
- **True new RACE.** Own skeleton + behavior graph + genome integration is
  unproven; the safe route is a `HumanRace` variant.

---

## Open questions / uncertainties

1. **BMOD limits** — how many SpringBone chains the engine handles gracefully,
   and whether ear LookAtChain works on first-person, is untested here.
2. **Can a genuinely new RACE (non-`HumanRace`-parented) enter the creator?** No
   confirmed example; all anthro results are HumanRace variants.
3. **Digitigrade locomotion** — no confirmed shipped example; behavior-graph gap
   is the suspected blocker.
4. **Does the player's live face use stored tint paths, like the NPC bake?** The bake is proven
   to use each tint entry's stored `VNAM` (§4.1). Whether the player's creator-driven composite
   re-reads the `AVMD` groups, and whether layer order comes from the stack (§4.3), is untested.

---

## Sources

- SF1Edit (xEdit) Starfield record definitions `wbDefinitionsSF1.pas` (RACE, HDPT,
  MRPH, BMOD, AVMD, NPC_, biped-object enum) — local dev tree, cross-checked vs
  `Starfield.esm`.
- nifly `include/Geometry.hpp` — `BSGeometry`, `BSGeometryMesh`,
  `BSGeometryMeshData` (mesh/morph/skin structure, meshlets, havokScale).
- StarfieldMeshConverter `src/MorphIO.cpp` / `include/MorphIO.h` (SesamePaste233) —
  authoritative `morph.dat` read/write; layout + DEC3N/half-float helpers verified
  byte-exact against vanilla `chargen`/`performance` morph.dat, 2026-07-14.
- Organization of Starfield's Meshes and Related Assets — https://www.nexusmods.com/starfield/articles/268 (mirror: https://allmods.net/starfield-mods/starfield-miscellaneous/organization-of-starfields-meshes-and-related-assets/)
- "Notes and pitfalls on creating a playable race" (ExoWarlock313), the primary race-build walkthrough — https://www.nexusmods.com/starfield/articles/431
- CharGen Resources Tutorial (AVM group catalog + RTFP config syntax) — https://www.nexusmods.com/starfield/articles/481
- Starfield Geometry Bridge (Blender) — https://www.nexusmods.com/starfield/mods/4360 ; docs https://starfieldgeometrybridge.github.io/ ; mesh tips https://starfieldgeometrybridge.github.io/docs/tips/mesh/ ; nif tips https://starfieldgeometrybridge.github.io/docs/tips/nif/
- StarfieldMeshConverter (SesamePaste233) — https://github.com/SesamePaste233/StarfieldMeshConverter
- SF Extended Skeleton — https://www.nexusmods.com/starfield/mods/16905
- Native Animation Framework SF (NAFSF) — https://www.nexusmods.com/starfield/mods/7360
- CharGenMenu — https://www.nexusmods.com/starfield/mods/6850
- SFF Body Replacer — https://allmods.net/starfield-mods/starfield-characters/sff-body-replacer-v1-0/
- Felid Race — https://www.nexusmods.com/starfield/mods/17160
- CP's Menagerie — https://www.nexusmods.com/starfield/mods/7783
- Character Creation overview — https://starfield.wiki.fextralife.com/Character_Creation ; https://www.starfielddb.com/character-creation/ ; https://www.pcgamesn.com/starfield/character-creation
- Generating/Regenerating FaceGen — https://forums.nexusmods.com/topic/13526765-generating-facegen-data/ ; https://github.com/The-Animonculory/Modding-Resources
- NifSkope (fo76utils fork) for Starfield — https://www.nexusmods.com/starfield/mods/10748
- Companion Library pages: `morphs-shapekeys.md`, `dismemberment.md` (TRI/BPTD ancestry).


*Reviewed: Bad Dog 9/20/26*
