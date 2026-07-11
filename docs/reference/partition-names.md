# Skyrim Body Partition Names (SBP_*)

`[Skyrim]` Skyrim skins a body/armor mesh into numbered **body partitions**
(`SBP_<n>_<name>`) carried by `BSDismemberSkinInstance`. The number is a **biped
object slot**; the game uses partitions to **hide regions covered by other worn
items** (e.g. tall boots cover the feet and calves, so a body's foot/calf
partitions are hidden when the boots are equipped). Skyrim does **not** do
runtime limb severing — for that, see Fallout 4 below.

The partition system itself (how `BSDismemberSkinInstance` and `NiSkinPartition`
work) is documented on the **[NIF Files](../file-formats/nif-files.md)** page;
this page is just the complete slot list.

## Base partitions (30–39)

| # | Name | Region |
|---|---|---|
| 30 | `SBP_30_HEAD` | Head |
| 31 | `SBP_31_HAIR` | Hair |
| 32 | `SBP_32_BODY` | Torso / main body |
| 33 | `SBP_33_HANDS` | Hands |
| 34 | `SBP_34_FOREARMS` | Forearms |
| 35 | `SBP_35_AMULET` | Amulet / necklace |
| 36 | `SBP_36_RING` | Ring |
| 37 | `SBP_37_FEET` | Feet / boots |
| 38 | `SBP_38_CALVES` | Calves / lower legs |
| 39 | `SBP_39_SHIELD` | Shield |

## Extended / dual-purpose slots (40–61)

Slots 44–47 are **dual-purpose**: on dragons they carry blood/gore body parts; on
humanoids the community uses them (and 48–61) as mod partitions. The dragon
meaning and the common mod meaning are both listed.

| # | Name | Region |
|---|---|---|
| 40 | `SBP_40_TAIL` | Tail (custom races) |
| 41 | `SBP_41_LONGHAIR` | Long hair |
| 42 | `SBP_42_CIRCLET` | Circlet |
| 43 | `SBP_43_EARS` | Ears |
| 44 | `SBP_44_DRAGON_BLOODHEAD_OR_MOD_MOUTH` | Dragon blood-head / mod: mouth |
| 45 | `SBP_45_DRAGON_BLOODWINGL_OR_MOD_NECK` | Dragon blood-wing (L) / mod: neck |
| 46 | `SBP_46_DRAGON_BLOODWINGR_OR_MOD_CHEST_PRIMARY` | Dragon blood-wing (R) / mod: chest (primary) |
| 47 | `SBP_47_DRAGON_BLOODTAIL_OR_MOD_BACK` | Dragon blood-tail / mod: back |
| 48 | `SBP_48_MOD_MISC1` | Mod: misc 1 |
| 49 | `SBP_49_MOD_PELVIS_PRIMARY` | Mod: pelvis (primary) |
| 50 | `SBP_50_DECAPITATEDHEAD` | Decapitated head |
| 51 | `SBP_51_DECAPITATE` | Decapitate |
| 52 | `SBP_52_MOD_PELVIS_SECONDARY` | Mod: pelvis (secondary) |
| 53 | `SBP_53_MOD_LEG_RIGHT` | Mod: right leg |
| 54 | `SBP_54_MOD_LEG_LEFT` | Mod: left leg |
| 55 | `SBP_55_MOD_FACE_JEWELRY` | Mod: face jewelry |
| 56 | `SBP_56_MOD_CHEST_SECONDARY` | Mod: chest (secondary) |
| 57 | `SBP_57_MOD_SHOULDER` | Mod: shoulder |
| 58 | `SBP_58_MOD_ARM_LEFT` | Mod: left arm |
| 59 | `SBP_59_MOD_ARM_RIGHT` | Mod: right arm |
| 60 | `SBP_60_MOD_MISC2` | Mod: misc 2 |
| 61 | `SBP_61_FX01` | FX slot 1 |

## Skinned / secondary variants (130s, 140s, 150, 230)

| # | Name | Region |
|---|---|---|
| 130 | `SBP_130_HEAD` | Head (skinned variant) |
| 131 | `SBP_131_HAIR` | Hair (skinned variant) |
| 141 | `SBP_141_LONGHAIR` | Long hair (skinned variant) |
| 142 | `SBP_142_CIRCLET` | Circlet (skinned variant) |
| 143 | `SBP_143_EARS` | Ears (skinned variant) |
| 150 | `SBP_150_DECAPITATEDHEAD` | Decapitated head (skinned variant) |
| 230 | `SBP_230_NECK` | Neck |

## Custom partitions

Any other partition number can be referenced as **`SBP_<n>_UNKNOWN`**, where `<n>`
is the number. Custom races and body mods commonly use the 40s–60s mod slots for
extra pieces (tails, ears, additional armor layers).

## Fallout 4

`[FO4]` Fallout 4 does **not** use the `SBP_*` partition system. It replaces it
with **segments / subsegments** (for real runtime dismemberment) plus an external
**`.ssf`** segment file. See **[Dismemberment](../game-specific/fallout4/dismemberment.md)**
for the full scheme, including cut offsets and the biped-object (Pip-Boy) segments.

## Source

- BadDogSkyrim/PyNifly wiki — [Skyrim Partitions](https://github.com/BadDogSkyrim/PyNifly/wiki/Skyrim-Partitions)

_Draft 2026-07-10 — not yet reviewed_
