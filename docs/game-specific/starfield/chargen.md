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

This is *why* the whole custom-race workflow is "clone HumanRace" — you inherit
everything the game's race checks rely on. Two design paths follow:

- **Clone HumanRace → a new race**, assigned to the player and chosen NPCs.
  Selective, toggleable, mod-compatible (the article-431 route documented below).
- **Override `HumanRace` itself** (swap its skin ARMO / default head parts) →
  *everyone* changes, with no per-NPC editing, but it's total, not toggleable, and
  conflicts with other appearance/body mods. Ambient crowds are `HumanCrowdRace`
  (override that too for full coverage); kids are `ChildRace`.

**Selecting the player's race is done by plugin, not in the creator** (same as `[FO4]`):
Starfield has no in-chargen race picker, so a mod sets the player's race by **overriding
the player NPC record (form `7`) + its 12 copies** (article 431). This pairs naturally
with the chargen topology-lock (above): put the **topology boundary at the race/plugin**
— one race (and a small player-setting plugin) per distinct head *geometry* (canid,
felid, …) — and handle all same-topology variety (fur color, markings via AVMD overlays,
ear/tail head parts, muzzle morphs) *inside* the creator. For a multi-species pack: a
core master defining all races + shared assets, plus one tiny "player" plugin per race
that does the player-record override (only one can win — enabling one = the choice).

What actually "notices" a race swap: conditions testing a **keyword**
(`ActorTypeNPC`/`ActorTypeHuman`, etc.) **pass** — a clone inherits HumanRace's
keywords, covering most generic AI/quest/dialogue checks. Conditions testing the
**specific race form** (`GetIsRace HumanRace`) or a **race form-list** **fail** until
you add your race — which is exactly what the finishing-fix form-lists patch
(spacesuit `CNDF:0003D8C1`, dialogue camera `CPTH:000C1056`; see §10). Going wide to
named NPCs also means re-baking **FaceGen** per NPC (the slow, fragile part);
player-only avoids it.

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
  — but **no `PNAM` head parts, no face morphs, `EDCT` (tint count) = 0**, and `ACBS`
  template flags of `Factions, Keywords` only (**not `Traits`** → appearance not
  inherited). The head instead comes from the **outfit**: each `Outfit_Crowds_*` equips
  clothing **plus a leveled list `LL_Crowd_Heads [000F4E92]`** (variants
  `_Overweight` / `_Thin`) that draws one of **8 authored `CrowdHead_<phenotype>` ARMOs**
  (`CrowdHead_af_md1`, `_eu_yo1`, … ethnicity×age). A `CrowdHead` ARMO sits on **biped
  slot 2 (Hide Head)** and shows its head mesh via an `AA_CrowdHead_*` addon. So a crowd
  face = a random head ARMO from a finite pool + random skin tone + random height. No
  per-NPC FaceGen.

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
leveled list**, so mixed-species furry crowds are a *data-driven* job, not per-NPC and
not multi-race:
- Author furry head ARMOs (`CrowdHead_Wolf`, `_Cat`… — ARMO on slot 2 + `AA_CrowdHead_*`
  addon → furry head mesh/material) and **add them to `LL_Crowd_Heads` (+ `_Overweight`/
  `_Thin`)**. Every crowd NPC then randomly draws a furry head → mixed-species crowds
  from **one leveled-list edit**. One crowd race hosts all species — no extra races.
- The **body** is the shared `WNAM` (`Skin_Crowd_Base_Body`); override it to a furry body.
  Head and body vary independently (vanilla reconciles via skin-tone textures), so either
  use one generic fur-textured anthro body and vary only heads (simplest), or tie body to
  head species (bundle a body into each `CrowdHead` set / make species-specific
  actors/outfits) if per-NPC body-species matching is required.
