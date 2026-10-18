# Starfield Crowds

City crowds are ordinary NPC records on a lightweight race, spawned by region records and
dressed by their outfits. The head comes from the outfit too: one baked mesh per head, with
the eyes and both arms merged in. This page covers how the pieces fit, measured from
`Starfield.esm` and the unpacked vanilla assets, and what a crowd of a new species needs,
from building one (a fox crowd, tested in game October 2026).

The [chargen page](chargen.md#ambient-crowds-humancrowdrace-generated-on-the-fly) has the
overview; this page has the detail.

---

## 1. How crowds spawn

Crowds come from **19 `CrowdRegion_*` records** (signature `GBFM`, carrying a
`BGSCrowdComponent`). Each holds a density (`CDND`), a population count (`CDNS`), and one or
more **populations**, typically a day and a night one, each with:

- conditions (`CITC` + `CTDA`), which is how day/night is chosen;
- a name (`STRV`: `CrowdCompDayTime`, `CrowdCompNightTime`) and a scale (`FLTV`);
- a **proportions list** (`PRPS`): entries of {actor, weight, curve table}. Vanilla weights
  are 100 or 50.

**A proportions entry must be an `NPC_`**; xEdit's definition allows no leveled NPC list.
So the variety comes from the NPC's outfit, not from the spawn list.

The `CrowdActor_*` NPCs are also used by 28 dialogue conditions, 3 quests and a few cell
placements. Changing their race changes those too; adding new NPCs to the proportions
lists avoids that.

## 2. The crowd actors

Census of the 138 `CrowdActor_*` NPCs (excluding the `_TEMPLATE`, `_VOICE` and `_KEYWORDS`
helpers), 2026-10-16:

| Field | Value |
|---|---|
| Race (`RNAM`) | `HumanCrowdRace [002BBC09]`, all 138 |
| Skin (`WNAM`) | `Skin_Crowd_Base_Body_NOTPLAYABLE`, the race's own skin |
| Skin tone (`STON`) | present on all 138 |
| Head parts, face morphs, tint layers | none |
| Default outfit (`DOFT`) | `Outfit_Crowds_<district>_<sex>` |
| Template flags (`ACBS`, u16 at offset 14) | Factions + Keywords (`0x1004`) on 95; **Traits** + Factions + Keywords (`0x1005`) on 24; other combinations on 19 |

**Crowds have no skin tones.** `HumanCrowdRace` names no skin-tone groups at all (no
`BSTT`, `HSTT` or `FSTT`), and 176 of 181 crowd actors set `STON` to 0. Every visible bit of
skin is inside the one head mesh with its own baked texture, so head, neck and hands always
match. Anything else that has to match the head, like a tail, has to come in the same tone by
construction (§5).

**Traits carries race.** The 24 that inherit Traits take them from
`LCharCrowdVoices_Male` / `_Female`, whose 10 entries are all `HumanCrowdRace` NPCs. Copy
one of those actors, set a new race, and the template quietly sets it back. Turn the Traits
flag off (and zero `TPTA` entry 0) on a copy that needs its own race.

### The outfit

An outfit holds three leveled lists: clothes (biped slot 3), a head list (slot 2), and a
hair-or-hat list (slot 1). Across the 39 crowd outfits there are 15 pairings: 3 head lists
(`LL_Crowd_Heads`, `_Thin`, `_Overweight`) × 5 hair lists (`NoHats`, `Hats_ALL`,
`Hats_Akila`, `Hats_NA`, `Hats_Neon`). The 168 vanilla crowd armors use **only slots 1–3**.

Each head list holds **8 head armors**, `CrowdHead_<phenotype>_NOTPLAYABLE`, one per human
phenotype, shared by both sexes. Each armor's single addon names a male NIF (`MOD2`), a
female NIF (`MOD3`), and one shared performance morph per sex (`NAM4` / `NAM6` → an `MRPH`
under `Meshes\Morphs\Human_Crowd\<Sex>\Performance`).

## 3. The crowd head

A crowd head NIF is **one `BSGeometry`**: head, eyes, mouth and both arms from the biceps to
the fingertips, merged into one mesh. The crowd race's skin is itself clothing
(`AA_Clothes_Crowd_Sweater_01_NOTPLAYABLE`, no bare skin), so the hands come with the head.

- **Size:** 4,179 vertices (female), 4,302 (male). Every crowd head of a sex shares that
  topology, which is what lets one performance morph (11 keys: `jawOpen`, blinks, brows,
  lips) serve all of them.
- **Skin:** 52–55 bones: head, neck, both eyes, both arms.
- **Material:** one `Materials\Actors\Human\Crowd\*.mat` with baked colour, normal,
  rough, metal and AO textures. **Crowd heads have no skin tones**: a colour variation is a
  separate texture set.
- **LOD:** 4 slots over 3 `.mesh` files, `ABBC` ([meshes §1](meshes.md#1-the-geometry-less-nif-and-the-bsgeometry-block)).
- **Eye positions:** a root `BoneTranslations` block, `BoneTrn`, holding where this head's
  eyes are. Without it the eyes are drawn in the wrong place; see
  [meshes: `BoneTranslations`](meshes.md#bonetranslations-a-crowd-heads-eye-positions).
- **Body types:** every head has `_thin` and `_overweight` copies (no suffix = average),
  each with its own `_facebones` companion, so the arms fit that body type's sleeves.

### The `_facebones` companion is just a copy

Every crowd head has a `<name>_facebones.nif`. Unlike a chargen head's companion, it has
**no face bones**: the same bones, shape and material as the plain NIF, and the same
slot-0 `.mesh`, with only slot 0 listed. The crowd `skeleton_facebones.nif` likewise equals
`skeleton.nif` (only `DirectAt` differs). There is no face rig on a crowd actor.

**This matters (verified in game):** the game draws a crowd head from its companion. A
companion skinned to `faceBone_*` bones, the way a chargen head's is, renders an
**invisible head**, because the crowd skeleton has none of those bones. Write the companion
as a copy of the plain NIF.

## 4. The crowd skeleton

`HumanCrowdRace` uses its own skeleton NIF
(`Actors\human_crowd\CharacterAssets\skeleton.nif`, and `\Female\`) but the **vanilla human
`skeleton.rig`** and the same **`Human_Root.agx`** animation graph as `HumanRace`. There is
no crowd `.rig`.

Compared with the human skeleton:

- **90 nodes against 115**, all at the same positions, none reparented.
- **9 twist bones are rotated differently**: `C_Neck_Twist`, `L/R_Biceps_Twist`,
  `L/R_Wrist_Twist1/2`, `L/R_Thigh_Twist`, by 29–152°.
- No `BSConnectPoint::Parents` on the root, and no `C_BackPack` ragdoll body.

**Nothing is bound to those twist rotations.** Measured over all 144 vanilla crowd clothing
NIFs (both sexes, all three body types), 1,112 twist-bone binds: 0 match the crowd
skeleton, 1,076 match the human skeleton exactly, and 36 (the female Neon rainwear's arms)
sit 3.6° from human against 30–143° from crowd. The crowd heads bind to the human
orientations too. That's why crowd outfits look warped in the Creation
Kit until a pose is applied: the unposed crowd skeleton has the odd rotations, and a pose
overrides them.

So **bind new crowd meshes to the human skeleton's orientations**, as vanilla's are.

## 5. A crowd of another species

What was built and tested for a fox crowd (October 2026), and what's still open.

**Worked in game:**

- **A crowd race of its own** (copied from `HumanCrowdRace`) with **new NPCs** copied from
  crowd actors and set to it. Inherited Traits must be turned off (§2).
- **The head as a head armor in the NPC's outfit**, on a new head list. No vanilla armor or
  list is touched.
- **The `_facebones` companion as a plain copy** (§3).
- **`BoneTrn` copied from a vanilla head** when the custom head's eyes sit where that head's
  do. The eye bones must be at the eyeball centres, or the eyes wobble as they turn.
- **Colour variants as separate texture sets**, each with its own `.mat` copied from the
  head's material and its own copy of the NIF pointing at it. All variants share one
  `.mesh`, morph and `BoneTrn`. The NIF names its material twice: a header string and the
  shape's `MaterialID` (a CRC-32 of the path; see [materials](materials.md)). Both must
  change.
- **Variant materials need their own object ids.** Each copy keeps the `res:` namespace
  (words 2–3) and gets new first words for the objects it defines, which is how vanilla's crowd
  materials differ from each other. References into imported templates keep theirs.
  Variants made that way render distinct textures in game.
- **A full skeleton on the crowd race.** The race's `ANAM`s pointed at copies of Extended
  Skeleton's human skeletons (which add a tail chain), under the race's own path. Vanilla crowd
  clothes render correctly on it, as §4's bind census predicts.
- **No `WNAM` on the NPCs.** An NPC's own skin overrides its race's, and the vanilla crowd actors
  carry one (the human crowd skin). Copies that keep it never wear the new race's skin; drop
  the field and give an NPC a skin only when it should differ from its race.
- **A tail renders on the crowd foxes.** It came from the race's skin: the player race's tail
  addon (body slot 15, with its `BSClothExtraData`) with the crowd race added to its races.

**Not yet tested:**

- **A tail in each head's tone.** Since crowds have no skin tones (§2), a tail on the race skin
  is one colour on every actor. Built: one tail addon per tone, each with its own material,
  carried by the head armor as a second addon (the armor's `BO64` gains slot 15), so the
  leveled list's pick brings the matching tail. The first try came out red because the copies
  kept the source addon's **Is Skin** flag ([chargen](chargen.md)); the flag is cleared now and
  awaits a look in game.
- Whether crowd actors simulate the tail's cloth at the same distances as full NPCs.
- The alternative of adding species addons to the vanilla head and hair armors, relying on
  armor race to pick the addon.

---

## Sources

- `Starfield.esm` record censuses with esplib (crowd actors, templates, outfits, regions,
  armor slots), 2026-10-10 to 2026-10-16.
- Unpacked vanilla meshes (`meshes\actors\human_crowd`, `meshes\clothes\*crowd*`) read with
  PyNifly: skin binds, skeleton transforms, `BoneTranslations`.
- In-game tests of a custom fox crowd head and NPC, 2026-10-16.
- xEdit `wbDefinitionsSF1.pas` for `BGSCrowdComponent` and `TPTA`.

_Draft 2026-10-16 — not yet reviewed_