- **How much body-matching matters depends on visible skin.** A crowd outfit equips just
  three things: one **slot-3 (BODY) full-body garment** + `LL_Crowd_Heads` + a hair
  leveled list (`LL_Crowd_Hairs_NoHats`). Vanilla crowd clothing is nearly all long-sleeved
  full-body pieces (jackets/sweaters/jumpsuits/fatigues) with boots, so the exposed skin is
  usually just **head/neck + hands** (sleeves end at the wrist; hands are the shared body
  skin, not gloved). So outside revealing areas a generic fur body + varied heads reads as
  seamless — only the head needs to carry species. **Neon is the exception** (catsuits/
  short-sleeve fashion show arms/skin), where body markings must match the head species.
  Note hair is *also* a leveled-list item — for animal heads, swap/empty `LL_Crowd_Hairs_*`
  or repurpose it as mane/head-fur.
- Crowds are a distinct race from a cloned player race → full coverage means handling
  both (plus `ChildRace` for kids).

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

Key insight: a `MRPH` separates the **face-animation morphs** (expressions,
visemes) from the **chargen morphs** (creator sliders), and can additionally
map morph sliders onto **bone transforms** via the Bone Morph Definition File —
so a slider can move bones, not just vertices.

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
    `as_yo1`, `eu_md2`, `eu_ol1`, `eu_yo1`. (Note the trailing index is a fixed
    token, not a free axis — `eu` uses `md2` where `af`/`as` use `md1`.)
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
>   name**, or the face is frozen in dialogue and won't lip-sync — a substantial
>   per-head rigging cost, and a big reason shipped beast races have static faces.
> - **Animated ears/appendages via expression** (e.g. "sad → droopy ears") work the
>   same way, keyed to *action units* rather than named emotions: give the ears
>   their own `performance/morph.dat` (an ear head part, like `eyebrow_01`) and
>   author ear-pose deltas onto the AUs that compose each mood — droop on
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
`…Afraid` ↔ `…Afraid`, `…Shocked`, `…Depressed`, `…Disgust`, `…Smirk`, …) and were even
authored in the **same FormID block** (`FXPD facialExpression_Afraid [0020D3A0]`,
`KYWD AnimFaceArchetypeAngry [0020D3A2]`). So the trigger path is **dialogue/scene →
`AnimFaceArchetype` keyword → (in-house animation/behavior layer) → the matching `FXPD`
morph bundle** — the keyword↔`FXPD` binding is by **name/convention in the anim system,
not an editable plugin reference**. (`INFO` responses additionally carry a per-line
*Emotion* keyword + value in `TRDA`.)

> **Unconfirmed:** that editing an `FXPD` actually changes the in-game performance — the
> anim/behavior layer could source an archetype's morphs from the `.agx` graph rather than
> the `FXPD` record, in which case `FXPD` is data the runtime doesn't read. A one-off test
> (add an obvious morph to `facialExpression_Angry`, trigger an angry line) would settle
> both this and the ignore-unknown-AU assumption below.

> **Furry-race implications.**
> - Because an `FXPD` references morphs **by name**, and every face part only responds
>   to the AU keys *its own* `performance/morph.dat` defines, a muzzle head that authors
>   the vanilla AU names (`browLowererL`, `jawOpen`, `innerBrowRaise`, …) is driven by the
>   **vanilla dialogue expressions automatically** — no behavior-graph authoring, no
>   record edits. This is the cheapest path to dialogue-driven emotion on a non-human head.
> - **`FXPD` records are global, not per-race.** There is no race field and dialogue picks
>   the expression, not the actor's race — so you *cannot* give an anthro wolf a different
>   `_Angry` mix from a human by adding a race-specific expression alone.
> - **Work-around (unconfirmed, promising):** add **new, species-specific action units**
>   (e.g. `canine_ear_angry`, `canine_ear_happy`) to the canine head/ear `performance/
>   morph.dat`, then add those AU names to the relevant **global** `FXPD` records at chosen
>   weights. Humans lack those keys in their morph.dat, so the added entries are **silently
>   ignored on humans** (unknown key = no-op) but deform the canine's ears — one shared
>   expression, species-appropriate result, no custom dialogue needed. Costs: it's an edit
>   to base-game global records (a compatibility/"dirty edit" consideration), and the
>   ignore-unknown-AU behavior should be confirmed in-game. A few reusable ear AUs
>   (`earPinBack`/`earDroop`/`earPerk`) spread across the emotion `FXPD`s is tidier than a
>   bespoke morph per emotion. Authoring *brand-new* `FXPD`s instead avoids editing vanilla
>   records but then needs custom dialogue/scenes to trigger them.

### The morph-delta file (`.morph` / `morph.dat`)
Stored under `Data/meshes/morphs/…/morph.dat` — always named `morph.dat`, only the folder path varies
(e.g. `meshes/morphs/human/female/chargen/body/morph.dat`); **not** hash-named like `.mesh` files.
Binary layout **verified** against Outfit Studio's `SFMorphFile` (little-endian):

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

So a morph is **dense over vertices** (one `offsets` entry each, `numOffsets == numVertices`) but
**sparse over keys**: a vertex stores a run of deltas only for the shape keys whose bit is set in its
`keyMarker`, and the set bits (ascending) map 1:1 to that vertex's consecutive `morphData` records.
Position deltas share the `.mesh`'s `havokScale` factor.

> **Corrections (verified byte-exact against vanilla + the SGB `MorphIO.cpp` source, 2026-07-14):**
> the normal/tangent are **DEC3N signed** (earlier notes said UDEC3), and the position half-float is
> stored **metric** and multiplied — not divided — by `havokScale` to reach game units. A round-trip
> reader/writer reproduces a vanilla `morph.dat` byte-for-byte with this layout.

**`targetVertColor` is an RGB565 per-vertex colour**, **constant per vertex across all of that vertex's
morph keys** (verified: for `chargen/coily_mohawk_f`, 0 of 10,011 multi-key vertices differ across
keys; same for the head). SF vertex colour drives **material masks** (hair/clothing use R/G/B channels —
`HairSettingsComponent.AOVertexColorChannel` / `DepthOffsetMaskVertexColorChannel`;
`AlphaBlenderSettings.VertexColorChannel`; chromatic values like magenta `(1,0,1)`; faces use a
near-gray baked AO `0xBDF7`). It's a constant on most morphs — of 1194 vanilla `morph.dat`, only 49
carry a non-constant colour. It **correlates with the mesh's own vertex colour** but is not byte-equal
(on the hair sample R/B match, G differs); the exact relationship is **unresolved**.

Because it's one value per vertex (not per morph), it maps to a Blender **colour attribute**: import
writes the per-vertex colours there, export RGB565-encodes them back (gray default if absent) — so a
morph round-trips from mesh + shape keys + one colour attribute, no per-morph colour authoring. (Whether
the engine reads these colours at all is unconfirmed; the in-game round-trip settles it, and for faces
the gray default reproduces the real value, so only hair/fur is at risk.)

> **Note — the base `.mesh` DOES carry vertex colours** (the hair sample has 1002 distinct raw colours;
> ~22% of sampled SF `.mesh` use non-black colour/alpha). A current NIF ctypes/wrapper layer read them
> as all-black — a vertex-colour **import bug** to fix, since it silently breaks material rendering
> (alpha especially) on every mesh that uses vertex colour, independent of morphs.

Workflow facts (Starfield Geometry Bridge, Blender):
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

---

## 4. Tints, complexions & overlays — the AVM system (`AVMD`/`AVMS`)

For a furry race, **fur color, stripes, spots, and markings live here**, not in
the mesh. Starfield replaced the fixed `[Skyrim]` tint-mask layers with a
generalized **Additive Visual Material (AVM)** system.

### Per-NPC tint application (`NPC_` → "AVMD Tints")
**Tints are applied on the `NPC_` record, not the `RACE` record** — the race has
no tint-layer list. Each NPC carries an `EDCT` **Tint Count** plus an **AVMD
Tints** array; each entry is one applied layer:
| Field | Meaning |
|---|---|
| `MNAM` | → the `AVMD` record this layer comes from |
| `TNAM` Tint Group | which group (e.g. skin, cheeks, "muzzle") |
| `QNAM` Tint Name | which option in the group |
| `VNAM` Tint Texture | the overlay texture path |
| `NNAM` Tint Color | RGBA color |
| `INTV` Intensity | 1–128 |

So the chain that hooks a material's tint overlay to a specific character is
**`NPC_` "AVMD Tints" → `MNAM` (`AVMD` group/option) → `VNAM` texture / `NNAM`
color**, composited over the face material at runtime (for the player, driven by
the creator; for NPCs, authored on the record and baked by FaceGen — §6). The NPC
also names its per-slot colors directly as strings (`HCOL` hair, `FHCL` facial
hair, `BCOL` eyebrow, `ECOL` eye, `JCOL` jewelry).

`AVMD` ("AVMS Data") records define the tint/complexion **groups and options**
themselves, referenced by the race's `Skin Tone AVMS Subtype` and the head part's
`Color Mapping`. This is a **layered, arbitrarily-stackable** compositing system,
which is why the community can add new "paint" layers (the pattern used by the
Felid race — stripe patterns are added as tint groups that *replace* the
lipstick option in the creator).

**Three AVM group kinds** (from the CharGen Resources tutorial, article 481):

| Kind | Entry = | Used for |
|---|---|---|
| **Simple Group** (type 1) | `name : texturePath` | a texture option (skin tone, eye/teeth/hair texture, a face overlay) |
| **Complex Group** (type 2) | `name : SimpleGroupName` | exposes a simple group for a head part's **color mapping** (e.g. hair/eyebrow color) |
| **Modulation Group** (type 3) | `name : R:G:B:A` | a solid **color** option (e.g. jewelry/lipstick color) |

Face overlays (complexion, dermaesthetic, scars, tattoos, lipstick, eyeshadow,
cheeks, accents…) are Simple Groups whose textures live under
`textures/actors/human/faces/chargen/postblenddetails/<category>/` and apply **only
to the "Face" head part**. **For a furry race, fur markings/stripes are authored
here** — as a Face-overlay Simple Group (this is exactly how Felid does stripes via
the lipstick-accent slot).

Concrete vanilla AVMD groups a race mod extends (FormIDs from article 431):
`ComplexGroup_HairColor [AVMD:000ECD2E]`, `ComplexGroup_FacialHairColor [000ECD30]`,
`ComplexGroup_EyebrowColor [000ECD2D]`, `SimpleGroup_EyebrowOpacity [0000EF9F]`
(required, else eyebrows render transparent), `SimpleGroup_EyeColor [000377DC]`,
`SimpleGroup_TeethCustomization [0006160A]`. Skin tones use a **0-based index** (the
option *name* doesn't matter); the race's `Chargen and Skintones` body/hands skin-tone
must match the AVM group's `YNAM`. New chargen options can be added either directly in
xEdit or via the config-driven **RTFP** patcher (`[AVMData]`/`[FormList]` `add_entr`
directives, `minver=115`) — the approach the CharGen Resources resource ships.

Body shape is also stored per-NPC as **`MRSV` Body Morph Region Values**:
five floats — **Head / Upper Torso / Arms / Lower Torso / Legs** — the runtime
expression of the body triangle.

---

## 5. The body & head mesh — `.mesh` files and `BSGeometry`

**The biggest structural change from `[FO4]`/`[Skyrim]`: geometry is no longer
stored inside the `.nif`.**

- The NIF holds a **`BSGeometry`** block (replacing `BSTriShape` /
  `BSDynamicTriShape`). `BSGeometry` references one or more external
  **`.mesh`** files, one per LOD.
- `.mesh` files live at `Data/geometries/<hex1>/<hex2>.mesh`. Vanilla names are
  40 hex chars (split 20/20) that *look* like a digest, but the name is **not a
  computed/enforced hash** (nifly/OS write arbitrary names; the game doesn't
  verify), so human-readable replacement names work. See
  [meshes.md](meshes.md) for the full `.mesh` byte layout.
- Inside a `.mesh` (`BSGeometryMeshData` in nifly): 32-bit vertex count
  (practical cap **65535** verts per the tooling), triangles, **UDEC3-packed**
  normals & tangents, vertex colors, UV1/UV2, per-vertex **skin weights**
  (`nWeightsPerVert`), **LODs**, **meshlets** (vertOffset/primOffset — the
  mesh-shader clustering), and **cull data**. Positions are **normalized to
  metric units** (nifly applies a `havokScale ≈ 69.969` to match old-game sizes).
- **Skinning/bone data stays in the NIF**, not the `.mesh` (verified against a
  real body NIF): the bone-name list is in a **`SkinAttach`** block (string names
  — 38 for the vanilla body); per-bone bind transforms/bounding spheres are in
  **`BSSkin::BoneData`**, with **`BSSkin::Instance`** as the skin instance. The
  `.mesh` carries only per-vertex `{boneIndex, weight}` pairs indexing that name
  list. Note the vanilla body uses **6 weights per vertex** (Starfield lifts the
  old 4-bone cap).

**Practical gotcha:** the community reports "internal geometry" (embedding mesh
data in the NIF rather than an external `.mesh`) **causes issues with head
parts** — head parts should reference external `.mesh` files.

### Body layout
The body is delivered by the race's `WNAM` Skin `ARMO` and its armor addons, cut
into biped slots (§7). Community body replacers (e.g. the SFF female body) show
the division as separate meshes for **body, hands, feet, first-person body/hands,
head**, each skinned to the shared skeleton, each with its own `.mesh`, morphs,
UVs, and skin-tone textures (`sk6/sk7/sk8` texture variants seen in the wild).
Head and body are **separate meshes joined at the neck** — the neck seam and
matching skin-tone/tint at the seam is a classic failure point.

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

### Digitigrade legs
Digitigrade legs are the **hard** case: they change the leg bone chain and its
proportions, which breaks every locomotion animation retargeted for plantigrade
legs. Options are (i) keep the human leg skeleton and fake digitigrade with mesh
weighting only (limited), or (ii) add real digitigrade bones and **retarget/redo
locomotion** — blocked by the behavior-graph tooling gap. **Unverified** that any
Starfield mod has shipped true digitigrade locomotion.

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
- **Unverified:** the exact Starfield facegen output subpaths and file naming —
  the community docs describe the workflow but I did not confirm the literal
  `facegendata/…` path for Starfield. Treat as "same idea as FO4, path TBD."

Implication for a furry race's NPCs: every NPC of the race must be baked in the
CK with the race's head parts, morphs, and fur tints — a bulk, error-prone step.
This is exactly the pain point that dedicated facegen tooling (writing the baked
`.nif`/`.dds` directly instead of Ctrl+F4-ing in the CK) aims to eliminate.

---

## 9. What the community has actually achieved

- **Felid Race** (Starfield Nexus 17160): playable cat-people (tiger/jaguar/
  leopard/cougar). Implemented by **customizing the human race** — new head-part
  meshes + tint groups (stripe patterns occupy the "lipstick" tint slot),
  vanilla-clothing compatible. Not a from-scratch race. Its tail is driven by
  **Havok cloth physics** (not BMOD/animation) and is reported as "wonky" — the
  reference point for the appendage-motion question in §6.
- **CP's Menagerie** (7783): WIP "add fur" project; first release a wolf-like
  mammal.
- **SesamePaste "wolf race"** (author of StarfieldMeshConverter): early, buggy,
  requires manual fixup — a proof of concept.
- **SFF Body Replacer**: full female body replacer showing the body-mesh +
  morph + extended-skeleton pipeline; depends on **SF Extended Skeleton** and
  **CharGenMenu**.
- **CharGenMenu**: in-game framework (SFSE) to expose custom sliders/morphs.
- **StarUI-style / body-slider mods**: extend the creator's body sliders.

**Consensus takeaway:** a *truly new* playable race (own RACE record, own
skeleton, own behavior graph) is **not a solved problem**. Every shipped
"anthro/beast" result is a **skinned reworking of `HumanRace`** — new head parts
(using the Creature-* types), new tint groups, new body/head `.mesh` + `.morph`,
BMOD-driven appendages, reusing the human skeleton and behavior graph.

---

## 10. Practical path — building a custom anthro race

A realistic ordering, easiest→hardest, with blockers flagged:

1. **Start by cloning `HumanRace`** (or overriding it), not authoring a new
   skeleton/behavior graph. You inherit locomotion, facegen wiring, and biped
   slots for free.
2. **Body & head meshes.** Model the anthro body/head in Blender; export each
   part to `.mesh` via Starfield Geometry Bridge. Keep ≤65535 verts, UV-unwrapped,
   manifold. Skin to the (human or extended) skeleton — bone list stored in the
   NIF's SkinAttach.
3. **Morphs.** Author a `Basis` + chargen shape keys (0–1) per mesh; export
   `.morph`. Create `MRPH` records; point head parts' `MNAM` at them. Add
   expression/viseme morphs too (or the face is static).
4. **Head parts.** Create `HDPT` records using **Creature Head / Creature Tail /
   Creature Wings** etc. Set `RNAM Valid Races` to your race's `FLST` so parts
   appear only for your race. Wire default parts into `RACE → Head Parts`.
5. **Fur / markings.** Build `AVMD` tint groups (stripes, spots, muzzle mask,
   belly) and skin-tone AVMS subtypes; reference them from `RACE → Chargen and
   Skintones` and head parts' `Color Mapping`. Layers stack, so fur patterns are
   additive overlays — no hard limit like the old 4-layer tint system.
6. **Creator sliders.** Expose custom sliders via **CharGenMenu** + JSON whose
   keys match your `.morph` keys. Define **Face Dials** and **Face Morph
   Phenotypes** in the RACE record for presets.
7. **Tail / ears (animated).** Add bones to `skeleton.nif`; skin the tail/ear
   `.mesh` to them; add **`BMOD` SpringBone / LookAtChain** modifiers to
   `RACE → Bone Modifiers`. No behavior-graph work needed for physics-swing.
8. **FaceGen bake.** Bake every NPC of the race in the CK; verify neck-seam
   skin-tone match and no floating eyes/teeth. Consider a direct facegen writer
   to avoid mass Ctrl+F4.

### Finishing fixes & gotchas (verified, article 431)

Concrete FormIDs/steps that trip up first-time race authors:

- **Verify a headpart:** make an NPC of the race, add it to `CharGenPresets [FLST:0003F551]`, then in-game `slm 14` and pick the last preset.
- **Chargen visibility:** append head parts to `HeadPartsChargenOptionsMale [FLST:0003D9AF]` / `Female [FLST:0003D9B0]` (entry = HDPT FormID minus its first three load-order digits). Eye Color needs **both** a left- and right-eye head part.
- **Spacesuit not showing:** add your race to `HumanRaceORChildRaceORHumanCorpseRace [CNDF:0003D8C1]`.
- **Dialogue camera too close:** add your race to `DC_Race_Human [CPTH:000C1056]`.
- **Invisible limbs in new-game chargen:** give `Clothes_GenWare_01 "Space Undersuit" [ARMO:00165722]` a skin ARMA / remodel it to your naked-skin model.
- **Become the race:** set the **Player** record (`NPC_` FormID **7**) to your race; there are **12** player copies to change.
- **Toggle-able:** split the player overrides into a separate `.esm` so disabling it keeps the race available for NPC mods but reverts the player.
- Quirks: **females have no facial hair** (the `beard` slot / `fhclr` don't work on female); the **first** eyebrow in a list ignores its assigned texture (engine bug).

### Hard blockers (honest assessment)
- **Behavior graph.** No public Starfield behavior-graph editor → no new
  locomotion → **digitigrade legs and novel gaits are effectively blocked**;
  reuse human legs.
- **Format maturity.** `.mesh`/`.morph` are reverse-engineered, not documented
  by Bethesda; tooling (SGB/StarfieldMeshConverter/nifly) is the source of truth
  and can lag engine updates.
- **FaceGen scale.** Baking many NPCs is slow and fragile (dark-face bug).
- **Creator UI.** Radically non-human morphology stresses a UI/morph system
  designed around a human face; sliders assume human topology.
- **True new RACE.** Own skeleton + behavior graph + genome integration is
  unproven; the safe route is a `HumanRace` variant.

---

## What a custom anthro race requires — checklist

- [ ] **RACE record** — clone of `HumanRace`; set `Skeleton Data` (ANAM/NAM5/
      NAM6/DNAM), `WNAM` Skin ARMO, `GNAM` Body Part Data, FaceGen clamps.
- [ ] **skeleton.nif** — human skeleton (or SF Extended Skeleton) **+ tail/ear
      bones** if animated appendages.
- [ ] **Body/head/hands/feet `.mesh` files** — anthro geometry, skinned; NIFs
      with `BSGeometry` + `SkinAttach`; both normal and **SS (spacesuit)** slots
      considered.
- [ ] **`.morph` files + `MRPH` records** — chargen morphs (creator sliders),
      expression/viseme morphs, optional bone-morph definition.
- [ ] **`HDPT` records** using **Creature Head / Tail / Wings / Arms / Legs**
      types — muzzle/snout, ears, tail; `RNAM Valid Races` = your race FLST;
      `MNAM` → MRPH.
- [ ] **`AVMD`/AVMS tint groups** — fur color, stripes/spots/markings, muzzle
      mask; skin-tone subtypes; referenced by RACE Chargen and head-part Color
      Mapping.
- [ ] **`BMOD` Bone Modifiers** — SpringBone (tail/ear jiggle), LookAtChain
      (ear tracking); attached to `RACE → Bone Modifiers`.
- [ ] **Chargen wiring** — Face Dials + Face Morph Phenotypes in RACE; custom
      sliders exposed via **CharGenMenu** + JSON config.
- [ ] **Body Part Data (`BPTD`)** — dismemberment regions if changing anatomy.
- [ ] **Skin/texture sets (`TXST`)** — fur diffuse/normal/specular; face custom
      textures base path.
- [ ] **FaceGen bake** for every NPC of the race (CK), or a direct facegen
      writer.
- [ ] **Dependencies for players** — SFSE, CharGenMenu, likely SF Extended
      Skeleton.

---

## Open questions / uncertainties

1. ~~Exact `morph.dat` binary layout~~ — **RESOLVED** (verified byte-exact against
   vanilla + Outfit Studio `SFMorphFile` / StarfieldMeshConverter `MorphIO.cpp`;
   corrected the color/normal encodings, see §3).
7. ~~How a material's tint layers hook to a specific character~~ — **RESOLVED**:
   they don't sit on the `RACE`; each `NPC_` lists its own **AVMD Tints**
   (`MNAM` → `AVMD` group/option → texture/color), see §4.
2. ~~Vanilla skeleton bone list~~ — **RESOLVED** (116 NiNodes extracted from
   `skeleton.nif`, see §6).
3. **Starfield facegen output paths** — workflow confirmed, literal
   `facegendata/…` path not verified for Starfield.
4. **BMOD limits** — how many SpringBone chains the engine handles gracefully,
   and whether ear LookAtChain works on first-person, is untested here.
5. **Can a genuinely new RACE (non-`HumanRace`-parented) enter the creator?** No
   confirmed example; all anthro results are HumanRace variants.
6. **Digitigrade locomotion** — no confirmed shipped example; behavior-graph gap
   is the suspected blocker.

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

_Draft 2026-07-06 — not yet reviewed_
